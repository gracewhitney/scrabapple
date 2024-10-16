import json
from collections import Counter

import dawg
from django.contrib import messages
from django.contrib.admin.utils import flatten
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from scrabble.constants import Multiplier, TurnAction, WordGame, Dictionary
from scrabble.dictionaries import validate_word
from scrabble.gameplay.scrabble_gameplay import BOARD_CONFIG, TILE_SCORES
from scrabble.forms import CreateGameForm, EditGameForm
from scrabble.helpers import create_new_game, get_calculator, send_turn_notification
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
        return redirect("scrabble:play_game", game_id=game.id)


class GamePermissionMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        self.game = get_object_or_404(ScrabbleGame, id=self.get_game_id())
        return GamePlayer.objects.filter(game_id=self.game.id, user_id=self.request.user.id).exists()

    def get_game_id(self):
        return self.kwargs.get("game_id")


class GameView(GamePermissionMixin, TemplateView):
    template_name = "scrabble/word_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game_player = GamePlayer.objects.get(game=self.game, user=self.request.user)
        in_turn = game_player.turn_index == self.game.next_turn_index and not self.game.over
        last_turn = self.game.all_turns().last()
        can_undo = last_turn.game_player == game_player if last_turn else False
        remaining_letters = self.game.letter_bag + flatten(
            self.game.racks.exclude(user=self.request.user).values_list('rack', flat=True)
        )
        context.update({
            "game": self.game,
            "game_player": game_player,
            "in_turn": in_turn,
            "can_undo": can_undo,
            "rack": [{"letter": letter} for letter in game_player.rack],
            "letter_counts": sorted(Counter(remaining_letters).items()),
            "TurnAction": TurnAction,
            "WordGame": WordGame,
        })
        if self.game.game_type == WordGame.scrabble:
            context.update({
                "BOARD_CONFIG": BOARD_CONFIG,
                "TILE_SCORES": TILE_SCORES,
                "Multiplier": Multiplier,
            })
        return context


class EditGameOptionsView(GamePermissionMixin, FormView):
    form_class = EditGameForm
    template_name = "scrabble/edit_game_options.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.game
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your changes have been saved")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("scrabble:play_game", kwargs={"game_id": self.game.id})


class GameTurnView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        turn_data = json.loads(request.body.decode())
        game_player = GamePlayer.objects.get(game=self.game, user=self.request.user)
        calculator = get_calculator(self.game)
        with transaction.atomic():
            try:
                cleaned_turn_data = calculator.validate_turn(turn_data, game_player)
                turn = calculator.do_turn(cleaned_turn_data, game_player)
            except ValidationError as e:
                return JsonResponse(status=400, data={"error": e.message})
            if turn.turn_action == TurnAction.play:
                success_message = f"You played {', '.join(turn.turn_words)} for {turn.score} points."
            else:
                success_message = "Your turn is complete."
            messages.success(request, success_message)
        send_turn_notification(self.game, request)
        return redirect('scrabble:play_game', game_id=self.game.id)


class CalculateScoreView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        turn_data = json.loads(request.body.decode())
        game_player = GamePlayer.objects.get(game=self.game, user=self.request.user)
        calculator = get_calculator(self.game)
        try:
            cleaned_turn_data = calculator.validate_turn(turn_data, game_player, check_player=False)
        except ValidationError as e:
            return JsonResponse(status=400, data={"error": e.message})
        if cleaned_turn_data["action"] != TurnAction.play:
            return JsonResponse(status=400, data={"error": "Invalid action"})
        points, words = calculator.calculate_points(cleaned_turn_data["played_tiles"])
        invalid_words = calculator.validate_words(words)
        return JsonResponse(data={"points": points, "words": words, "invalidWords": invalid_words})


class GameTurnIndexView(GamePermissionMixin, View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(data={'turn_index': self.game.next_turn_index})


class UpdateRackView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        game_player = GamePlayer.objects.get(game=self.game, user=self.request.user)
        rack = json.loads(request.body.decode())
        if Counter(rack) != Counter(game_player.rack):
            return JsonResponse(status=400, data={"error": "Rack does not match."})
        game_player.update(rack=rack)
        return JsonResponse(data={"message": "Rack successfully updated."})


class UndoTurnView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        game_player = GamePlayer.objects.get(game=self.game, user=self.request.user)
        calc = get_calculator(self.game)
        try:
            calc.undo_last_turn(game_player)
        except ValidationError as e:
            messages.error(request, f"Can't undo turn: {e.message}")
        return redirect("scrabble:play_game", game_id=self.game.id)


class ToggleNotificationsView(GamePermissionMixin, View):
    def post(self, request, *args, **kwargs):
        game_player = GamePlayer.objects.get(game=self.game, user=self.request.user)
        game_player.update(send_turn_notifications=not game_player.send_turn_notifications)
        return redirect("scrabble:play_game", game_id=self.game.id)
