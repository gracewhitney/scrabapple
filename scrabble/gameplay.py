from django.core.exceptions import ValidationError

from scrabble.constants import TurnAction
from scrabble.serializers import GameTurnSerializer


def validate_turn(turn_data, game, game_player):
    # Check that turn is allowed
    if game_player.turn_index != game.next_turn_index:
        raise ValidationError("Wrong player.")
    # deserialize turn data
    serializer = GameTurnSerializer(data=turn_data)
    serializer.is_valid()
    turn_action = serializer.validated_data["turn_action"]
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
        if any(tile.tile not in game_player.rack for tile in played_tiles):
            raise ValidationError("Invalid tile, not in rack")
        board = ScrabbleBoard(game.board)
        if board.is_first_play():
            # First play must include center tile
            if not any((tile.x, tile.y) == (7, 7) for tile in played_tiles):
                raise ValidationError("First play must include center tile")
        else:
            # Subsequent plays must be adjacent to existing word
            if not any(board.has_adjacent_tile(tile.x, tile.y) for tile in played_tiles):
                raise ValidationError("Disconnected play")
        # Play must not overlap an existing tile
        if any([not board.is_free_square(tile.x, tile.y) for tile in played_tiles]):
            raise ValidationError("Play includes non-empty square")
        # Play must be in a single row or column
        if len(set(tile.x for tile in played_tiles)) > 1 and len(set(tile.y for tile in played_tiles)) > 1:
            raise ValidationError("Play not in line")
        return serializer.validated_data
    else:
        raise NotImplementedError(f"Turn validation not implemented for {turn_action}")

def do_turn(turn_data, game, game_player):
    """Returns turn score and mutates rack & letter bag in place"""
    turn_action = turn_data["action"]
    if turn_action == TurnAction.pass_turn:
        return 0
    if turn_action == TurnAction.exchange:
        exchanged_tiles = turn_data["exchanged_tiles"]
        new_tiles = game.draw_tiles(len(exchanged_tiles))
        for tile in exchanged_tiles:
            rack_index = game_player.rack.find(tile)
            game_player.rack.pop(rack_index)
            game.letter_bag.append(tile)
        game_player.rack.extend(new_tiles)
        return 0
    if turn_action == TurnAction.forfeit:
        game_player.forfeited = True
        if game.racks.count() == 2:
            game.over = True
        return 0
    if turn_action == TurnAction.play:
        played_tiles = turn_data["played_tiles"]
        points = calculate_points(played_tiles, game)
        played_tiles = [tile.tile for tile in played_tiles]
        new_tiles = game.draw_tiles(len(played_tiles))
        for tile in played_tiles:
            rack_index = game_player.rack.find(tile)
            game_player.rack.pop(rack_index)
        game_player.rack.extend(new_tiles)
        ScrabbleBoard(game.board).update_board(played_tiles)
        return points
    else:
        raise NotImplementedError(f"No turn action defined for {turn_action}")


def calculate_points(played_tiles, game):
    # TODO
    horizontal_play = len(set(tile.y for tile in played_tiles)) == 1
    if horizontal_play:
        pass
    return 0


class ScrabbleBoard:
    def __init__(self, board):
        self.board = board

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
