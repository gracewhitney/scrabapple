from django.contrib.admin.utils import flatten
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from scrabble.constants import TurnAction
from scrabble.models import GameTurn
from scrabble.serializers import GameTurnSerializer


class BaseGameCalculator:
    game_type = None
    bingo_points = 50
    board_size = None
    tile_frequencies = None
    winner_takes_unplayed_points = True

    def __init__(self, game):
        if not self.game_type:
            raise NotImplementedError("Must specify game type")
        if game.game_type != self.game_type:
            raise ValueError("Wrong game type calculator instantiated")
        if not self.board_size:
            raise NotImplementedError("Must specify board size")
        if not self.tile_frequencies:
            raise NotImplementedError("Must specify tile frequencies")
        self.game = game

    def get_initial_board(self):
        return [["" for _ in range(self.board_size)] for _ in range(self.board_size)]

    def get_initial_letter_bag(self):
        # Returns full letter bag, ordered
        return flatten([letter for (letter, count) in self.tile_frequencies.items() for _ in range(count)])

    def validate_turn(self, turn_data, game_player, check_player=True):
        # Check that turn is allowed
        if check_player and game_player.turn_index != self.game.next_turn_index:
            raise ValidationError("Wrong player.")
        # deserialize turn data
        serializer = GameTurnSerializer(data=turn_data)
        if not serializer.is_valid():
            raise ValidationError(f"Misformatted data: {serializer.errors}")
        turn_action = serializer.validated_data["action"]
        if turn_action in [TurnAction.pass_turn, TurnAction.forfeit]:
            return serializer.validated_data
        if turn_action == TurnAction.exchange:
            exchanged_tiles = serializer.validated_data.get("exchanged_tiles")
            if not exchanged_tiles:
                raise ValidationError("Must choose at least one tile to exchange")
            if any(tile not in game_player.rack for tile in exchanged_tiles):
                raise ValidationError("Invalid tile to exchange, not in rack")
            if len(exchanged_tiles) > len(self.game.letter_bag):
                raise ValidationError("Not enough letters in bag")
            return serializer.validated_data
        if turn_action == TurnAction.play:
            played_tiles = serializer.validated_data["played_tiles"]
            board = GameBoard(self.game.board)
            self.validate_play(played_tiles, board, game_player)
            return serializer.validated_data
        else:
            raise NotImplementedError(f"Turn validation not implemented for {turn_action}")

    def validate_play(self, played_tiles, board, game_player):
        # Play must only include tiles which are in the user's rack
        if any(tile['tile'][0] not in game_player.rack for tile in played_tiles):
            raise ValidationError("Invalid tile, not in rack")
        if board.is_first_play():
            self.validate_first_play(played_tiles)
        else:
            # Subsequent plays must be adjacent to existing word
            if not any(board.has_adjacent_tile(tile['x'], tile['y']) for tile in played_tiles):
                raise ValidationError("Disconnected play")
        # Play must not repeat a square
        if len(set([(tile['x'], tile['y']) for tile in played_tiles])) != len(played_tiles):
            raise ValidationError("Play includes a square twice")
        # Play must be in a single row or column
        if len(set(tile['x'] for tile in played_tiles)) > 1 and len(set(tile['y'] for tile in played_tiles)) > 1:
            raise ValidationError("Play not in line")
        # Play must not have gaps
        if len(set(tile['y'] for tile in played_tiles)) != 1:
            played_tiles = [{**tile, "x": tile["y"], "y": tile["x"]} for tile in played_tiles]
            board.transpose_board()
        play_indices = set(tile['x'] for tile in played_tiles)
        row = played_tiles[0]['y']
        for x in range(min(play_indices), max(play_indices)):
            if x not in play_indices and board.get_tile(x, row) == "":
                raise ValidationError("Play not contiguous")
        return played_tiles

    def validate_first_play(self, played_tiles):
        raise NotImplementedError()

    def do_turn(self, turn_data, game_player):
        turn_action = turn_data["action"]
        points = 0
        starting_rack = list(game_player.rack)
        words = None
        if turn_action == TurnAction.pass_turn:
            pass
        elif turn_action == TurnAction.exchange:
            exchanged_tiles = turn_data["exchanged_tiles"]
            new_tiles = self.game.draw_tiles(len(exchanged_tiles))
            for tile in exchanged_tiles:
                rack_index = game_player.rack.index(tile)
                game_player.rack.pop(rack_index)
                self.game.letter_bag.append(tile)
            game_player.rack.extend(new_tiles)
        elif turn_action == TurnAction.forfeit:
            game_player.forfeited = True
            if self.game.racks.count() == 2:
                self.game.over = True
        elif turn_action == TurnAction.play:
            played_tiles = turn_data["played_tiles"]
            points, words = self.calculate_points(played_tiles)
            played_letters = [tile['tile'] for tile in played_tiles]
            new_tiles = self.game.draw_tiles(len(played_letters))
            for tile in played_letters:
                rack_index = game_player.rack.index(tile[0])
                game_player.rack.pop(rack_index)
            game_player.rack.extend(new_tiles)
            GameBoard(self.game.board).update_board(played_tiles)
        else:
            raise NotImplementedError(f"No turn action defined for {turn_action}")
        # save game and create turn object
        self.game.next_turn_index = (self.game.next_turn_index + 1) % self.game.racks.count()
        game_player.score += points
        self.game.save()
        game_player.save()
        turn_count = self.game.racks.aggregate(current_count=Max("turns__turn_count"))['current_count'] or 0
        turn = GameTurn.objects.create(
            game_player=game_player,
            turn_count=turn_count + 1,
            turn_action=turn_action,
            score=points,
            rack_before_turn=starting_rack,
            turn_words=words,
            turn_data=turn_data,
        )
        if len(game_player.rack) == 0:
            self.go_out(game_player)
        return turn

    def calculate_points(self, played_tiles):
        board = GameBoard(self.game.board)
        words = []
        # Transpose vertical plays
        if len(set(tile['y'] for tile in played_tiles)) != 1:
            played_tiles = [{**tile, "x": tile["y"], "y": tile["x"]} for tile in played_tiles]
            board.transpose_board()
        points, word = self.calculate_word_points(played_tiles, board)
        words.append(word)
        board.transpose_board()
        for tile in played_tiles:
            word_points, word = self.calculate_word_points([{**tile, "x": tile["y"], "y": tile["x"]}], board)
            points += word_points
            if word:
                words.append(word)
        if len(played_tiles) == 7:
            points += self.bingo_points
        return points, words

    def calculate_word_points(self, played_tiles, board):
        raise NotImplementedError()

    def go_out(self, game_player):
        with transaction.atomic():
            for opponent in game_player.game.racks.exclude(user_id=game_player.id):
                for tile in opponent.rack:
                    tile_score = self.get_unplayed_tile_points(tile)
                    if self.winner_takes_unplayed_points:
                        game_player.score += tile_score
                    opponent.score -= tile_score
                opponent.save()
            game_player.save()
            game_player.game.over = True
            game_player.game.save()

    def get_unplayed_tile_points(self, tile):
        raise NotImplementedError()


