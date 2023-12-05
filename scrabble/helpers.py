from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from sentry_sdk import capture_exception


def send_invitation_email(user, game_id, new_user, request):
    template_name = "emails/new_user_invitation.html" if new_user else "emails/existing_user_invitation.html"
    message = render_to_string(template_name, context={
        "user": user,
        "game_id": game_id
    }, request=request)
    try:
        send_mail(
            "Play scrabble!",
            "Your email viewer does not support html. Please use a different viewer.",
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except Exception as e:
        capture_exception(e)
        messages.error(request, "The invitation email could not be sent. Please invite your opponents via another channel.")


