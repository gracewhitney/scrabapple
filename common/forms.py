from django import forms
from django.contrib.auth.forms import SetPasswordForm as AuthSetPasswordForm, PasswordChangeForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from common.models import User


class CrispyFormMixin(object):
    submit_label = "Save"
    form_action = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "POST"
        self.helper.form_action = self.form_action
        self.helper.add_input(Submit("submit", self.submit_label))


class SetPasswordForm(CrispyFormMixin, AuthSetPasswordForm):
    pass


class UpdatePasswordForm(CrispyFormMixin, PasswordChangeForm):
    pass


class UserSettingsForm(CrispyFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email']
        labels = {
            'first_name': "Display Name",
        }
