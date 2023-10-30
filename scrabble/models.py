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
    return ["" for _ in range(15) for _ in range(15)]


# Create your models here.
class ScrabbleGame(TimestampedModel):
    letter_bag = ArrayField(models.CharField(max_length=1), default=get_initial_letter_bag)
    board = ArrayField(
        ArrayField(models.CharField(max_length=1, default=""), size=15),
        default=get_initial_board,
        size=15
    )


class GamePlayer(TimestampedModel):
    user = models.ForeignKey(User, related_name="game_racks", on_delete=models.PROTECT)
    game = models.ForeignKey(ScrabbleGame, related_name="racks", on_delete=models.CASCADE)
    rack = ArrayField(models.CharField(max_length=1), size=7)
    score = models.IntegerField(default=0)
    turn_index = models.IntegerField()

    class Meta:
        unique_together = [('game', 'turn_index')]


class GameTurn(TimestampedModel):
    game_player = models.ForeignKey(User, related_name="turns", on_delete=models.CASCADE)
    turn_count = models.IntegerField()
    turn_action = models.CharField(choices=TurnAction.choices)
    score = models.IntegerField()
    rack_before_turn = ArrayField(models.CharField(max_length=1), size=7)
