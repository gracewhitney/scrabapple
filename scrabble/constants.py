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
    'J': 1,
    'K': 1,
    'L': 4,
    'M': 2,
    'N': 6,
    'O': 8,
    'P': 2,
    'Q': 1,
    'R': 6,
    'S': 4,
    'T': 6,
    'U': 4,
    'V': 2,
    'W': 2,
    'X': 1,
    'Y': 2,
    'Z': 2,
    '-': 2,  # BLANK
}

TILE_SCORES = {
    'A': 1,
    'B': 3,
    'C': 3,
    'D': 2,
    'E': 1,
    'F': 4,
    'G': 2,
    'H': 4,
    'I': 1,
    'J': 8,
    'K': 5,
    'L': 1,
    'M': 3,
    'N': 1,
    'O': 1,
    'P': 3,
    'Q': 10,
    'R': 1,
    'S': 1,
    'T': 1,
    'U': 1,
    'V': 4,
    'W': 4,
    'X': 8,
    'Y': 4,
    'Z': 10,
    '-': 0,  # BLANK
}


class Multipliers(TextChoices):
    dl = 'dl', "Double Letter Score"
    tl = 'tl', "Triple Letter Score"
    dw = 'dw', "Double Word Score"
    tw = 'tw', "Triple Word Score"


BOARD_CONFIG = [
    [Multipliers.tw, None, None, Multipliers.dl, None, None, None, Multipliers.tw, None, None, None, Multipliers.dl, None, None, Multipliers.tw],
    [None, Multipliers.dw, None, None, None, Multipliers.tl, None, None, None, Multipliers.tl, None, None, None, Multipliers.dw, None],
    [None, None, Multipliers.dw, None, None, None, Multipliers.dl, None, Multipliers.dl, None, None, None, Multipliers.dw, None, None],
    [Multipliers.dl, None, None, Multipliers.dw, None, None, None, Multipliers.dl, None, None, None, Multipliers.dw, None, None, Multipliers.dl],
    [None, None, None, None, Multipliers.dw, None, None, None, None, None, Multipliers.dw, None, None, None, None],
    [None, Multipliers.tl, None, None, None, Multipliers.tl, None, None, None, Multipliers.tl, None, None, None, Multipliers.tl, None],
    [None, None, Multipliers.dl, None, None, None, Multipliers.dl, None, Multipliers.dl, None, None, None, Multipliers.dl, None, None],
    [Multipliers.tw, None, None, Multipliers.dl, None, None, None, None, None, None, None, Multipliers.dl, None, None, Multipliers.tw],
    [None, None, Multipliers.dl, None, None, None, Multipliers.dl, None, Multipliers.dl, None, None, None, Multipliers.dl, None, None],
    [None, Multipliers.tl, None, None, None, Multipliers.tl, None, None, None, Multipliers.tl, None, None, None, Multipliers.tl, None],
    [None, None, None, None, Multipliers.dw, None, None, None, None, None, Multipliers.dw, None, None, None, None],
    [Multipliers.dl, None, None, Multipliers.dw, None, None, None, Multipliers.dl, None, None, None, Multipliers.dw, None, None, Multipliers.dl],
    [None, None, Multipliers.dw, None, None, None, Multipliers.dl, None, Multipliers.dl, None, None, None, Multipliers.dw, None, None],
    [None, Multipliers.dw, None, None, None, Multipliers.tl, None, None, None, Multipliers.tl, None, None, None, Multipliers.dw, None],
    [Multipliers.tw, None, None, Multipliers.dl, None, None, None, Multipliers.tw, None, None, None, Multipliers.dl, None, None, Multipliers.tw],
]


class TurnAction(TextChoices):
    play = "play"
    exchange = "exchange"
    pass_turn = "pass"
    forfeit = "forfeit"
