import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.crypto import get_random_string
from django.views.generic import FormView, TemplateView

from common.models import User
from scrabble.constants import TILE_SCORES, TurnAction
from scrabble.forms import CreateGameForm
from scrabble.helpers import send_invitation_email
from scrabble.gameplay import validate_turn, calculate_points, do_turn
from scrabble.models import ScrabbleGame, GamePlayer, GameTurn


# Create your views here.
class CreateGameView(LoginRequiredMixin, FormView):
    template_name = "scrabble/new_game.html"
    form_class = CreateGameForm

    def form_valid(self, form):
        game = ScrabbleGame.objects.create()
        GamePlayer.objects.create(user=self.request.user, game=game, turn_index=0)
        turn_index = 1
        for email in [
            form.cleaned_data["player_2_email"],
            form.cleaned_data.get("player_3_email"),
            form.cleaned_data.get("player_4_email")
        ]:
            if not email:
                break
            user, created = User.objects.get_or_create(
                email=email, defaults={"one_time_passcode": get_random_string(32)}
            )
            GamePlayer.objects.create(user=user, game=game, turn_index=turn_index)
            send_invitation_email(user, game.id, new_user=created)
            turn_index += 1
        messages.success(
            self.request, f"New game created with {turn_index + 1} players. Invitation emails have been issued."
        )
        return redirect("play_scrabble", game_id=game.id)


class GamePermissionMixin(UserPassesTestMixin):
    def test_func(self):
        self.scrabble_game = get_object_or_404(ScrabbleGame, id=self.get_game_id())
        return GamePlayer.objects.filter(game_id=self.scrabble_game.id, user=self.request.user).exists()

    def get_game_id(self):
        return self.kwargs.get("game_id")


class ScrabbleView(GamePermissionMixin, TemplateView):
    template_name = "scrabble/scrabble_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game_player = GamePlayer.objects.get(game=self.scrabble_game, user=self.request.user)
        # TODO add react data
        context["game"] = self.scrabble_game
        context["rack"] = [{"letter": letter, "points": TILE_SCORES[letter]} for letter in game_player.rack]
        return context


class ScrabbleTurnView(GamePermissionMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        turn_data = json.loads(request.body.decode())
        game_player = GamePlayer.objects.get(game=self.scrabble_game, user=self.request.user)
        try:
            cleaned_turn_data = validate_turn(turn_data, self.scrabble_game, game_player)
        except ValidationError as e:
            return JsonResponse(status=400, data={"error": e.message})
        turn_score, updated_rack, updated_letter_bag = do_turn(cleaned_turn_data, self.scrabble_game, game_player)
        with transaction.atomic():
            GameTurn.objects.create(
                game_player
            )
