from django.core.exceptions import ValidationError
from django.db import transaction

from scrabble.constants import TILE_SCORES, BOARD_CONFIG, Multiplier, WordGame
from scrabble.gameplay.base_calculator import BaseGameCalculator


class ScrabbleCalculator(BaseGameCalculator):
    game_type = WordGame.scrabble

    def validate_play(self, played_tiles, board, game_player):
        super().validate_play(played_tiles, board, game_player)
        # Play must not overlap an existing tile
        if any([not board.is_free_square(tile['x'], tile['y']) for tile in played_tiles]):
            raise ValidationError("Play includes non-empty square")

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

    def go_out(self, game_player):
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
