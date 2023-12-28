from django.urls import path

from scrabble import views

app_name = "scrabble"

urlpatterns = [
    path("new/", views.CreateGameView.as_view(), name="create_game"),
    path("play/<uuid:game_id>", views.GameView.as_view(), name="play_game"),
    path("play/<uuid:game_id>/post/", views.GameTurnView.as_view(), name="post_play"),
    path("play/<uuid:game_id>/score/", views.CalculateScoreView.as_view(), name="score_play"),
    path("info/<uuid:game_id>/turn", views.GameTurnIndexView.as_view(), name="get_game_turn"),
]