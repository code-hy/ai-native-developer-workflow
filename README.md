# Household Chores Manager

> **Everyone knows what’s next, who’s up, and that it’s fair.**  
> Web app for shared households (roommates / families / couples) — self-hosted, Docker Compose, Django + HTMX.

**Spec:** `_docs/plan.md` → **Stack:** `_docs/stack-decision.md` (Django 5.2 + HTMX + Tailwind + PostgreSQL 16) → **Process:** `_docs/process.md`
> **Python:** 3.12 pinned in `.python-version`, **uv** manages venv + lock (`uv.lock`), no `pip`/`requirements.txt`

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# edit DJANGO_SECRET_KEY (generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
docker compose up --build
# web: http://localhost:8000
# mailpit: http://localhost:8025  (email inbox)
# db: 5432, redis: 6379

docker compose exec web uv run python manage.py createsuperuser
```

### Local (without Docker) — uv-only

```bash
uv sync  # creates .venv from uv.lock (Python 3.12)
cp .env.example .env
# set DATABASE_URL=sqlite:///db.sqlite3 for quick local without Postgres
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver  # http://127.0.0.1:8000

# in another terminal if editing CSS:
uv run python manage.py tailwind:start
```

## Commands — uv-only (no pip)

| Purpose | Command |
|---|---|
| Install | `uv sync` |
| Dev server | `uv run python manage.py runserver` |
| Migrate | `uv run python manage.py migrate` |
| Make migrations | `uv run python manage.py makemigrations` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy .` |
| Unit tests | `uv run pytest -q` |
| Coverage gate | `uv run pytest --cov --cov-fail-under=80` |
| E2E | `npx playwright test` |
| Shell | `uv run python manage.py shell` |

## Project Structure

```
household/ (Django apps, created on scaffold)
├── core/           # settings, urls, wsgi, rrule utils, fairness service
├── accounts/       # User (email login)
├── households/     # Household, Membership, Invite
├── chores/         # Chore, recurrence, assignment strategies
├── groceries/      # GroceryItem
├── bills/          # Bill
├── maintenance/    # MaintenanceTask
├── activity/       # Activity log
├── templates/base.html
├── static/         # Tailwind input + built css, htmx, alpine
└── tests/          # e2e J1/J2/J3
_docs/
├── plan.md, stack-decision.md, process.md, task-template.md
├── design-system.md, testing-guidelines.md
└── team/pm.md, team/software-engineer.md, team/qa-engineer.md
```

## Documentation

- **Plan:** `_docs/plan.md` — vision, personas, full home ops scope, data model
- **Stack ADR:** `_docs/stack-decision.md` — Django vs Next.js vs SvelteKit
- **Process:** `_docs/process.md` — issue lifecycle, loop goals, branch/commit rules
- **Design:** `_docs/design-system.md` — tokens, HTMX patterns
- **Testing:** `_docs/testing-guidelines.md` — pytest/Playwright gates

## Self-Host Guide (10 minutes, $5 VPS)

1. Provision Ubuntu 24.04 (Hetzner CX11 / Fly / Render)
2. Install Docker + Compose: `apt update && apt install docker.io docker-compose-plugin`
3. Clone + `cp .env.example .env` + set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=your.domain`
4. `docker compose up -d --build` + `docker compose exec web python manage.py createsuperuser`
5. Put `web:8000` behind Nginx/Caddy with TLS (or `flyctl` handles TLS)
6. Backup: `docker compose exec db pg_dump -U household household | gzip > backup-$(date +%F).sql.gz`
7. Restore: `gunzip -c backup.sql.gz | docker compose exec -T db psql -U household household`

Email: Mailpit in dev; in prod set `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_PASSWORD` for your SMTP (e.g., Resend, Brevo, Postfix).

## Contributing (AI-native workflow)

1. No code without a groomed issue (`needs-grooming` → `groomed` by PM)
2. Branch `feat/issue-#N-slug` from `main`
3. Commit per AC: `feat(#12): add rotating assignment — AC1`
4. Push + open PR `Closes #N` + paste `pytest`/`ruff`/`mypy` logs
5. QA posts `PASS`/`FAIL` with logs; only QA closes issues

See `AGENTS.md` / `CLAUDE.md` for harness goals:
`/goal groom all issues`, `/goal implement issue #N`, `/goal qa issue #N`, `/goal sync tasks`

## License

TBD — private self-hosted use.
