from collections import defaultdict
from random import randint

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Sum

from common.models import TimestampedModel, User
from scrabble.constants import TurnAction, WordGame, Dictionary


# Create your models here.
class ScrabbleGame(TimestampedModel):
    letter_bag = ArrayField(models.CharField(max_length=1))
    board = ArrayField(
        ArrayField(models.CharField(max_length=5, default=""), size=15),
        size=15
    )
    next_turn_index = models.IntegerField(default=0)
    over = models.BooleanField(default=False)
    archived_on = models.DateTimeField(null=True)
    game_type = models.CharField(choices=WordGame.choices, max_length=32)
    use_old_upwords_rules = models.BooleanField(default=False, blank=True)
    prevent_stack_duplicates = models.BooleanField(default=False, blank=True)
    validate_words = models.BooleanField(default=False, blank=True)
    selected_dictionaries = ArrayField(models.CharField(choices=Dictionary.choices, max_length=32), null=True)

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

    def last_turn(self):
        if not self.all_turns().exists():
            return None
        return self.all_turns().reverse()[0]

    def update_turn_index(self, backwards=False):
        update = -1 if backwards else 1
        self.next_turn_index = (self.next_turn_index + update) % self.racks.count()
        if not self.racks.exclude(rack=[]).exists():
            return
        if len(self.next_player().rack) == 0:
            self.update_turn_index(backwards=backwards)

    def next_player(self):
        return self.racks.get(turn_index=self.next_turn_index)

    def ordered_racks(self):
        return self.racks.order_by("turn_index").select_related("user")

    def winners(self, cached=True):
        if cached:
            return self.racks.filter(winner=True)
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

    def total_score(self):
        return self.racks.aggregate(Sum("score"))["score__sum"]

    def get_scorecard_rows(self):
        player_count = self.racks.count()
        player_turns = defaultdict(list)
        if not self.all_turns().exists():
            return []
        # It's possible for one player to have fewer turns at the end of the game (forfeit, upwords go out)
        for turn in self.all_turns():
            player_turns[turn.game_player.turn_index].append(turn)
        num_rounds = max(len(turns) for turns in player_turns.values())

        cumulative_scores = defaultdict(int)
        scorecard_rows = []
        round_list = []
        for round_index in range(num_rounds):
            for turn_index in range(player_count):
                if len(player_turns[turn_index]) < round_index + 1:
                    round_list.append((0, ""))
                else:
                    turn = player_turns[turn_index][round_index]
                    cumulative_scores[turn.game_player_id] += turn.score
                    round_list.append((turn.score, cumulative_scores[turn.game_player_id] if turn.score else "--"))
            scorecard_rows.append(round_list)
            round_list = []
        return scorecard_rows

    def get_dictionaries(self):
        ospds = [Dictionary.ospd2, Dictionary.ospd3, Dictionary.ospd4]
        if self.selected_dictionaries:
            dicts = list(self.selected_dictionaries)
            if set(dicts).intersection(ospds):
                dicts.append(Dictionary.long)
            return dicts
        return [*ospds, Dictionary.long]


class GamePlayer(TimestampedModel):
    user = models.ForeignKey(User, related_name="game_racks", on_delete=models.PROTECT)
    game = models.ForeignKey(ScrabbleGame, related_name="racks", on_delete=models.CASCADE)
    rack = ArrayField(models.CharField(max_length=1), size=7, default=list)
    score = models.IntegerField(default=0)
    turn_index = models.IntegerField()
    forfeited = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    winner = models.BooleanField(default=False)

    send_turn_notifications = models.BooleanField(default=False)

    class Meta:
        unique_together = [('game', 'turn_index'), ('game', 'user')]

    def get_player_initial(self):
        other_names = [rack.user.get_short_name().lower() for rack in self.game.racks.exclude(id=self.id)]
        player_name = self.user.get_short_name().lower()
        for i in range(len(player_name)):
            matches = [name for name in other_names if name[0:i+1] == player_name[0:i+1]]
            if not matches:
                return player_name[0:i+1]
        return player_name


class GameTurn(TimestampedModel):
    game_player = models.ForeignKey(GamePlayer, related_name="turns", on_delete=models.CASCADE)
    turn_count = models.IntegerField()
    turn_action = models.CharField(choices=TurnAction.choices, max_length=32)
    turn_words = ArrayField(models.CharField(max_length=15), null=True)
    score = models.IntegerField()
    rack_before_turn = ArrayField(models.CharField(max_length=1), size=7)
    turn_data = models.JSONField(null=True)
    deleted = models.BooleanField(default=False)
