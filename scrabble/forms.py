from django import forms

from common.forms import CrispyFormMixin
from scrabble.constants import WordGame


class CreateGameForm(CrispyFormMixin, forms.Form):
    submit_label = "Start Game"

    game_type = forms.ChoiceField(choices=WordGame.choices)
    player_2_email = forms.EmailField()
    player_3_email = forms.EmailField(required=False)
    player_4_email = forms.EmailField(required=False)

