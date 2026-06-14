from django.contrib import admin

from .models import Match, Membership, Message, Prediction, Profile, Squad, Team, Wager


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("__str__", "stage", "group", "kickoff", "status", "home_score", "away_score")
    list_filter = ("stage", "status", "group")
    list_editable = ("status", "home_score", "away_score")


admin.site.register([Team, Prediction, Profile, Squad, Membership, Wager, Message])
