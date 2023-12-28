from django.db.models import TextChoices


class WordGame(TextChoices):
    scrabble = 'scrabble'
    upwords = 'upwords'


class Multiplier(TextChoices):
    dl = 'dl', "Double Letter Score"
    tl = 'tl', "Triple Letter Score"
    dw = 'dw', "Double Word Score"
    tw = 'tw', "Triple Word Score"
    start = 'start', "Starting Square"


class TurnAction(TextChoices):
    play = "play"
    exchange = "exchange"
    pass_turn = "pass"
    forfeit = "forfeit"
