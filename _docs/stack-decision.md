# Stack Decision — Household Chores Manager
**Date:** 2026-09-04  
**Status:** Proposed → **RECOMMENDED: Option A (Python)**  
**Deciders:** Plan `_docs/plan.md` constraints + User review preference: **Python (Django/FastAPI)**  
**Context:** Web app only · Simple & self-hosted (Docker, email/password, private data) · Full home ops (chores + groceries + bills + maintenance) · Flexible households (roommates/family/couple)

---

## 1. Decision Outcome

> **Select Option A — Python: Django 5 + HTMX + Alpine.js + Tailwind CSS + PostgreSQL 16 + Django Auth + WhiteNoise/Gunicorn + Docker Compose**

**Primary runner-up:** Option B (Next.js) — technically excellent for this scope but suboptimal for *your* review capability (Python). Keep as fallback if team review shifts to TypeScript.

**ADR in one line:** We optimize for *reviewability* and *self-host simplicity* over frontend hype; Django’s batteries-included admin, ORM, and auth let a Python reviewer ship the full home ops spec fastest with least custom plumbing.

---

## 2. Options Evaluated

### Option A — Python / Django + HTMX (RECOMMENDED)

**Stack:**

```
Language: Python 3.12
Framework: Django 5.1 (MTV, Apps)
Frontend interactivity: HTMX 1.9 + Alpine.js 3 (sprinkles) + _hyperscript minimal
Styling: Tailwind CSS 3.4 (via django-tailwind or standalone CLI) + django-widget-tweaks
DB: PostgreSQL 16 + psycopg 3
ORM: Django ORM
Auth: Django Auth (email/password) + django-allauth optional later, bcrypt, session + CSRF, password reset via email token
Forms/Validation: Django Forms + Pydantic for API boundaries (if DRF added later)
Recurrence: python-dateutil + dateutil.rrule (RFC5545) — same engine for chores/bills/maintenance
Background jobs: Django Q / Celery + Beat OR APScheduler / django-crontab for digest + overdue (start with django-q2 or celery+redis; fallback to cron)
Email: Django Email backend → SMTP (Mailpit in dev, local postfix/Resend fallback in prod), django.core.mail
File uploads (photo proof): Django Media + local volume (/media) → easy S3/MinIO swap via django-storages
Testing: pytest + pytest-django + factory-boy + Playwright (e2e for J1/J2/J3)
Lint/Format: ruff + mypy (strict) + djlint
Deploy: Docker (python:3.12-slim) + Gunicorn + WhiteNoise + Nginx (optional) + Docker Compose (web, db, redis, mailpit) + .env
Admin: Django Admin (free household/chore/member audit UI)
```

