from django.urls import path

from scrabble import views

app_name = "scrabble"

urlpatterns = [
    path("new/", views.CreateGameView.as_view(), name="create_game"),
    path("play/<uuid:game_id>", views.GameView.as_view(), name="play_game"),
    path("play/<uuid:game_id>/post/", views.GameTurnView.as_view(), name="post_play"),
    path("play/<uuid:game_id>/score/", views.CalculateScoreView.as_view(), name="score_play"),
    path("play/<uuid:game_id>/update_rack/", views.UpdateRackView.as_view(), name="update_rack"),
    path("play/<uuid:game_id>/undo/", views.UndoTurnView.as_view(), name="undo_turn"),
    path("info/<uuid:game_id>/turn", views.GameTurnIndexView.as_view(), name="get_game_turn"),
    path("play/<uuid:game_id>/notifications/", views.ToggleNotificationsView.as_view(), name="update_game_settings"),
    path("play/<uuid:game_id>/options/", views.EditGameOptionsView.as_view(), name="edit_game_options"),
    path("play/<uuid:game_id>/archive/", views.ArchiveGameView.as_view(), name="archive_game")
]