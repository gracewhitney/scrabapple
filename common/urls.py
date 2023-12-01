from django.conf import settings
from django.urls import include, path

from common import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("settings/", views.UserSettingsView.as_view(), name="user_settings"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots_txt"),
    path("one-time/<str:one_time_passcode>/", views.OneTimeLoginView.as_view(), name="one_time_login"),
]

# START_FEATURE debug_toolbar
if settings.DEBUG_TOOLBAR:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
# END_FEATURE debug_toolbar