**Project layout:**
```
household/
├── households/       # Household, Membership, Invite
├── chores/           # Chore, Recurrence, Assignment strategies
├── groceries/        # GroceryItem
├── bills/            # Bill
├── maintenance/      # MaintenanceTask
├── activity/         # Activity log (signals)
├── accounts/         # Custom User (email login)
├── core/             # settings, urls, fairness service, rrule utils
├── templates/        # base.html, chores/, dashboard/
├── static/           # tailwind input, htmx, alpine
├── tests/
├── manage.py
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

**Why it fits *your* constraints:**

| Criterion | Score | Rationale |
|---|---|---|
| **Reviewability (Python)** | ★★★★★ | You can review Django idioms, ORM, signals, class-based views confidently; PRs stay in Python |
| **Self-host simplicity** | ★★★★★ | `docker compose up` → web+db+redis+mailpit; single `python manage.py migrate`; Gunicorn+WhiteNoise no Node build needed (Tailwind CLI is optional, can pre-build CSS). Backups = pg_dump |
| **Auth simplicity** | ★★★★★ | `AbstractUser` with email login, password hash (PBKDF2/argon2), logout everywhere, reset token — ~0 custom crypto vs NextAuth config |
| **Recurrence & Fairness** | ★★★★☆ | `dateutil.rrule` is Python-native, well-tested for DST/household timezone; fairness = ORM `annotate(Sum('effort'))`; shared util across 3 models |
| **Velocity for Full Home Ops** | ★★★★★ | 4 apps scaffolded in minutes; Django Admin gives you instant household/member/chore editor for QA without building separate UI |
| **Performance (web-only)** | ★★★★☆ | Server-rendered HTML + HTMX → ~30KB JS (alpine+htmx) vs 150KB+ Next.js bundle; Lighthouse ≥95 trivially; <1.5s first paint on 3G |
| **Testability** | ★★★★☆ | `pytest-django` + `TestClient` for views, `factory-boy` for data, Playwright for J1-J3 — coverage gate 80% straightforward |
| **Hiring / Harness friendliness** | ★★★★☆ | Loop / Graph agents (PM/SWE/QA) get clear app boundaries; tasks map 1:1 to Django apps; `/_docs/team/*.md` easily ported |

**Cons to own:**
- Less SPA “snappiness” than Next.js (but HTMX + Alpine covers modal/drawer/calendar strip well; not a real con for chore app which is CRUD-heavy, not real-time).
- Tailwind build step slight friction (mitigate: commit compiled CSS or run `tailwindcss -w` in Docker).
- If you later want React Native, you’d add DRF API layer (Django Rest Framework) — Django can grow there, but Next.js would have head start for unified JS.

**Mitigations:** Use `django-htmx` middleware, `django-tailwind`, `whitenoise` so no Node in prod image; add `DRF` only when V2 mobile needs it; document Tailwind build in `AGENTS.md`.

---

### Option B — TypeScript / Next.js 15 (Runner-up, Best Docs & Ecosystem)

**Stack:**
```
Next.js 15 (App Router) + React 19 + TypeScript 5.6
Tailwind 3.4 + shadcn/ui + lucide-react + Framer Motion (optional)
Prisma 5 + PostgreSQL 16
Auth: Auth.js (NextAuth) credentials provider + bcrypt + JWT httpOnly + CSRF
Validation: Zod + react-hook-form
Recurrence: rrule.js
Email: Resend + react-email or Nodemailer + Mailpit
Background: Vercel Cron / node-cron / BullMQ + Redis (for digests)
Testing: Vitest + Playwright + Testing Library
Deploy: Docker (node:20-slim + standalone output) + Compose (app, db, mailpit)
```

**Pros:**
- Best docs, largest community, Vercel one-click deploy alternative to self-host; shadcn/ui speeds dashboard/kanban; Prisma migrations ergonomic.
- SPA feels snappy; easy PWA + offline later with Workbox.
- `rrule.js` mirrors Python `dateutil.rrule` well.

**Cons for YOU:**
- **Review burden:** Requires reviewing TS, React hooks, Prisma, Next.js caching/RSC subtleties — mismatch with Python comfort; higher risk of missing subtle bugs in PRs.
- Heavier JS bundle (100–200KB), `pnpm build` step, Node CVEs, and larger Docker image.
- Auth.js credentials setup is config-heavy vs Django’s one-liner.

**When to pick:** If team pivots to TypeScript or needs unified JS for future native app; keep as documented fallback.

---

### Option C — Lightweight / SvelteKit + SQLite (Minimal VPS)

**Stack:**
```
SvelteKit 2 + Svelte 4 + TypeScript
Tailwind + Skeleton UI
Drizzle ORM + SQLite (Litestream for backup) or Turso
Auth: Lucia Auth 3 (now Arctic) + email/password
Recurrence: rrule.js
Email: Nodemailer + Mailpit
Testing: Vitest + Playwright
Deploy: Docker (node:20-alpine) + single file DB → fits $3.50 VPS, Litestream → S3 backup
```

**Pros:**
- Smallest bundle (~20KB JS), fastest cold start, simplest backup (single file), cheap hosting; great for self-hosters who hate Postgres.
- Svelte’s reactivity super clean for fairness charts.

**Cons:**
- SQLite concurrency limits under household writes (Groceries concurrent edits) — possible `busy` errors; need WAL tuning.
- Smallest hiring pool, fewer Django/Next.js-caliber agents/harness examples; Lucia is ESM-only learning curve.
- Fewer batteries (no admin) → build more UI for household management.

**When to pick:** If constraint tightens to “run on Raspberry Pi / 512MB VPS with zero Postgres ops”; otherwise premature optimization.

---

## 3. Comparison Matrix

| Dimension | Weight | A: Django+HTMX | B: Next.js+Prisma | C: SvelteKit+SQLite |
|---|---|---|---|---|
| Reviewability (you = Python) | 30% | **5** | 2 | 2 |
| Self-host simplicity (`compose up`) | 20% | **5** | 4 | 5 (smallest) |
| Full home ops velocity (4 apps) | 15% | **5** | 4 | 3 |
| Recurrence correctness (DST) | 10% | **5** (dateutil) | 4 (rrule.js) | 4 |
| Web-only perf / Lighthouse | 10% | **5** (SSR+30KB) | 4 | 5 |
| Testability (80% gate) | 10% | 4 | 4 | 4 |
| Future mobile/API path | 5% | 3 (needs DRF) | **5** | 4 |
| **Weighted total** | 100% | **4.75** | 3.15 | 3.45 |

**Note:** If reviewer were TypeScript-native, B would win at ~4.6. Weighting explicitly favors your stated Python comfort — which is the correct Spec-Driven principle (optimize for reviewer capability).

---

## 4. Recommendation Details — Option A Implementation Notes

### 4.1 Auth (F-01, F-02)
- Custom `User` (`AbstractUser`, `USERNAME_FIELD='email'`, `REQUIRED_FIELDS=[]`), `email` unique case-insensitive.
- Login view rate-limited (`django-ratelimit` 5/min), session cookie `HttpOnly`, `Secure`, `SameSite=Lax`, CSRF via `{% csrf_token %}`.
- Invite: `Household.invite_code` (8-char nanoID) + `Invite(email, token, expires_at 7d)`; link `/invite/<token>` → set password.

### 4.2 Assignment Strategies (F-04)
```
strategy = Assigned(assignee_id) | Pool(assignee=None) | Rotating(order=[user_ids], pointer_index)
# Rotating: on completion, advance pointer OR effort-balanced: pick min(Sum(effort) last 30d)
```
Service `chores/services/assignment.py` pure Python → unit testable.

### 4.3 Recurrence Service (F-03, F-09, F-10, F-11)
- `RecurrenceRule` model stores `rrule_str` (RFC5545) + `dtstart` (household timezone). Util `core/rrule.py` wraps `rrulestr` with DST-safe `zoneinfo`.
- Cron job `manage.py generate_due_instances` runs hourly (or Beat beat every 15m) → generates next `ChoreInstance`/`Bill` when `nextDueAt < now+7d`.
- Indexes: `Chore(household_id, status, due_at)` already in plan.

### 4.4 Fairness (F-06)
- `Activity` via `post_save` signals on `Chore.completed_at`; materialized via ORM query `Chore.objects.filter(household, completed_at__range).values('assignee').annotate(points=Sum('effort'))`.
- Chart: Chart.js or HTMX + partial + Tailwind bars (no heavy React chart).

### 4.5 Email & Jobs (F-11)
- Start simple: `django.core.mail.send_mail` + console backend in dev; `django-q2` or `celery` + `redis` for digest; fallback to `cron` calling `manage.py send_digests` at 08:00 per household timezone. Document SMTP env in `.env.example`.

### 4.6 Photo Proof (Open Q)
- V1: local `MEDIA_ROOT` volume; model `Chore.proof = ImageField(upload_to='proofs/%Y/%m/')`; limit 5MB, validate MIME. Swap to `django-storages[s3]` + MinIO when needed — interface stays `proof.url`.

### 4.7 HTMX Patterns (no SPA)
- List filtering via `hx-get` + `hx-push-url` to `?assignee=me&status=overdue` partial.
- Modals: `hx-get` → drawer HTML, `Alpine` for local state (effort slider).
- Dashboard fairness bar: server-rendered `<div class="bar" style="width: {{ pct }}%">` — no JS chart required.

### 4.8 Docker & Compose (Self-host <10 min)
```yaml
# docker-compose.yml
services:
  web: { build: ., command: gunicorn core.wsgi:application --bind 0.0.0.0:8000, env_file: .env, volumes: [media:/app/media], depends_on: [db, redis] }
  db: { image: postgres:16-alpine, volumes: [pgdata:/var/lib/postgresql/data], env_file: .env }
  redis: { image: redis:7-alpine }
  mailpit: { image: axllent/mailpit, ports: ["8025:8025", "1025:1025"] }
volumes: { pgdata:, media: }
```
- `Dockerfile` 2-stage: builder (collectstatic + tailwind) → runtime `python:3.12-slim`.
- `.env.example` documents `SECRET_KEY, DATABASE_URL, REDIS_URL, EMAIL_HOST, EMAIL_PORT, ALLOWED_HOSTS`.
- Backup: `docker compose exec db pg_dump -U household | gzip > backup.sql.gz`; restore docs in `README`.

### 4.9 Testing & Quality Gates
- `pytest -cov` ≥80% for `chores/services/`, `core/rrule.py`, `activity`.
- Playwright 3 journeys: J1 flatshare onboard, J2 family approval, J3 couple balance — assert DOM + email outbox (`mail.outbox` / Mailpit API).
- CI: GitHub Actions `ruff check + mypy + pytest + playwright + docker build`.

---

## 5. Deferred Decisions (ADR Follow-ups)

- [ ] VPS target: default to **Hetzner CX11 / $5 + Ubuntu 24.04 + Docker** (Render supports compose; Fly.io needs `fly.toml` — Hetzner keeps pure compose). Confirm after scaffolding.
- [ ] Background runner: start with **`django-q2 + Redis`** (lighter than Celery); swap to Celery if beat complexity grows.
- [ ] Tailwind integration: `django-tailwind` vs standalone CLI — benchmark in scaffolding issue #1.

---

## 6. What This Unblocks

1. **Scaffold issue #1** can now create Django project with this stack — no ambiguity.
2. **`_docs/tasks.md`** generation may reference `app: households/chores/groceries/bills/maintenance` directly.
3. **`AGENTS.md`** commands become `python manage.py …` (`uv` or `pip`, `ruff`, `pytest`, `playwright`).
4. QA can prepare Django Admin checklists and `mailpit` assertions.

---

## 7. Approval & Next Steps

- [ ] You: **Approve Option A** (or pick B/C) — reply “approve A” or “choose B/C”
- [ ] On approval, scaffold PR creates:
  - `AGENTS.md` (and `CLAUDE.md` symlink) with `uv run` / `pip` commands
  - `_docs/process.md`, `_docs/task-template.md`, `_docs/team/*.md`
  - `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`
  - Django project skeleton + Tailwind + HTMX + tests harness
- [ ] Then run backlog generation: `_docs/tasks.md` → `gh issue create` (14 issues) → `/goal groom all issues` loop

*If you prefer FastAPI over Django (also Python): we can pivot to FastAPI + Jinja + HTMX + SQLModel — similar HTMX pattern but you lose Admin; say “prefer FastAPI” and we’ll rewrite this ADR accordingly.*

---

**References:** `_docs/plan.md` §9 (Stack Selection), §6 NFRs, §7 Data Model, §10 Workflow.
