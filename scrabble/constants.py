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
    end_game = "end_game"


class Dictionary(TextChoices):
    ospd2 = "ospd2", "OSPD2"
    ospd3 = "ospd3", "OSPD3"
    ospd4 = "ospd4", "OSPD4"
    csw = "csw12", "CSW12"
    enable = "ENABLE", "ENABLE"
    long = "long", "Long Words"


BLANK_CHARS = ['-', '*']
