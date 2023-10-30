from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_invitation_email(user, game_id, new_user):
    template_name = "emails/new_user_invitation.html" if new_user else "emails/existing_user_invitation.html"
    message = render_to_string(template_name, context={
        "user": user,
        "game_id": game_id
    })
    send_mail(
        "Play scrabble!",
        message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
