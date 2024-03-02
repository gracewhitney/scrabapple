from random import randint

from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.models import TimestampedModel, User
from scrabble.constants import TurnAction, WordGame


# Create your models here.
class ScrabbleGame(TimestampedModel):
    letter_bag = ArrayField(models.CharField(max_length=1))
    board = ArrayField(
        ArrayField(models.CharField(max_length=5, default=""), size=15),
        size=15
    )
    next_turn_index = models.IntegerField(default=0)
    over = models.BooleanField(default=False)
    game_type = models.CharField(choices=WordGame.choices, max_length=32)

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

    def all_turns(self):
        return GameTurn.objects.filter(
            game_player__game_id=self.id, deleted=False
        ).order_by('turn_count').select_related("game_player__user")

    def next_player(self):
        return self.racks.get(turn_index=self.next_turn_index)

    def winners(self):
        if not self.over:
            return []
        players = self.racks.exclude(forfeited=True).order_by('-score')
        max_score = players[0].score
        winners = []
        for player in players:
            if player.score == max_score:
                winners.append(player)
            else:
                break
        return winners


class GamePlayer(TimestampedModel):
    user = models.ForeignKey(User, related_name="game_racks", on_delete=models.PROTECT)
    game = models.ForeignKey(ScrabbleGame, related_name="racks", on_delete=models.CASCADE)
    rack = ArrayField(models.CharField(max_length=1), size=7, default=list)
    score = models.IntegerField(default=0)
    turn_index = models.IntegerField()
    forfeited = models.BooleanField(default=False)

    send_turn_notifications = models.BooleanField(default=False)

    class Meta:
        unique_together = [('game', 'turn_index'), ('game', 'user')]


class GameTurn(TimestampedModel):
    game_player = models.ForeignKey(GamePlayer, related_name="turns", on_delete=models.CASCADE)
    turn_count = models.IntegerField()
    turn_action = models.CharField(choices=TurnAction.choices, max_length=32)
    turn_words = ArrayField(models.CharField(max_length=15), null=True)
    score = models.IntegerField()
    rack_before_turn = ArrayField(models.CharField(max_length=1), size=7)
    turn_data = models.JSONField(null=True)
    deleted = models.BooleanField(default=False)
