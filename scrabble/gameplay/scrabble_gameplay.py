from django.core.exceptions import ValidationError

from scrabble.constants import Multiplier, WordGame
from scrabble.gameplay.base_calculator import BaseGameCalculator

SCRABBLE_TILE_FREQUENCIES = {
    'A': 9,
    'B': 2,
    'C': 2,
    'D': 4,
    'E': 12,
    'F': 2,
    'G': 3,
    'H': 2,
    'I': 9,
    'J': 1,
    'K': 1,
    'L': 4,
    'M': 2,
    'N': 6,
    'O': 8,
    'P': 2,
    'Q': 1,
    'R': 6,
    'S': 4,
    'T': 6,
    'U': 4,
    'V': 2,
    'W': 2,
    'X': 1,
    'Y': 2,
    'Z': 1,
    '-': 2,  # BLANK
}


class ScrabbleCalculator(BaseGameCalculator):
    game_type = WordGame.scrabble
    board_size = 15
    tile_frequencies = SCRABBLE_TILE_FREQUENCIES

    def validate_play(self, played_tiles, board, game_player):
        played_tiles = super().validate_play(played_tiles, board, game_player)
        # Play must not overlap an existing tile
        if any([not board.is_free_square(tile['x'], tile['y']) for tile in played_tiles]):
            raise ValidationError("Play includes non-empty square")
        return played_tiles

    def validate_first_play(self, played_tiles):
        # First play must include center tile
        if not any((tile['x'], tile['y']) == (7, 7) for tile in played_tiles):
            raise ValidationError("First play must include center tile")

    def calculate_word_points(self, played_tiles, board):
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

    def get_unplayed_tile_points(self, tile):
        return TILE_SCORES[tile]


BOARD_CONFIG = [
    [Multiplier.tw, None, None, Multiplier.dl, None, None, None, Multiplier.tw, None, None, None, Multiplier.dl, None, None, Multiplier.tw],
    [None, Multiplier.dw, None, None, None, Multiplier.tl, None, None, None, Multiplier.tl, None, None, None, Multiplier.dw, None],
    [None, None, Multiplier.dw, None, None, None, Multiplier.dl, None, Multiplier.dl, None, None, None, Multiplier.dw, None, None],
    [Multiplier.dl, None, None, Multiplier.dw, None, None, None, Multiplier.dl, None, None, None, Multiplier.dw, None, None, Multiplier.dl],
    [None, None, None, None, Multiplier.dw, None, None, None, None, None, Multiplier.dw, None, None, None, None],
    [None, Multiplier.tl, None, None, None, Multiplier.tl, None, None, None, Multiplier.tl, None, None, None, Multiplier.tl, None],
    [None, None, Multiplier.dl, None, None, None, Multiplier.dl, None, Multiplier.dl, None, None, None, Multiplier.dl, None, None],
    [Multiplier.tw, None, None, Multiplier.dl, None, None, None, Multiplier.start, None, None, None, Multiplier.dl, None, None, Multiplier.tw],
    [None, None, Multiplier.dl, None, None, None, Multiplier.dl, None, Multiplier.dl, None, None, None, Multiplier.dl, None, None],
    [None, Multiplier.tl, None, None, None, Multiplier.tl, None, None, None, Multiplier.tl, None, None, None, Multiplier.tl, None],
    [None, None, None, None, Multiplier.dw, None, None, None, None, None, Multiplier.dw, None, None, None, None],
    [Multiplier.dl, None, None, Multiplier.dw, None, None, None, Multiplier.dl, None, None, None, Multiplier.dw, None, None, Multiplier.dl],
    [None, None, Multiplier.dw, None, None, None, Multiplier.dl, None, Multiplier.dl, None, None, None, Multiplier.dw, None, None],
    [None, Multiplier.dw, None, None, None, Multiplier.tl, None, None, None, Multiplier.tl, None, None, None, Multiplier.dw, None],
    [Multiplier.tw, None, None, Multiplier.dl, None, None, None, Multiplier.tw, None, None, None, Multiplier.dl, None, None, Multiplier.tw],
]

TILE_SCORES = {
    'A': 1,
    'B': 3,
    'C': 3,
    'D': 2,
    'E': 1,
    'F': 4,
    'G': 2,
    'H': 4,
    'I': 1,
    'J': 8,
    'K': 5,
    'L': 1,
    'M': 3,
    'N': 1,
    'O': 1,
    'P': 3,
    'Q': 10,
    'R': 1,
    'S': 1,
    'T': 1,
    'U': 1,
    'V': 4,
    'W': 4,
    'X': 8,
    'Y': 4,
    'Z': 10,
    '-': 0,  # BLANK
}