class GameBoard:
    def __init__(self, board):
        self.board = board
        self.board_height = len(self.board)
        self.board_width = len(self.board[0])

    def get_tile(self, x, y, most_recent=False):
        tile = self.board[y][x]
        if tile and most_recent:
            return tile[0]
        return tile

    def set_tile(self, tile, x, y):
        self.board[y][x] = tile + self.get_tile(x, y)

    def is_first_play(self):
        """Returns True if no plays have been made yet on this board"""
        return all(all(square == "" for square in row) for row in self.board)

    def is_free_square(self, x, y):
        """Returns True if the specified square has not yet been played"""
        return self.board[y][x] == ""

    def has_adjacent_tile(self, x, y):
        """Returns True if any adjacent square contains a tile"""
        adjacent_squares = []
        if x > 0:
            adjacent_squares.append((x - 1, y))
        if x < self.board_width - 1:
            adjacent_squares.append((x + 1, y))
        if y > 0:
            adjacent_squares.append((x, y - 1))
        if y < self.board_height - 1:
            adjacent_squares.append((x, y + 1))
        return any(not self.is_free_square(adj_x, adj_y) for (adj_x, adj_y) in adjacent_squares)

    def update_board(self, play):
        for played_tile in play:
            self.set_tile(played_tile['tile'], played_tile['x'], played_tile['y'])

    def transpose_board(self):
        self.board = [
            [self.board[y][x] for y in range(self.board_height)]
            for x in range(self.board_width)
        ]

