from django.shortcuts import render
from django.views.generic import FormView

from scrabble.forms import CreateGameForm
from scrabble.models import ScrabbleGame


# Create your views here.
class CreateGameView(FormView):
    template_name = "scrabble/new_game.html"
    form_class = CreateGameForm

    def form_valid(self, form):
        game = ScrabbleGame.objects.create()


