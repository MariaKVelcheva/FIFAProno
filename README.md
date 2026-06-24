# FIFA World Cupcake 🧁

A friends-only World Cup 2026 prediction game built with Django.
Predict scores, climb your squad's cake stand, and wager promises (never money).

![Python](https://img.shields.io/badge/Python-3.12.4-blue) ![Django](https://img.shields.io/badge/Django-5.x-green)

---

## Features

- **Predict scores** for all 104 World Cup matches — locked automatically at kickoff
- **Quick-predict gallery** — on login, a modal surfaces all unrated upcoming matches one by one so you never miss a prediction before kickoff
- **Scoring**: exact score = 3 pts · correct outcome = 1 pt · knockout matches ×2 · won wager = 10 pts
- **Squads / Kitchen brigades** — create a group, share the 6-character invite code with friends (click to copy)
- **Cake stand scoreboard** per squad — top 5 on tiered display, rest in the "also baking" list
- **Bake-offs** — challenge a squad mate to a promise (loser cooks dinner, etc.), no money involved; settled wagers are claimable by either party
- **Kitchen chat** — message wall per squad, polls every 15s with toast notifications and unread badge across all your squads
- **Player profiles** — visit any squad mate's profile to see their past predictions, points total, and shared brigades
- **Compare cakes** — side-by-side prediction comparison between any two players in a shared squad, including bake-off history
- **Cupcake mascot avatars** — pick your dessert at signup; your avatar appears throughout the app including on the scoreboard and as a section divider on the dashboard
- Browse matches and see results without an account — sign up only required to predict
- **Mosaic card layout** — match cards arranged in a 1-2-3 pyramid pattern with organic tilts and padding variation
---

## Local setup

### 1. Clone and create a virtual environment

Clone the repo and navigate into it:

    git clone https://github.com/MariaKVelcheva/FIFAProno.git
    cd worldcup-prono

Linux / macOS:

    python -m venv .venv && source .venv/bin/activate

Windows (PowerShell):

    python -m venv .venv
    .venv\Scripts\Activate.ps1

If PowerShell blocks script execution: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. Install dependencies

    pip install -r requirements.txt

### 3. Configure environment

Linux/macOS:

    cp .env.example .env

Windows:

    copy .env.example .env

Edit `.env` and fill in at minimum:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | ✅ | Generate with the command shown in `.env.example` |
| `DEBUG` | ✅ | `True` locally, `False` in production |
| `ALLOWED_HOSTS` | ✅ | `localhost,127.0.0.1` locally |
| `FOOTBALL_DATA_TOKEN` | ✅ | Free at football-data.org/client/register |
| `DATABASE_URL` | optional | Leave blank to use SQLite locally; Postgres URL in production |

### 4. Run migrations and create a superuser

    python manage.py makemigrations prono
    python manage.py migrate
    python manage.py createsuperuser

### 5. Pull match data

    python manage.py sync_matches

Fetches all 104 WC fixtures and any finished results, rescores predictions automatically.
Free tier allows 10 calls/min — this command makes exactly 1 call. Re-run after each match day.

No token yet? Results can be entered manually in /admin (Match list is inline-editable).

### 6. Start the server

    python manage.py runserver

Open http://127.0.0.1:8000, sign up, create a squad, share the code.

---

## Scoring rules

Defined in prono/scoring.py — easy to adjust and resync:

| Result | Points |
|---|---|
| Exact score | 3 |
| Correct outcome (W/D/L) | 1 |
| Wrong | 0 |
| Knockout stage multiplier | ×2 |
| Won a bake-off wager | +10 |

---

## Project structure

    prono/
    ├── models.py         # Profile, Team, Match, Prediction, Squad, Membership, Wager, Message
    ├── scoring.py        # Pure scoring functions (isolated, easy to unit-test)
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── admin.py
    ├── signals.py        # Auto-creates Profile on User creation
    ├── management/
    │   └── commands/
    │       └── sync_matches.py   # The only file that talks to the API
    ├── templates/
    │   ├── prono/
    │   └── registration/
    └── static/prono/
        ├── style.css
        └── images/
            ├── cupcake.png       # Hero illustration
            └── wrapper.png       # Match card decoration
    config/
    ├── settings.py
    ├── urls.py
    └── wsgi.py
    render.yaml           # Render blueprint (web service + Postgres)
    runtime.txt           # Python 3.12.4

---

## Deployment (Render)

The repo includes a render.yaml blueprint — connect your GitHub repo on Render via
New -> Blueprint and it will create the web service and PostgreSQL database automatically.

After deploy, add FOOTBALL_DATA_TOKEN manually in the service's Environment tab, then run
the following via Render's Shell tab to populate match data:

    python manage.py sync_matches

Environment variables set automatically by the blueprint:

| Variable | How set |
|---|---|
| `SECRET_KEY` | Auto-generated by Render |
| `DATABASE_URL` | Injected from the Postgres instance |
| `DEBUG` | False |
| `ALLOWED_HOSTS` | world-cupcake.onrender.com |

Free tier note: the web service spins down after 15 minutes of inactivity and takes ~30 seconds
to wake on the next request. Fine for active use during the tournament.

---

## Tech stack

- Django 5 — backend, ORM, auth — https://djangoproject.com
- football-data.org — free World Cup fixture and results API
- Vanilla JS — prediction inputs, chat polling, toast notifications
- WhiteNoise — static file serving in production
- SQLite (local) / PostgreSQL (production)

---
## A note on authorship

Designed and directed by a human. Baked alongside Claude (Anthropic).
The frosting choices were entirely mine.

## License

MIT — use freely, but please don't run a real money betting operation with this. That's not what it's for.