import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import FormView, TemplateView

from scrabble.constants import TILE_SCORES, BOARD_CONFIG, Multiplier, TurnAction
from scrabble.forms import CreateGameForm
from scrabble.gameplay import validate_turn, do_turn, create_new_game
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
        # TODO add react data
        context.update({
            "game": self.scrabble_game,
            "game_player": game_player,
            "rack": [{"letter": letter, "points": TILE_SCORES[letter]} for letter in game_player.rack],
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
            do_turn(cleaned_turn_data, self.scrabble_game, game_player)
        return redirect('scrabble:play_scrabble', game_id=self.scrabble_game.id)
