from django.forms import widgets


class EmailAutocompleteWidget(widgets.Input):
    template_name = "widgets/email_autocomplete.html"

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["users"] = [
            {"value": known_user.email, "label": f"{known_user.email} ({known_user.first_name})"}
            for known_user in sorted(self.user.known_users(), key=lambda u: u.get_short_name())
        ]
        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["className"] = attrs.pop("class", "")
        return attrs