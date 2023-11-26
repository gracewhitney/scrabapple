from random import randint

from django.contrib.admin.utils import flatten
from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.models import TimestampedModel, User
from scrabble.constants import TILE_FREQUENCIES, TurnAction


def get_initial_letter_bag():
    # Returns full letter bag, ordered
    return flatten([letter for (letter, count) in TILE_FREQUENCIES.items() for _ in range(count)])


def get_initial_board():
    # Return 15 * 15 array of empty strings
    return [["" for _ in range(15)] for _ in range(15)]


# Create your models here.
class ScrabbleGame(TimestampedModel):
    letter_bag = ArrayField(models.CharField(max_length=1), default=get_initial_letter_bag)
    board = ArrayField(
        ArrayField(models.CharField(max_length=2, default=""), size=15),
        default=get_initial_board,
        size=15
    )
    next_turn_index = models.IntegerField(default=0)
    over = models.BooleanField(default=False)

    def draw_tiles(self, num_tiles, commit=False):
        """Returns num_tiles tiles & new letter bag. If commit=True, also saves letter bag."""
        tiles = []
        for _ in range(num_tiles):
            if len(self.letter_bag) == 0:
                break
            tile = self.letter_bag.pop(randint(0, len(self.letter_bag) - 1))
            tiles.append(tile)
        if commit:
            self.save()
        return tiles


class GamePlayer(TimestampedModel):
    user = models.ForeignKey(User, related_name="game_racks", on_delete=models.PROTECT)
    game = models.ForeignKey(ScrabbleGame, related_name="racks", on_delete=models.CASCADE)
    rack = ArrayField(models.CharField(max_length=1), size=7, default=list)
    score = models.IntegerField(default=0)
    turn_index = models.IntegerField()
    forfeited = models.BooleanField(default=False)

    class Meta:
        unique_together = [('game', 'turn_index'), ('game', 'user')]


class GameTurn(TimestampedModel):
    game_player = models.ForeignKey(GamePlayer, related_name="turns", on_delete=models.CASCADE)
    turn_count = models.IntegerField()
    turn_action = models.CharField(choices=TurnAction.choices, max_length=32)
    turn_words = ArrayField(models.CharField(max_length=15), null=True)
    score = models.IntegerField()
    rack_before_turn = ArrayField(models.CharField(max_length=1), size=7)
