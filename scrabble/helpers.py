from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string

from scrabble.constants import TurnAction
from scrabble.models import GamePlayer
from scrabble.serializers import GameTurnSerializer


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


def validate_turn(turn_data, game, user):
    game_player = GamePlayer.objects.get(game=game, user=user)
    # Check that turn is allowed
    if game_player.turn_index != game.next_turn_index:
        raise ValidationError("Wrong player.")
    # deserialize turn data
    serializer = GameTurnSerializer(data=turn_data)
    serializer.is_valid()
    turn_action = serializer.validated_data["turn_action"]
    if turn_action in [TurnAction.pass_turn, TurnAction.forfeit]:
        return []
    if turn_action == TurnAction.exchange:
        if any(tile not in game_player.rack for tile in serializer.validated_data["exchanged_tiles"]):
            raise ValidationError("Invalid tile to exchange")
        return []




def calculate_points(turn_data, game):
    return 0