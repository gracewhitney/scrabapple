from crispy_forms.layout import Layout, Field, Div
from django import forms

from common.forms import CrispyFormMixin
from scrabble.constants import WordGame


class CreateGameForm(CrispyFormMixin, forms.Form):
    submit_label = "Start Game"

    game_type = forms.ChoiceField(choices=WordGame.choices)
    use_old_upwords_rules = forms.BooleanField(
        required=False, label="Use original end-of-game rules",
        help_text="If this is checked, play continues until all players pass, "
                  "instead of ending once one player has used all their tiles."
    )
    player_2_email = forms.EmailField()
    player_3_email = forms.EmailField(required=False)
    player_4_email = forms.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Field("game_type", v_model="game_type"),
            Div(Field("use_old_upwords_rules"), v_if=f"game_type === '{WordGame.upwords.value}'"),
            "player_2_email",
            "player_3_email",
            "player_4_email",
        )

