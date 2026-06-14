from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("predict/<int:match_id>/", views.predict, name="predict"),
    path("squads/", views.squads, name="squads"),
    path("squads/<int:squad_id>/", views.squad_detail, name="squad_detail"),
    path("squads/<int:squad_id>/messages/", views.squad_messages, name="squad_messages"),
    path("wagers/<int:wager_id>/<str:action>/", views.wager_action, name="wager_action"),
]
