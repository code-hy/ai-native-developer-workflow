# AGENTS — Household Chores Manager

> **Read first:** `_docs/plan.md` (vision + spec) → `_docs/process.md` (workflow) → `_docs/stack-decision.md` (Django+HTMX)
> **Stack:** Django 5.1 + HTMX + Alpine.js + Tailwind CSS + PostgreSQL 16 + django-q2/Redis + Gunicorn + Docker Compose
> **Source of truth:** GitHub Issues (synced from `_docs/tasks.md`)

## Quick Start

```bash
# 1. env
cp .env.example .env
# edit SECRET_KEY, DATABASE_URL, etc.

# 2. run (Docker — recommended)
docker compose up --build
# web: http://localhost:8000, mailpit: http://localhost:8025, db:5432, redis:6379

# 3. run (local, no Docker)
uv sync              # or pip install -r requirements.txt
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
uv run python manage.py tailwind:start  # in separate terminal if editing CSS

# 4. test / lint
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest -q                    # unit + integration, --cov for coverage
uv run pytest --cov --cov-fail-under=80
npx playwright test                  # e2e for J1/J2/J3
```

## Commands (harness expects these)

| Purpose | Command |
|---|---|
| Install | `uv sync` or `pip install -r requirements.txt` |
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
| Docker test | `docker compose exec web pytest -q` |

## Top-Level Rules

1. **No code without a groomed issue.** Every PR must reference `Closes #N` where issue has Goal/AC/Constraints/Out-of-scope.
2. **Read context docs every session:** `AGENTS.md` + `plan.md` + `process.md` are mandatory. Load domain docs dynamically:
   - `label:ui` → `_docs/design-system.md`
   - `label:testing` → `_docs/testing-guidelines.md`
3. **Roles:**
   - PM grooms issues, sets AC, labels, never writes code.
   - SWE implements against AC, writes unit tests, commits per AC, never closes issue.
   - QA independently verifies, posts `PASS`/`FAIL` with logs, only QA closes.
4. **Commit convention:** `feat(#12): add rotating assignment — AC1, AC2` or `fix(#8): ...`
5. **Branches:** `feat/issue-#N-slug` from `main`; `main` protected, PR requires QA PASS comment.
6. **Continuous feedback:** If you correct a recurring mistake, update the relevant `_docs/*.md` in the same PR.
7. **Checkable stop conditions only:** `pytest` exit 0, `gh issue view` shows AC, not “cleaner code”.
8. **HTMX pattern:** Server-rendered HTML + `hx-get`/`hx-post` + Alpine sprinkles; do not introduce React/Vue without ADR.

## Project Layout

```
household/ (to be created on scaffold issue #1)
├── households/, chores/, groceries/, bills/, maintenance/, activity/, accounts/, core/
├── templates/base.html, static/, tests/
_docs/
├── plan.md, stack-decision.md, process.md, task-template.md
├── design-system.md, testing-guidelines.md
└── team/pm.md, team/software-engineer.md, team/qa-engineer.md
```

## Loop Goals (harness)

```
/goal groom all issues   → every open issue has Goal/AC/Constraints/Out-of-scope, no needs-grooming
/goal implement issue #N → code+tests committed, pytest passes for that module, AC checklist commented
/goal qa issue #N        → QA posts PASS (all AC verified) or FAIL with logs
/goal sync tasks         → gh issue list count == _docs/tasks.md count
```

## Decisions

- Stack ADR: `_docs/stack-decision.md` (Django+HTMX recommended, Next.js fallback, SvelteKit minimal)
- Household types: `roommates|family|couple|custom`, roles `admin|member|parent|child`
- Timezone: per-household, store UTC, recurrence with `dateutil.rrule` + `zoneinfo`
- Auth: email/password + session cookie HttpOnly/Secure/SameSite=Lax + CSRF + rate limit 5/min
- Uploads: `MEDIA_ROOT` volume locally, swap to `django-storages[s3]` later
- Email: console in dev, Mailpit in Docker, SMTP/Resend in prod

## References

- Plan: `_docs/plan.md` §10 (AI-native workflow)
- Process: `_docs/process.md`
- Team personas: `_docs/team/*.md`
- Design: `_docs/design-system.md`
- Testing: `_docs/testing-guidelines.md`
