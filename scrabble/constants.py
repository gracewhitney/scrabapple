from django.db.models import TextChoices

TILE_FREQUENCIES = {
    'A': 9,
    'B': 2,
    'C': 2,
    'D': 4,
    'E': 12,
    'F': 2,
    'G': 3,
    'H': 2,
    'I': 9,
    # TODO: Finish
}


class TurnAction(TextChoices):
    play = "play"
    exchange = "exchange"
    pass_turn = "pass"
    forfeit = "forfeit"
