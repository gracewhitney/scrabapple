from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.layout import Layout, Field, Div
from django import forms
from django.core.exceptions import ValidationError
from django.forms import CheckboxSelectMultiple

from common.forms import CrispyFormMixin
from common.widgets import EmailAutocompleteWidget
from scrabble.constants import WordGame, Dictionary
from scrabble.models import ScrabbleGame


class EditGameForm(CrispyFormMixin, forms.ModelForm):
    selected_dictionaries = forms.MultipleChoiceField(
        choices=Dictionary.choices, initial=[Dictionary.ospd2, Dictionary.ospd3], widget=CheckboxSelectMultiple,
        label="Choose dictionaries", required=False
    )

    class Meta:
        model = ScrabbleGame
        fields = [
            "use_old_upwords_rules", "prevent_stack_duplicates", "validate_words", "selected_dictionaries"
        ]
        labels = {
            "use_old_upwords_rules": "Use original end-of-game rules",
            "prevent_stack_duplicates": "Disallow repeated letters in the same stack",
            "validate_words": "Enforce word validation",
            "selected_dictionaries": "Choose dictionaries",
        }
        help_texts = {
            "use_old_upwords_rules": "If this is checked, play continues until all players pass, "
                                     "instead of ending once one player has used all their tiles.",
            "prevent_stack_duplicates": "If this is checked, validation checks all tiles in the stack for duplicates, "
                                        "rather then just the most recent one.",
            "validate_words": "If this is checked, plays may only contain words that are included in one of the "
                              "selected dictionaries. If unchecked, invalid words will not block play."
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Field("validate_words"),
            Div(
                Field("use_old_upwords_rules"),
                Field("prevent_stack_duplicates"),
                v_if=f"game_type === '{WordGame.upwords.value}'",
                v_cloak=True,
            ),
            InlineCheckboxes("selected_dictionaries", wrapper_class="override-legend"),
        )


class CreateGameForm(EditGameForm):
    submit_label = "Start Game"

    player_2_email = forms.EmailField()
    player_3_email = forms.EmailField(required=False)
    player_4_email = forms.EmailField(required=False)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for field in ["player_2_email", "player_3_email", "player_4_email"]:
            self.fields[field].widget = EmailAutocompleteWidget(user=user)
        self.helper.layout = Layout(
            Div(
                Field("game_type", v_model="game_type"),
                Field("validate_words"),
                Div(
                    Field("use_old_upwords_rules"),
                    Field("prevent_stack_duplicates"),
                    v_if=f"game_type === '{WordGame.upwords.value}'",
                    v_cloak=True,
                ),
                css_id="vue-anchor"
            ),
            InlineCheckboxes("selected_dictionaries", wrapper_class="override-legend"),
            "player_2_email",
            "player_3_email",
            "player_4_email",
        )

    class Meta(EditGameForm.Meta):
        fields = EditGameForm.Meta.fields + ["game_type"]

    def clean(self):
        cleaned_data = super().clean()
        emails = list(filter(
            None,
            [cleaned_data.get('player_2_email'), cleaned_data.get('player_3_email'), cleaned_data.get('player_4_email')]
        )) + [self.user.email]
        if len(set(emails)) != len(emails):
            raise ValidationError("You cannot invite the same person to a game twice.")
        return cleaned_data

