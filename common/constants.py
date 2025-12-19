from django.db.models import TextChoices

class NotificationType(TextChoices):
    new_game = "new_game"
    play = "play"
    game_over = "game_over"
