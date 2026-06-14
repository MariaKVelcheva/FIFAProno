# PRONO ROYALE ⚽

A friends-only World Cup 2026 prediction game built with Django.
Predict scores, climb your squad's scoreboard, and wager promises (never money).

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Django](https://img.shields.io/badge/Django-5.x-green)

---

## Features

- **Predict scores** for all 104 World Cup matches — locked automatically at kickoff
- **Scoring**: exact score = 3 pts · correct outcome = 1 pt · knockout matches ×2
- **Squads** — create a group, share the 6-character invite code with friends
- **Scoreboard** per squad with exact-score counter
- **Wagers** — challenge a squad mate to a promise (loser cooks dinner, etc.), no money involved
- **Locker-room chat** — simple message wall per squad, polls every 15 s

---

## Local setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/prono-royale.git
cd prono-royale

# Linux / macOS
python -m venv .venv && source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> If PowerShell blocks script execution: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows
```

Edit `.env` and fill in at minimum:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | ✅ | Generate with the command shown in `.env.example` |
| `DEBUG` | ✅ | `True` locally, `False` in production |
| `ALLOWED_HOSTS` | ✅ | `localhost,127.0.0.1` locally |
| `FOOTBALL_DATA_TOKEN` | ✅ | Free at [football-data.org](https://www.football-data.org/client/register) |
| `DATABASE_URL` | optional | Leave blank to use SQLite locally |

### 4. Run migrations and create a superuser

```bash
python manage.py makemigrations prono
python manage.py migrate
python manage.py createsuperuser
```

### 5. Pull match data

```bash
python manage.py sync_matches
```

Fetches all 104 WC fixtures and any finished results (rescores predictions automatically).
Free tier is 10 calls/min — this command makes exactly **1 call**. Re-run after each match day.

> No token yet? You can enter results manually in `/admin` (Match list is inline-editable).

### 6. Start the server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000`, sign up, create a squad, share the code.

---

## Scoring rules

Defined in `prono/scoring.py` — easy to adjust before the tournament and resync:

| Result | Points |
|---|---|
| Exact score | 3 |
| Correct outcome (W/D/L) | 1 |
| Wrong | 0 |
| Knockout stage multiplier | ×2 |

---

## Project structure

```
prono/
├── models.py       # Profile, Team, Match, Prediction, Squad, Membership, Wager, Message
├── scoring.py      # Pure scoring functions (isolated, easy to unit-test)
├── views.py
├── urls.py
├── forms.py
├── admin.py
├── signals.py      # Auto-creates Profile on User creation
├── management/
│   └── commands/
│       └── sync_matches.py   # The only file that talks to the API
├── templates/
│   ├── prono/
│   └── registration/
└── static/prono/
    └── style.css
config/
├── settings.py
├── urls.py
└── wsgi.py
```

---

## Deployment (Render / Railway)

For deployment, set in your platform's environment variables:

```
DEBUG=False
SECRET_KEY=<strong random key>
ALLOWED_HOSTS=yourapp.onrender.com
FOOTBALL_DATA_TOKEN=<your token>
DATABASE_URL=<postgres url from platform>
```

Add `gunicorn` and `psycopg2-binary` to `requirements.txt`, then use:
- **Build command**: `pip install -r requirements.txt && python manage.py migrate`
- **Start command**: `gunicorn config.wsgi`

---

## Tech stack

- [Django 5](https://djangoproject.com) — backend, ORM, auth
- [football-data.org](https://football-data.org) — free World Cup fixture & results API
- Vanilla JS — prediction inputs, chat polling
- SQLite (local) / PostgreSQL (production)

---

## License

MIT — use freely, but please don't run a real money betting operation with this. That's not what it's for.
