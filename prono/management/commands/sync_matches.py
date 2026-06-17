import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from prono.models import Match, Team
from prono.scoring import score_match

URL = "https://api.football-data.org/v4/competitions/WC/matches"


class Command(BaseCommand):
    help = "Sync World Cup matches from football-data.org"

    def handle(self, *args, **options):
        token = settings.FOOTBALL_DATA_TOKEN
        if not token:
            raise CommandError("Set FOOTBALL_DATA_TOKEN in your .env (free at football-data.org)")

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        resp = session.get(URL, headers={"X-Auth-Token": token}, timeout=30)
        resp.raise_for_status()

        resp.raise_for_status()
        data = resp.json()

        created, updated, scored = 0, 0, 0
        for m in data.get("matches", []):
            home = self._team(m.get("homeTeam"))
            away = self._team(m.get("awayTeam"))
            score = m.get("score", {}).get("fullTime", {})
            match, was_created = Match.objects.update_or_create(
                fd_id=m["id"],
                defaults={
                    "stage": m.get("stage", Match.GROUP_STAGE),
                    "group": m.get("group") or "",
                    "kickoff": parse_datetime(m["utcDate"]),
                    "status": m.get("status", "SCHEDULED"),
                    "home_team": home,
                    "away_team": away,
                    "home_score": score.get("home"),
                    "away_score": score.get("away"),
                },
            )
            created += was_created
            updated += not was_created
            if match.is_finished:
                score_match(match)
                scored += 1

        self.stdout.write(
            self.style.SUCCESS(f"{created} created, {updated} updated, {scored} finished matches rescored.")
        )

    @staticmethod
    def _team(team_data):
        if not team_data or not team_data.get("id"):
            return None  # TBD knockout slot
        team, _ = Team.objects.update_or_create(
            fd_id=team_data["id"],
            defaults={
                "name": team_data.get("name") or "TBD",
                "tla": team_data.get("tla") or "",
                "crest": team_data.get("crest") or "",
            },
        )
        return team
