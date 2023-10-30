from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import FormView, TemplateView

from common.models import User
from scrabble.forms import CreateGameForm
from scrabble.models import ScrabbleGame, GamePlayer


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
            user, created = User.objects.get_or_create(email=email)
            GamePlayer.objects.create(user=user, game=game, turn_index=turn_index)
            if created:

            turn_index += 1
        messages.success(self.request, f"New game created with {turn_index + 1} players.")
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
        return context
