import json

import rest_framework.exceptions
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from scrabble.constants import TILE_SCORES, BOARD_CONFIG, Multiplier, TurnAction
from scrabble.forms import CreateGameForm
from scrabble.gameplay import validate_turn, do_turn, create_new_game, calculate_points
from scrabble.models import ScrabbleGame, GamePlayer


# Create your views here.
class CreateGameView(LoginRequiredMixin, FormView):
    template_name = "scrabble/new_game.html"
    form_class = CreateGameForm

    def form_valid(self, form):
        game = create_new_game(form, self.request.user, self.request)
        messages.success(
            self.request, f"New game created with {game.racks.count()} players. Invitation emails have been issued."
        )
        return redirect("scrabble:play_scrabble", game_id=game.id)


class GamePermissionMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        self.scrabble_game = get_object_or_404(ScrabbleGame, id=self.get_game_id())
        return GamePlayer.objects.filter(game_id=self.scrabble_game.id, user_id=self.request.user.id).exists()

    def get_game_id(self):
        return self.kwargs.get("game_id")


class ScrabbleView(GamePermissionMixin, TemplateView):
    template_name = "scrabble/scrabble_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game_player = GamePlayer.objects.get(game=self.scrabble_game, user=self.request.user)
        in_turn = game_player.turn_index == self.scrabble_game.next_turn_index
        # TODO add react data
        context.update({
            "game": self.scrabble_game,
            "game_player": game_player,
            "in_turn": in_turn,
            "score_url": reverse("scrabble:score_play", kwargs={"game_id": self.scrabble_game.id}),
            "turn_url": reverse("scrabble:post_scrabble_play", kwargs={"game_id": self.scrabble_game.id}),
            "rack": [{"letter": letter} for letter in game_player.rack],
            "BOARD_CONFIG": BOARD_CONFIG,
            "TILE_SCORES": TILE_SCORES,
            "Multiplier": Multiplier,
            "TurnAction": TurnAction,
        })
        return context


class ScrabbleTurnView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        turn_data = json.loads(request.body.decode())
        game_player = GamePlayer.objects.get(game=self.scrabble_game, user=self.request.user)
        with transaction.atomic():
            try:
                cleaned_turn_data = validate_turn(turn_data, self.scrabble_game, game_player)
            except ValidationError as e:
                return JsonResponse(status=400, data={"error": e.message})
            turn = do_turn(cleaned_turn_data, self.scrabble_game, game_player)
            if turn.turn_action == TurnAction.play:
                success_message = f"You played {', '.join(turn.turn_words)} for {turn.score} points."
            else:
                success_message = "Your turn is complete."
            messages.success(request, success_message)
        return redirect('scrabble:play_scrabble', game_id=self.scrabble_game.id)


class ScrabbleCalculateScoreView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        turn_data = json.loads(request.body.decode())
        game_player = GamePlayer.objects.get(game=self.scrabble_game, user=self.request.user)
        try:
            cleaned_turn_data = validate_turn(turn_data, self.scrabble_game, game_player)
        except ValidationError as e:
            return JsonResponse(status=400, data={"error": e.message})
        if cleaned_turn_data["action"] != TurnAction.play:
            return JsonResponse(status=400, data={"error": "Invalid action"})
        points, _ = calculate_points(cleaned_turn_data["played_tiles"], self.scrabble_game)
        return JsonResponse(data={"points": points})


class GameTurnIndexView(GamePermissionMixin, View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(data={'turn_index': self.scrabble_game.next_turn_index})
