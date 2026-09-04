# Household Chores Manager

> **Everyone knows what’s next, who’s up, and that it’s fair.**  
> Web app for shared households (roommates / families / couples) — self-hosted, Docker Compose, Django 5.2 + HTMX.

**Spec:** `_docs/plan.md` → **Stack:** `_docs/stack-decision.md` (Django 5.2 + HTMX + Tailwind + PostgreSQL 16) → **Process:** `_docs/process.md`
> **Python:** 3.12 pinned in `.python-version`, **uv** manages venv + lock (`uv.lock`), no `pip`/`requirements.txt`

## Quick Start (30 seconds)

```bash
git clone https://github.com/code-hy/ai-native-developer-workflow.git
cd ai-native-developer-workflow
cp .env.example .env
# edit .env → DJANGO_SECRET_KEY (uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Option A — Docker (recommended, includes Postgres + Redis + Mailpit)
docker compose up --build
# web: http://localhost:8000 | mailpit: http://localhost:8025 | db host: localhost:5433 → container 5432

# Option B — Local without Docker (SQLite, no ports)
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser  # login with email
uv run python manage.py runserver        # http://127.0.0.1:8000
```

---

## Running

### 1. Running Locally (uv-only, no Docker)

Best for hacking on features. Uses SQLite by default so no Postgres needed.

```bash
# 1. env
cp .env.example .env
# For local SQLite, set in .env:
# DATABASE_URL=sqlite:///db.sqlite3
# Or leave empty — settings.py falls back to db.sqlite3

# 2. install (creates .venv from uv.lock, Python 3.12)
uv sync

# 3. DB
uv run python manage.py migrate
uv run python manage.py createsuperuser  # email + password (8+ chars)

# 4. run
uv run python manage.py runserver        # http://127.0.0.1:8000 → Dashboard
# http://127.0.0.1:8000/admin/           → Django admin (login with superuser email)
# http://127.0.0.1:8000/accounts/signup/ → signup flow
# http://127.0.0.1:8000/households/new/  → create household after signup

# 5. optional — Tailwind CSS watcher (if editing CSS)
uv run python manage.py tailwind:start   # in separate terminal

# 6. shell / one-offs
uv run python manage.py shell
uv run python manage.py createsuperuser
uv run python manage.py generate_due_instances  # recurrence job
uv run python manage.py send_digests            # email digest job (stub)
```

Stop: `Ctrl+C`. Deps update: `uv add <pkg>` → `uv sync` → commit `uv.lock`.

### 2. Running with Docker (production-like locally)

Includes `web` (Django+Gunicorn via `uv run`), `db` (Postgres 16), `redis` (queue), `mailpit` (email inbox).

```bash
cp .env.example .env
# edit: DJANGO_SECRET_KEY, DJANGO_DEBUG=True for local, keep defaults for DB

docker compose up --build
# web:     http://localhost:8000
# mailpit: http://localhost:8025  (SMTP 1025, catches all dev email)
# db:      localhost:5433 → container 5432 (5432 on host often allocated — compose now uses 5433)
# redis:   localhost:6379

# logs
docker compose logs -f web
docker compose logs -f db

# inside web container (uv-only)
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py createsuperuser
docker compose exec web uv run python manage.py shell
docker compose exec web uv run pytest -q

# stop
docker compose down        # keep data
docker compose down -v     # wipe pgdata (fresh DB)
```

**Port conflict (5432 already allocated)?** Already fixed — compose maps `5433:5432`. If you still see `Bind for 0.0.0.0:5432 failed`, run `docker compose down -v` once, or change `docker-compose.yml` `db.ports` to another free host port.

**First-run `uv sync` in Docker is slow?** Cold Docker `uv` cache builds 34 wheels (~2m on Windows mounts, `UV_LINK_MODE=copy` warning is harmless). Subsequent `up` is fast.

## Deployment

### 3. Deploying to Production (VPS — 10 min, $5)

**Target:** Hetzner CX11 / DigitalOcean / any Ubuntu 24.04 with Docker. Works on Fly.io/Render too (see below).

```bash
# on VPS
apt update && apt install -y docker.io docker-compose-plugin git
git clone https://github.com/code-hy/ai-native-developer-workflow.git
cd ai-native-developer-workflow
cp .env.example .env
nano .env
# set: DJANGO_SECRET_KEY=<generated>, DJANGO_DEBUG=False, DJANGO_ALLOWED_HOSTS=your.domain.com, EMAIL_HOST=smtp.resend.com etc.
# DATABASE_URL stays postgres://household:household@db:5432/household (internal)

docker compose up -d --build
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py createsuperuser
docker compose logs -f web  # check Starting at http://0.0.0.0:8000
```

**TLS:** Put `web:8000` behind Caddy/Nginx:

```nginx
# /etc/caddy/Caddyfile
your.domain.com {
    reverse_proxy localhost:8000
}
# caddy reload — auto TLS via Let's Encrypt
```

Or `flyctl`/`render` handle TLS.

**Env for prod (`.env` on VPS):**
```
DJANGO_SECRET_KEY=… # 50+ chars, never commit
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your.domain.com
DATABASE_URL=postgres://household:household@db:5432/household
REDIS_URL=redis://redis:6379/0
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=…
DEFAULT_FROM_EMAIL=noreply@your.domain.com
```

**Updates:**
```bash
git pull
docker compose up -d --build
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py collectstatic --noinput  # if needed
```

**Backup / Restore:**
```bash
# backup (cron daily)
docker compose exec db pg_dump -U household household | gzip > backup-$(date +%F).sql.gz

# restore to fresh
gunzip -c backup-2026-09-04.sql.gz | docker compose exec -T db psql -U household household

# also backup media volume: tar czf media-$(date +%F).tar.gz media/
```

### 4. Deploying to Fly.io / Render

- **Fly:** `fly launch --dockerfile Dockerfile --no-deploy` → `fly deploy` (uses `uv` image, `fly.toml` proxies 8000 → 80). Set secrets via `fly secrets set DJANGO_SECRET_KEY=…`.
- **Render:** New Web Service → Docker → `docker-compose.yml` → set env vars in dashboard → `render deploy`.

Both respect `uv.lock` and `.python-version`.

---

## Commands — uv-only (no pip)

| Purpose | Command |
|---|---|
| Install | `uv sync` |
| Dev server | `uv run python manage.py runserver` |
| Migrate | `uv run python manage.py migrate` |
| Make migrations | `uv run python manage.py makemigrations` |
| Tailwind build | `uv run python manage.py tailwind:build` |
| Shell | `uv run python manage.py shell` |
| Tests | `uv run pytest -q` |
| Coverage gate | `uv run pytest --cov --cov-fail-under=80` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy .` |
| E2E | `npx playwright test` |
| Docker up | `docker compose up --build` |
| Docker test | `docker compose exec web uv run pytest -q` |
| Docker shell | `docker compose exec web uv run python manage.py shell` |

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
