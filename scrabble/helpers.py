from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from sentry_sdk import capture_exception

from common.models import User
from scrabble.constants import WordGame
from scrabble.gameplay.scrabble_gameplay import ScrabbleCalculator
from scrabble.gameplay.upwords_gameplay import UpwordsCalculator
from scrabble.models import ScrabbleGame, GamePlayer


def send_invitation_email(user, game, new_user, request):
    template_name = "emails/new_user_invitation.html" if new_user else "emails/existing_user_invitation.html"
    message = render_to_string(template_name, context={
        "user": user,
        "game_id": game.id,
        "game_type": game.game_type,
    }, request=request)
    try:
        send_mail(
            f"Play {game.game_type.value}!",
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except Exception as e:
        capture_exception(e)
        messages.error(request, "The invitation email could not be sent. Please invite your opponents via another channel.")


def create_new_game(form, user, request=None):
    game = ScrabbleGame.objects.create(game_type=form.cleaned_data["game_type"])
    GamePlayer.objects.create(user=user, game=game, turn_index=0, rack=game.draw_tiles(7, commit=True))
    turn_index = 1
    for email in [
        form.cleaned_data["player_2_email"],
        form.cleaned_data.get("player_3_email"),
        form.cleaned_data.get("player_4_email")
    ]:
        if not email:
            break
        user, created = User.objects.get_or_create(
            email=email, defaults={"one_time_passcode": get_random_string(32)}
        )
        GamePlayer.objects.create(user=user, game=game, turn_index=turn_index, rack=game.draw_tiles(7, commit=True))
        send_invitation_email(user, game, new_user=created, request=request)
        turn_index += 1
    return game


def get_calculator(game):
    calculator_mapping = {
        WordGame.scrabble: ScrabbleCalculator,
        WordGame.upwords: UpwordsCalculator,
    }
    return calculator_mapping[game.game_type](game=game)
