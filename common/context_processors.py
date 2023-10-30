def django_settings(request):
    from django.conf import settings
    return {
        "PRODUCTION": settings.PRODUCTION,
        "LOCALHOST": settings.LOCALHOST,
        "APP_DISPLAY_NAME": settings.APP_DISPLAY_NAME,
    }
