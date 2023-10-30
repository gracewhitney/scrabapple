from django import forms

from common.forms import CrispyFormMixin


class CreateGameForm(CrispyFormMixin, forms.Form):
    submit_label = "Start Game"

    player_2_email = forms.EmailField()
    player_3_email = forms.EmailField(required=False)
    player_4_email = forms.EmailField(required=False)

