from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from sentry_sdk import capture_exception

from common.models import User
from scrabble.constants import WordGame, TurnAction
from scrabble.gameplay.scrabble_gameplay import ScrabbleCalculator
from scrabble.gameplay.upwords_gameplay import UpwordsCalculator
from scrabble.models import ScrabbleGame, GamePlayer


def send_invitation_email(user, game, request):
    template_name = "emails/new_user_invitation.html" if user.one_time_passcode else "emails/existing_user_invitation.html"
    message = render_to_string(template_name, context={
        "user": user,
        "game_id": game.id,
        "game_type": game.game_type,
    }, request=request)
    try:
        send_mail(
            f"Play {game.game_type}!",
            "Your email viewer does not support html. Please use a different viewer.",
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except Exception as e:
        capture_exception(e)
        messages.error(request, "The invitation email could not be sent. Please invite your opponents via another channel.")


def create_new_game(form, user, request=None):
    game = form.save(commit=False)
    calculator = get_calculator(game)
    game.board = calculator.get_initial_board()
    game.letter_bag = calculator.get_initial_letter_bag()
    game.save()
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
        send_invitation_email(user, game, request=request)
        turn_index += 1
    return game


def get_calculator(game):
    calculator_mapping = {
        WordGame.scrabble: ScrabbleCalculator,
        WordGame.upwords: UpwordsCalculator,
    }
    return calculator_mapping[game.game_type](game=game)


def send_turn_notification(game, request):
    player = game.next_player()
    if player.send_turn_notifications:
        message = render_to_string(
            "emails/turn_notification.html",
            context={
                "game": game,
                "player": player,
                "TurnAction": TurnAction,
            },
            request=request
        )
        send_mail(
            f"It's your turn!",
            "Your email viewer does not support html. Please use a different viewer.",
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[player.user.email],
        )
