from django.urls import path

from scrabble import views

app_name = "scrabble"

urlpatterns = [
    path("new/", views.CreateGameView.as_view(), name="create_game"),
    path("play/<uuid:game_id>", views.ScrabbleView.as_view(), name="play_scrabble"),
]