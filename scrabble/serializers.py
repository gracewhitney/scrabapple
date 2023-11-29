from django.core.exceptions import ValidationError
from rest_framework import serializers

from scrabble.constants import TurnAction


class TileMoveSerializer(serializers.Serializer):
    tile = serializers.CharField(max_length=2)  # Blank tiles played represented as e.g. '-A'
    x = serializers.IntegerField(min_value=0, max_value=14)
    y = serializers.IntegerField(min_value=0, max_value=14)

    def validate_tile(self, tile):
        if len(tile) > 1 and tile[0] != '-':
            raise ValidationError("Invalid tile: multiple letters")
        # TODO: remove first condition once blanks are set to a specific letter
        if not (tile[-1] == '-' or tile[-1].isalpha()):
            raise ValidationError("Invalid tile: not letter")
        return tile.upper()


class GameTurnSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=TurnAction.choices)
    played_tiles = serializers.ListField(child=TileMoveSerializer(), required=False, max_length=7)
    exchanged_tiles = serializers.ListField(child=serializers.CharField(max_length=1), required=False)
