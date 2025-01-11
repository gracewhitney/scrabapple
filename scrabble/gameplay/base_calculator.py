import json
import string
from collections import Counter

from django.contrib.admin.utils import flatten
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from scrabble.constants import TurnAction, BLANK_CHARS
from scrabble.dictionaries import validate_word
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
        # Keep track of valid blank replacements for current play
        self.blank_replacements = {
            char: [letter for letter in string.ascii_lowercase] for char in BLANK_CHARS
        }

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
            # Check that starting tile is included
            self.validate_first_play(played_tiles)
            # First play must be at least 2 letters
            if len(played_tiles) < 2:
                raise ValidationError("First play must use at least 2 tiles")
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
            if self.game.racks.filter(forfeited=False).count() == 2:
                self.game.over = True
            # TODO fix turn order if player forfeits in multiplayer game, or always end game?
            game_player.forfeited = True
        elif turn_action == TurnAction.play:
            played_tiles = turn_data["played_tiles"]
            points, words = self.calculate_points(played_tiles)
            invalid_words = self.validate_words(words)
            if self.game.validate_words and invalid_words:
                raise ValidationError(f"Invalid words: {', '.join(invalid_words)}")
            # Deal with replacing blank tiles based on validation
            for tile in played_tiles:
                if tile['tile'] in BLANK_CHARS:
                    if self.blank_replacements[tile['tile']]:
                        tile['tile'] += self.blank_replacements[tile['tile']][0].upper()
            words = [self._replace_blank_tiles(word) for word in words]
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
        self.game.update_turn_index()
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
        if self.game_over(game_player):
            self.go_out(game_player)
        return turn

    def _replace_blank_tiles(self, word):
        for char in BLANK_CHARS:
            if self.blank_replacements[char]:
                word = word.replace(char, self.blank_replacements[char][0].upper())
        return word

    def calculate_points(self, played_tiles):
        # Calculates points and validates words, returning (points, valid_words, invalid_words) tuple
        board = GameBoard(self.game.board)
        points = 0
        words = []
        # Transpose vertical plays
        if len(set(tile['y'] for tile in played_tiles)) != 1:
            played_tiles = [{**tile, "x": tile["y"], "y": tile["x"]} for tile in played_tiles]
            board.transpose_board()
        def _handle_word(tiles):
            word_points, word = self.calculate_word_points(tiles, board)
            if word:
                words.append(word)
            return word_points
        # Get play direction word & points
        points += _handle_word(played_tiles)
        # Get perpendicular words & points
        board.transpose_board()
        for tile in played_tiles:
           points += _handle_word([{**tile, "x": tile["y"], "y": tile["x"]}])
        # Add bingo points
        if len(played_tiles) == 7:
            points += self.bingo_points
        return points, words

    def calculate_word_points(self, played_tiles, board):
        raise NotImplementedError()

    def validate_words(self, words):
        dictionaries = self.game.get_dictionaries()
        if not dictionaries:
            return []
        invalid_words = [
            word for word in words
            if not validate_word(word, dictionaries, self.blank_replacements)
        ]
        return invalid_words

    def game_over(self, game_player):
        return len(game_player.rack) == 0

    def go_out(self, game_player):
        first_turn_count = self.game.racks.aggregate(current_count=Max("turns__turn_count"))['current_count'] or 0
        turn_count = first_turn_count + 1
        with transaction.atomic():
            extra_points = 0
            for opponent in game_player.game.racks.exclude(id=game_player.id):
                lost_points = 0
                for tile in opponent.rack:
                    tile_score = self.get_unplayed_tile_points(tile)
                    if self.winner_takes_unplayed_points:
                        extra_points += tile_score
                    lost_points += tile_score
                if lost_points:
                    GameTurn.objects.create(game_player=opponent, turn_action=TurnAction.end_game,
                                            turn_count=turn_count, score=-lost_points, rack_before_turn=opponent.rack)
                    opponent.score -= lost_points
                    opponent.save()
                turn_count += 1
            # Also deduct tile points from this player (only affects old-style upwords)
            for tile in game_player.rack:
                extra_points -= self.get_unplayed_tile_points(tile)
            GameTurn.objects.create(game_player=game_player, turn_action=TurnAction.end_game,
                                    turn_count=first_turn_count, score=extra_points, rack_before_turn=game_player.rack)
            game_player.score += extra_points
            game_player.save()
            game_player.game.over = True
            game_player.game.save()
            # Cache game winners
            for player in game_player.game.winners():
                player.update(winner=True)

    def get_unplayed_tile_points(self, tile):
        raise NotImplementedError()

    def undo_last_turn(self, game_player):
        if self.game.over:
            raise ValidationError("Game over")
        turn = self.game.all_turns().last()
        if turn.game_player != game_player:
            raise ValidationError("Player doesn't match")
        with transaction.atomic():
            used_tiles = []
            if turn.turn_action == TurnAction.play:
                played_tiles = turn.turn_data["played_tiles"]
                board = GameBoard(self.game.board)
                for play in played_tiles:
                    tile = board.get_tile(play['x'], play['y'])
                    # Either we don't have blanks or we have single stacks :)
                    previous = "" if tile[0] in BLANK_CHARS else tile[1:]
                    board.set_tile(previous, play['x'], play['y'], replace=True)
                    used_tiles.append(play['tile'][0])
            elif turn.turn_action == TurnAction.exchange:
                used_tiles = turn.turn_data["exchanged_tiles"]
            new_tile_counts = Counter(game_player.rack) - (Counter(turn.rack_before_turn) - Counter(used_tiles))
            for letter, count in new_tile_counts.items():
                self.game.letter_bag.extend([letter for _ in range(count)])
            game_player.rack = turn.rack_before_turn
            game_player.score -= turn.score
            game_player.save()
            self.game.update_turn_index(backwards=True)
            self.game.save()
            turn.update(deleted=True)


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

    def set_tile(self, tile, x, y, replace=False):
        existing = self.get_tile(x, y) if not replace else ""
        self.board[y][x] = tile + existing

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

