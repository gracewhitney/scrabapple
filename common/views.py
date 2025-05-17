from django.contrib import messages
from django.contrib.auth import logout, login
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView
from django.views.generic.base import TemplateView, View
from django.http.response import HttpResponse

from common.forms import SetPasswordForm, UserSettingsForm, UpdatePasswordForm
from common.models import User
from scrabble.helpers import get_user_statistics


class IndexView(TemplateView):
    template_name = "common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context.update({
                "in_progress_games": self.request.user.in_progress_games(),
                "past_games": self.request.user.completed_games().order_by("-created_on"),
                "user_statistics": get_user_statistics(self.request.user),
            })
        return context


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("index")


class RobotsTxtView(View):
    def get(self, request):
        if settings.PRODUCTION:
            # Allow all (note that a blank Disallow block means "allow all")
            lines = ["User-agent: *", "Disallow:"]
        else:
            # Block all
            lines = ["User-agent: *", "Disallow: /"]
        return HttpResponse("\n".join(lines), content_type="text/plain")


class OneTimeLoginView(FormView):
    form_class = SetPasswordForm
    template_name = "common/set_password.html"

    def get(self, request, *args, **kwargs):
        messages.info(request, "Please set a new password for your account.")
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        self.user = get_object_or_404(User, one_time_passcode=self.kwargs["one_time_passcode"])
        form_kwargs["user"] = self.user
        return form_kwargs

    def form_valid(self, form):
        user = self.user
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        user.one_time_passcode = ""
        user.set_password(form.cleaned_data["new_password1"])
        user.save()
        messages.success(self.request, "You have successfully reset your password.")
        return redirect(self.request.GET.get("next", reverse("index")))


class UserSettingsView(LoginRequiredMixin, FormView):
    form_class = UserSettingsForm
    success_url = reverse_lazy("user_settings")
    template_name = "common/user_settings.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your changes have been saved.")
        return super().form_valid(form)


class UpdatePasswordView(LoginRequiredMixin, FormView):
    form_class = UpdatePasswordForm
    success_url = reverse_lazy("login")
    template_name = "common/change_password.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your password has been updated. Please log in again.")
        logout(self.request)
        return super().form_valid(form)


class PrivacyPolicyView(TemplateView):
    template_name = "common/privacy_policy.html"


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
