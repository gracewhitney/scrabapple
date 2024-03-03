from django.core.exceptions import ValidationError

from scrabble.constants import WordGame, TurnAction
from scrabble.gameplay.base_calculator import BaseGameCalculator


UPWORDS_TILE_FREQUENCIES = {
    'A': 7,
    'B': 3,
    'C': 4,
    'D': 5,
    'E': 8,
    'F': 3,
    'G': 3,
    'H': 3,
    'I': 7,
    'J': 1,
    'K': 2,
    'L': 5,
    'M': 5,
    'N': 5,
    'O': 7,
    'P': 3,
    'Q': 1,
    'R': 5,
    'S': 6,
    'T': 5,
    'U': 5,
    'V': 1,
    'W': 2,
    'X': 1,
    'Y': 2,
    'Z': 1,
}


class UpwordsCalculator(BaseGameCalculator):
    game_type = WordGame.upwords
    board_size = 10
    bingo_points = 20
    tile_frequencies = UPWORDS_TILE_FREQUENCIES
    winner_takes_unplayed_points = False

    def validate_play(self, played_tiles, board, game_player):
        played_tiles = super().validate_play(played_tiles, board, game_player)
        assert(len(set(tile['y'] for tile in played_tiles)) == 1)
        if not any(board.get_tile(tile['x'], tile['y']) for tile in played_tiles):
            return played_tiles
        # Can't stack over 5 tiles high
        if any(len(board.get_tile(tile['x'], tile['y'])) > 4 for tile in played_tiles):
            raise ValidationError("Stack is over 5 high")
        # Can't duplicate an existing tile in the same position
        if self.game.prevent_stack_duplicates:
            if any((tile["tile"] in board.get_tile(tile['x'], tile['y'])) for tile in played_tiles):
                raise ValidationError("Duplicated tile in stack")
        else:
            if any(board.get_tile(tile['x'], tile['y'], most_recent=True) == tile["tile"] for tile in played_tiles):
                raise ValidationError("Duplicated tile")
        # Can't cover a whole word
        min_x = min(tile["x"] for tile in played_tiles)
        max_x = max(tile["x"] for tile in played_tiles)
        y = played_tiles[0]['y']
        if (
            max_x - min_x + 1 == len(played_tiles)
            and (min_x == 0 or board.get_tile(min_x - 1, y) == "")
            and (max_x == self.board_size - 1 or board.get_tile(max_x + 1, y) == "")
            and any((board.get_tile(i, y) and board.get_tile(i + 1, y)) for i in range(min_x, max_x))
        ):
            raise ValidationError("Play covers entire word")
        return played_tiles

    def validate_first_play(self, played_tiles):
        # First play must include one of the center tiles
        center_tiles = {(4, 4), (4, 5), (5, 4), (5, 5)}
        if not any((tile['x'], tile['y']) in center_tiles for tile in played_tiles):
            raise ValidationError("First play must include a center tile")

    def calculate_word_points(self, played_tiles, board):
        played_tiles = sorted(played_tiles, key=lambda play: play["x"])
        row = played_tiles[0]['y']
        start_x = played_tiles[0]['x']
        while start_x > 0 and board.get_tile(start_x - 1, row):
            start_x -= 1
        word = ''
        word_length = 0
        tile_index = 0
        points = 0
        max_height = 1
        has_q = False
        for x in range(start_x, self.board_size):
            letter = None
            board_tiles = board.get_tile(x, row)
            letter_points = len(board_tiles)
            if board_tiles:
                letter = board.get_tile(x, row, most_recent=True)
            if tile_index < len(played_tiles) and played_tiles[tile_index]['x'] == x:
                letter = played_tiles[tile_index]['tile']
                letter_points += 1
                tile_index += 1
            max_height = max(letter_points, max_height)
            if letter is None:
                break
            word += letter
            word_length += 1
            if letter == 'Q':
                has_q = True
                word += 'U'
            points += letter_points
        if max_height == 1:
            if has_q:
                points += 1
            points *= 2
        if word_length > 1:
            return points, word
        return 0, None

    def get_unplayed_tile_points(self, tile):
        return 5

    def game_over(self, game_player):
        if not self.game.use_old_upwords_rules:
            return super().game_over(game_player)
        return (
            len(self.game.letter_bag) == 0
            and all(
                turn.turn_action == TurnAction.pass_turn for turn in
                self.game.all_turns().order_by('-turn_count')[:self.game.racks.exclude(rack=[]).count()]
            )
        )