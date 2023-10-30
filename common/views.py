from django.contrib import messages
from django.contrib.auth import logout, login
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic.base import TemplateView, View
from django.http.response import HttpResponse

from common.models import User


class IndexView(TemplateView):
    template_name = "common/index.html"


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



# START_FEATURE django_react
class DjangoReactView(TemplateView):
    # TODO: delete me; this is just a reference example
    template_name = 'common/sample_django_react.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hello_msg'] = 'Component'
        context['sample_props'] = {'msg': 'sample props'}
        return context
# END_FEATURE django_react


class OneTimeLoginView(FormView):
    form = SetPasswordForm
    template_name = "common/set_password.html"

    def get(self, request, *args, **kwargs):
        messages.info(request, "Please set a new password for your account.")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = get_object_or_404(User, one_time_passcode=self.kwargs["one_time_passcode"])
        login(self.request, user)
        user.one_time_passcode = ""
        user.set_password(form.cleaned_data["password"])
        user.save()
        messages.success(self.request, "You have successfully reset your password.")
        return redirect(self.request.GET.get("next", reverse("index")))


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)

def error_500(request):
    return render(request, "errors/500.html", status=500)
