from crispy_forms.layout import Layout, Field, Div
from django import forms

from common.forms import CrispyFormMixin
from scrabble.constants import WordGame
from scrabble.models import ScrabbleGame


class CreateGameForm(CrispyFormMixin, forms.ModelForm):
    submit_label = "Start Game"

    player_2_email = forms.EmailField()
    player_3_email = forms.EmailField(required=False)
    player_4_email = forms.EmailField(required=False)

    class Meta:
        model = ScrabbleGame
        fields = ["game_type", "use_old_upwords_rules", "prevent_stack_duplicates"]
        labels = {
            "use_old_upwords_rules": "Use original end-of-game rules",
            "prevent_stack_duplicates": "Disallow repeated letters in the same stack",
        }
        help_texts = {
            "use_old_upwords_rules": "If this is checked, play continues until all players pass, "
                                     "instead of ending once one player has used all their tiles.",
            "prevent_stack_duplicates": "If this is checked, validation checks all tiles in the stack for duplicates, "
                                        "rather then just the most recent one."
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Field("game_type", v_model="game_type"),
            Div(
                Field("use_old_upwords_rules"),
                Field("prevent_stack_duplicates"),
                v_if=f"game_type === '{WordGame.upwords.value}'",
                v_cloak=True,
            ),
            "player_2_email",
            "player_3_email",
            "player_4_email",
        )

