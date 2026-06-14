import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

AVATARS = ["⚽", "🦁", "🦅", "🐺", "🔥", "⚡", "🧤", "👑", "🚀", "🐙", "🥶", "🤖"]


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.CharField(max_length=8, default="⚽")

    def __str__(self):
        return f"{self.avatar} {self.user.username}"


class Team(models.Model):
    fd_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    tla = models.CharField(max_length=5, blank=True)
    crest = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    GROUP_STAGE = "GROUP_STAGE"

    fd_id = models.IntegerField(unique=True)
    stage = models.CharField(max_length=30, default=GROUP_STAGE)
    group = models.CharField(max_length=20, blank=True)
    kickoff = models.DateTimeField()
    status = models.CharField(max_length=20, default="SCHEDULED")
    home_team = models.ForeignKey(
        Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="home_matches"
    )
    away_team = models.ForeignKey(
        Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="away_matches"
    )
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["kickoff"]
        verbose_name_plural = "matches"

    def __str__(self):
        h = self.home_team.name if self.home_team else "TBD"
        a = self.away_team.name if self.away_team else "TBD"
        return f"{h} vs {a}"

    @property
    def is_open(self):
        """Predictions allowed until kickoff."""
        return self.kickoff > timezone.now() and self.status in ("SCHEDULED", "TIMED")

    @property
    def is_finished(self):
        return self.status == "FINISHED"

    @property
    def is_knockout(self):
        return self.stage != self.GROUP_STAGE


class Prediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    home_score = models.PositiveSmallIntegerField()
    away_score = models.PositiveSmallIntegerField()
    points = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "match")

    def __str__(self):
        return f"{self.user.username}: {self.home_score}-{self.away_score} ({self.match})"


def make_squad_code():
    return secrets.token_urlsafe(4)[:6].upper().replace("-", "X").replace("_", "Z")


class Squad(models.Model):
    name = models.CharField(max_length=60)
    code = models.CharField(max_length=10, unique=True, default=make_squad_code)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="squads_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    squad = models.ForeignKey(Squad, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "squad")


class Wager(models.Model):
    PROPOSED, ACCEPTED, SETTLED, DECLINED = "P", "A", "S", "D"
    STATUS_CHOICES = [
        (PROPOSED, "Proposed"),
        (ACCEPTED, "Accepted"),
        (SETTLED, "Settled"),
        (DECLINED, "Declined"),
    ]

    squad = models.ForeignKey(Squad, on_delete=models.CASCADE, related_name="wagers")
    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wagers_made"
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wagers_received"
    )
    match = models.ForeignKey(Match, null=True, blank=True, on_delete=models.SET_NULL)
    stake = models.CharField(max_length=200, help_text="A promise, never money. e.g. 'Loser cooks raclette'")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PROPOSED)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="wagers_won"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.challenger} vs {self.opponent}: {self.stake}"


class Message(models.Model):
    squad = models.ForeignKey(Squad, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
