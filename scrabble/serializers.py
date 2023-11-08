from rest_framework import serializers

from scrabble.constants import TurnAction


class TileMoveSerializer(serializers.Serializer):
    tile = serializers.CharField(max_length=1)
    blank_letter = serializers.CharField(max_length=1, required=False)  # Replacement letter for blanks
    x = serializers.IntegerField(min_value=0, max_value=14)
    y = serializers.IntegerField(min_value=0, max_value=14)


class GameTurnSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=TurnAction.choices)
    played_tiles = serializers.ListField(child=TileMoveSerializer(), required=False, max_length=7)
    exchanged_tiles = serializers.ListField(child=serializers.CharField(max_length=1), required=False)
