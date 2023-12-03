from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils.crypto import get_random_string

from common.models import User
from scrabble.constants import TurnAction, TILE_SCORES, BOARD_CONFIG, Multiplier
from scrabble.helpers import send_invitation_email
from scrabble.models import GameTurn, ScrabbleGame, GamePlayer
from scrabble.serializers import GameTurnSerializer


def create_new_game(form, user, request=None):
    game = ScrabbleGame.objects.create()
    GamePlayer.objects.create(user=user, game=game, turn_index=0, rack=game.draw_tiles(7, commit=True))
    turn_index = 1
    for email in [
        form.cleaned_data["player_2_email"],
        form.cleaned_data.get("player_3_email"),
        form.cleaned_data.get("player_4_email")
    ]:
        if not email:
            break
        user, created = User.objects.get_or_create(
            email=email, defaults={"one_time_passcode": get_random_string(32)}
        )
        GamePlayer.objects.create(user=user, game=game, turn_index=turn_index, rack=game.draw_tiles(7, commit=True))
        send_invitation_email(user, game.id, new_user=created, request=request)
        turn_index += 1
    return game


def validate_turn(turn_data, game, game_player):
    # Check that turn is allowed
    if game_player.turn_index != game.next_turn_index:
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
        if len(exchanged_tiles) > len(game.letter_bag):
            raise ValidationError("Not enough letters in bag")
        return serializer.validated_data
    if turn_action == TurnAction.play:
        played_tiles = serializer.validated_data["played_tiles"]
        # Play must only include tiles which are in the user's rack
        if any(tile['tile'][0] not in game_player.rack for tile in played_tiles):
            raise ValidationError("Invalid tile, not in rack")
        board = ScrabbleBoard(game.board)
        if board.is_first_play():
            # First play must include center tile
            if not any((tile['x'], tile['y']) == (7, 7) for tile in played_tiles):
                raise ValidationError("First play must include center tile")
        else:
            # Subsequent plays must be adjacent to existing word
            if not any(board.has_adjacent_tile(tile['x'], tile['y']) for tile in played_tiles):
                raise ValidationError("Disconnected play")
        # Play must not overlap an existing tile
        if any([not board.is_free_square(tile['x'], tile['y']) for tile in played_tiles]):
            raise ValidationError("Play includes non-empty square")
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
        return serializer.validated_data
    else:
        raise NotImplementedError(f"Turn validation not implemented for {turn_action}")


def do_turn(turn_data, game, game_player):
    """Saves and returns turn object and mutates associated data"""
    turn_action = turn_data["action"]
    points = 0
    starting_rack = list(game_player.rack)
    words = None
    if turn_action == TurnAction.pass_turn:
        pass
    elif turn_action == TurnAction.exchange:
        exchanged_tiles = turn_data["exchanged_tiles"]
        new_tiles = game.draw_tiles(len(exchanged_tiles))
        for tile in exchanged_tiles:
            rack_index = game_player.rack.index(tile)
            game_player.rack.pop(rack_index)
            game.letter_bag.append(tile)
        game_player.rack.extend(new_tiles)
    elif turn_action == TurnAction.forfeit:
        game_player.forfeited = True
        if game.racks.count() == 2:
            game.over = True
    elif turn_action == TurnAction.play:
        played_tiles = turn_data["played_tiles"]
        points, words = calculate_points(played_tiles, game)
        played_letters = [tile['tile'] for tile in played_tiles]
        new_tiles = game.draw_tiles(len(played_letters))
        for tile in played_letters:
            rack_index = game_player.rack.index(tile[0])
            game_player.rack.pop(rack_index)
        game_player.rack.extend(new_tiles)
        ScrabbleBoard(game.board).update_board(played_tiles)
    else:
        raise NotImplementedError(f"No turn action defined for {turn_action}")
    # save game and create turn object
    game.next_turn_index = (game.next_turn_index + 1) % game.racks.count()
    game_player.score += points
    game.save()
    game_player.save()
    turn_count = game.racks.aggregate(current_count=Max("turns__turn_count"))['current_count'] or 0
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
        go_out(game_player)
    return turn


def calculate_points(played_tiles, game):
    board = ScrabbleBoard(game.board)
    words = []
    # Transpose vertical plays
    if len(set(tile['y'] for tile in played_tiles)) != 1:
        played_tiles = [{**tile, "x": tile["y"], "y": tile["x"]} for tile in played_tiles]
        board.transpose_board()
    points, word = calculate_word_points(played_tiles, board)
    words.append(word)
    board.transpose_board()
    for tile in played_tiles:
        word_points, word = calculate_word_points([{**tile, "x": tile["y"], "y": tile["x"]}], board)
        points += word_points
        if word:
            words.append(word)
    if len(played_tiles) == 7:
        points += 50
    return points, words


def calculate_word_points(played_tiles, board):
    played_tiles = sorted(played_tiles, key=lambda play: play["x"])
    row = played_tiles[0]['y']
    start_x = played_tiles[0]['x']
    while start_x > 0 and board.get_tile(start_x - 1, row):
        start_x -= 1
    word = ''
    tile_index = 0
    word_multiplier = 1
    points = 0
    for x in range(start_x, 15):
        tile = board.get_tile(x, row)
        if tile:
            points += TILE_SCORES[tile[0]]
            word += tile[-1]
        elif tile_index < len(played_tiles) and played_tiles[tile_index]['x'] == x:
            tile = played_tiles[tile_index]['tile']
            letter_points = TILE_SCORES[tile[0]]
            multiplier = BOARD_CONFIG[x][row]
            if multiplier == Multiplier.dl:
                letter_points *= 2
            if multiplier == Multiplier.tl:
                letter_points *= 3
            if multiplier in [Multiplier.dw, Multiplier.start]:
                word_multiplier *= 2
            if multiplier == Multiplier.tw:
                word_multiplier *= 3
            points += letter_points
            word += tile[-1]
            tile_index += 1
        else:
            break
    points *= word_multiplier
    if len(word) > 1:
        return points, word
    return 0, None


def go_out(game_player):
    with transaction.atomic():
        for opponent in game_player.game.racks.exclude(user_id=game_player.id):
            for tile in opponent.rack:
                tile_score = TILE_SCORES[tile]
                game_player.score += tile_score
                opponent.score -= tile_score
            opponent.save()
        game_player.save()
        game_player.game.over = True
        game_player.game.save()


class ScrabbleBoard:
    def __init__(self, board):
        self.board = board

    def get_tile(self, x, y):
        return self.board[y][x]

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
        if x < 14:
            adjacent_squares.append((x + 1, y))
        if y > 0:
            adjacent_squares.append((x, y - 1))
        if y < 14:
            adjacent_squares.append((x, y + 1))
        return any(not self.is_free_square(adj_x, adj_y) for (adj_x, adj_y) in adjacent_squares)

    def update_board(self, play):
        for played_tile in play:
            self.board[played_tile['y']][played_tile['x']] = played_tile['tile']

    def transpose_board(self):
        self.board = [
            [self.board[y][x] for y in range(15)]
            for x in range(15)
        ]
