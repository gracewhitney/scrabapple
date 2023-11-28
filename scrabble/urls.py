from django.urls import path

from scrabble import views

app_name = "scrabble"

urlpatterns = [
    path("new/", views.CreateGameView.as_view(), name="create_game"),
    path("play/<uuid:game_id>", views.ScrabbleView.as_view(), name="play_scrabble"),
    path("play/<uuid:game_id>/post/", views.ScrabbleTurnView.as_view(), name="post_scrabble_play"),
    path("play/<uuid:game_id>/score/", views.ScrabbleCalculateScoreView.as_view(), name="score_play"),
]