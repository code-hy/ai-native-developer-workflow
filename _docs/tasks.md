# Tasks — Household Chores Manager

> **Source of truth:** GitHub Issues (this file is a generated view).  
> **Template:** `_docs/task-template.md` — every issue uses Goal / AC / Constraints / Out-of-Scope.  
> **Stack:** `_docs/stack-decision.md` (Django 5.1 + HTMX). **Plan:** `_docs/plan.md`.  
> **Sync check:** `gh issue list --json number,title | jq length` == `grep -c "^## Task: " _docs/tasks.md`

---

## Task: 1 — Project scaffolding + Docker + CI + context docs
**Goal:** Enable any engineer to clone and `docker compose up` a working Django project so that all future work has a consistent, tested baseline.
**Description:** Scaffolds Django 5.1 project with apps (`accounts`, `households`, `chores`, `groceries`, `bills`, `maintenance`, `activity`, `core`), Postgres+Redis+Mailpit compose, base settings with custom `User(email)`, HTMX+Tailwind base templates, and context docs (`AGENTS.md`, `process.md`, `stack-decision.md`, team personas). Establishes `ruff`/`mypy`/`pytest` harness per `_docs/testing-guidelines.md`. See plan §10 and stack-decision §4.8.
**Acceptance Criteria:**
- [ ] AC1: Given a fresh checkout, when `docker compose up --build` then web responds 200 on `/` and `/admin/` (prove: `curl -s http://localhost:8000 | grep Household`)
- [ ] AC2: Given no `.env`, when `cp .env.example .env && python manage.py migrate` then migrations apply with no errors and `python manage.py check` exits 0 (prove: logs)
- [ ] AC3: Given scaffold, when `ruff check . && ruff format --check . && pytest -q` then all pass (prove: command output)
**Constraints:**
- Stack per `_docs/stack-decision.md` §A: Django 5.1 + HTMX + `whitenoise` + `gunicorn`, no React
- Files: `manage.py`, `core/settings.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `AGENTS.md`, `_docs/process.md`, `_docs/team/*.md`, `templates/base.html`, `pyproject.toml`
- Security: `SECRET_KEY` from env, `DEBUG` off in prod, `ALLOWED_HOSTS` env
**Out of Scope:**
- No household/chore business logic (issues #2+)
- No DRF API or native apps
- No CI GitHub Actions yet (can be #13)
**Labels:** `type:chore`, `area:infra`, `role:swe`, `effort:M`, `status:done`
**Dependencies:** None (root). Blocks #2–#14
**Estimate:** M
**QA Notes:** Run `python manage.py check`, `python manage.py migrate`, `ruff check .`, `pytest -q`; `docker compose config` validates; fresh `git clone` → `docker compose up` smoke.

---

## Task: 2 — Auth + households + membership + invites (F-01, F-02)
**Goal:** Enable users to create or join households via email/password and invite tokens so that any flatshare/family/couple can onboard in <3 minutes (plan §1.3).
**Description:** Implements custom `User` (email login), `Household` (name, type `roommates|family|couple|custom`, timezone), `Membership` (user×household, role `admin|member|parent|child`), and `Invite` (email, token, expiry 7d, single use). Provides signup/login/logout, password reset via email token, and invite flow `/invite/<token>`. Covers plan §3.1A, J1-2.
**Acceptance Criteria:**
- [ ] AC1: Given a new user POSTs `/accounts/signup` with email+password, when valid then `User` created with hashed password and redirected to `/households/new` (prove: `pytest accounts/tests/test_auth.py::test_signup -q`)
- [ ] AC2: Given an admin invites `guest@example.com` from a household, when guest follows `/invite/<token>` within 7d then membership `member` created, token invalidated, and household appears in dashboard (prove: `pytest households/tests/test_invite.py -q` + Playwright invite subflow in J1)
- [ ] AC3: Given 5 failed logins from same IP within 1 min, when 6th attempt then 429/rate-limited and login page shows generic error (prove: `pytest accounts/tests/test_rate_limit.py -q`)
- [ ] AC4: Given authenticated user, when GET household detail then only members of that household can view (403 for outsider) (prove: `pytest households/tests/test_scoping.py -q`)
**Constraints:**
- Stack: Django Auth per stack-decision §4.1, `session` cookie `HttpOnly/Secure/SameSite=Lax`, `{% csrf_token %}`, `django-ratelimit` 5/min on login
- Files: `accounts/models.py`, `households/models.py`, `households/views.py`, `templates/accounts/`, `templates/households/`, `core/urls.py`
- Security: PBKDF2/argon2 hash, invite token 32-byte, expiry enforced server-side
**Out of Scope:**
- OAuth/SSO, 2FA, social login
- Payment/billing roles
- Child-parent approval toggle (comes in #5)
**Labels:** `type:feature`, `area:auth`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #1
**Estimate:** M
**QA Notes:** `pytest accounts households -q`; manual signup → create household → invite → accept; check `mail.outbox` for reset email; try expired token (8d) shows 410.

---

## Task: 3 — Chore CRUD + status flow (F-03, F-05)
**Goal:** Enable household members to create, edit, delete and complete chores with effort, categories and due dates so that daily home ops have a single source of truth.
**Description:** Implements `Chore` model (title, description, category, effort 1–5, minutes, status `todo|in_progress|completed|overdue|skipped`, assignee FK?, dueAt, completedAt, proofUrl, recurrenceRule FK?, household FK). Provides list/create/detail/edit/delete views (HTMX) and one-click `POST /chores/<id>/complete`. Overdue computed server-side. See plan §3.1B, §5 F-03/05.
**Acceptance Criteria:**
- [ ] AC1: Given a member POSTs valid chore with title/effort/category/dueAt, when saved then chore appears in `/chores/` list scoped to household (prove: `pytest chores/tests/test_crud.py -q`)
- [ ] AC2: Given a dueAt < now() and status `todo`, when viewing dashboard then badge `overdue` shows (and `is_overdue()` returns True), regardless of client clock (prove: `pytest chores/tests/test_overdue.py -q` with `time-machine` frozen time)
- [ ] AC3: Given a chore `todo`, when `POST /chores/<id>/complete` then status → `completed` with `completedAt=now()` and second POST returns 400 (prove: `pytest chores/tests/test_status.py -q`)
**Constraints:**
- Stack: `chores/models.py`, `chores/views.py`, `core/rrule.py` (not used yet), HTMX `hx-post` for complete, server-side `due_at` UTC with household `timezone` render
- Files: `chores/`, `templates/chores/`, `tests/`, indexes `(household_id, status, due_at)` per plan §7
- Security: `login_required` + `household_membership_required` + CSRF, audit via `post_save` → `Activity` (stub may be #7)
**Out of Scope:**
- Recurrence generation (#4)
- Assignment pools/rotation (#5)
- Photo proof upload (#11 — placeholder `proofUrl` field only)
**Labels:** `type:feature`, `area:chores`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #2
**Estimate:** M
**QA Notes:** `pytest chores -q`; manual: login → create chore → verify MP list → mark done → refresh → shows completed; try mark done twice → error.

---

## Task: 4 — Recurrence engine (rrule, generate instances) (F-03, F-09, F-10)
**Goal:** Enable chores/bills/maintenance to auto-schedule recurring instances so that ≥90% of weekly chores need no manual re-creation.
**Description:** Implements `RecurrenceRule` (or field `rrule_str` RFC5545 + `dtstart`) and service `core/services/rrule.py` wrapping `dateutil.rrule` with timezone-aware handling. Provides hourly job `manage.py generate_due_instances` (or `django-q2` beat) that creates next `Chore` instance when `nextDueAt < now+7d`. Shared by chores, bills, maintenance. Handles DST, monthly 31→30, `every 2nd Sunday`. See plan §3.1B recurrence, §14 risks.
**Acceptance Criteria:**
- [ ] AC1: Given `rrule_str="FREQ=WEEKLY;BYDAY=MO"` and dtstart Mon 07:00 Europe/Berlin, when `next_due(after=Mon 07:01)` then returns next Mon 07:00 (prove: `pytest core/tests/test_rrule.py -q` parametrized)
- [ ] AC2: Given a chore with `FREQ=MONTHLY;BYMONTHDAY=31`, when generating instances over Feb→Mar in `Europe/Berlin` then next due is Mar 31 (no Feb 31 phantom) (prove: `pytest core/tests/test_rrule_edges.py -q`)
- [ ] AC3: Given a completed recurring chore, when hourly job runs then a new `Chore` clone with `dueAt=nextDue` and status `todo` is created (prove: `pytest chores/tests/test_recurrence_job.py -q` with `time-machine`)
- [ ] AC4: Given DST spring-forward gap (2026-03-29 02:00 Europe/Berlin missing), when rule `FREQ=DAILY;BYHOUR=2` then next occurrence skips missing hour without exception (prove: `pytest core/tests/test_rrule_dst.py -q`)
**Constraints:**
- Stack: `python-dateutil` `rrulestr`, `zoneinfo` per household `timezone`, store UTC, render in tz
- Files: `core/rrule.py` (or `core/services/rrule.py`), `chores/models.py` (`rrule_str` field), `core/management/commands/generate_due_instances.py`, `core/tests/`
- Perf: index `(household_id, nextDueAt)`, job idempotent (no duplicate clones)
**Out of Scope:**
- UI recurrence builder polish (basic `FREQ` + `BYDAY` text field ok)
- Per-user notification scheduling (#11)
**Labels:** `type:feature`, `area:chores`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #3
**Estimate:** M
**QA Notes:** `pytest core chores -q -k rrule`; manual cron: `python manage.py generate_due_instances` → list shows new instance; check logs for idempotency on double run.

---

## Task: 5 — Assignment modes (assigned / pool / rotating) (F-04)
**Goal:** Enable chores to be assigned, claimed from pool, or auto-rotated so that flatshares get fairness and families get parental control.
**Description:** Implements three modes in `chores/services/assignment.py`: `ASSIGNED` (FK assignee), `POOL` (null → anyone can claim), `ROTATING` (ordered list of membership ids + pointer or effort-balanced min `Sum(effort)` 30d). Provides `POST /chores/<id>/claim`, `POST /chores/<id>/swap` stub for V1, and HTMX claim button. Enforces family mode: `child` cannot be admin nor delete chores.
**Acceptance Criteria:**
- [ ] AC1: Given a chore with mode `POOL`, when `POST /chores/<id>/claim` by member then `assignee=memb` and status remains `todo` (prove: `pytest chores/tests/test_assignment.py::test_pool_claim -q`)
- [ ] AC2: Given a household with round-robin `ROTATING` and members [A,B,C], when chores complete in order then next assignee cycles A→B→C→A (prove: `pytest chores/tests/test_rotating.py -q` parametrized)
- [ ] AC3: Given household type `family` and actor role `child`, when `DELETE /chores/<id>` then 403 (prove: `pytest chores/tests/test_roles.py -q`)
**Constraints:**
- Stack: pure Python service `chores/services/assignment.py` unit-testable, Django view wrappers enforce membership, HTMX `hx-post` claim updates row with `outerHTML`
- Files: `chores/services/assignment.py`, `chores/views.py`, `templates/chores/partials/`
- Perf: fairness lookup cached per request, not N+1
**Out of Scope:**
- Full swap/trade request flow (V1.1 — #12)
- Reward store/penalties (V2)
**Labels:** `type:feature`, `area:chores`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #3, #4 (if rotating uses recurrence)
**Estimate:** M
**QA Notes:** `pytest chores -q -k assignment`; manual: create pool chore → Claim as Jordan → assignee shows Jordan; rotate: complete → next instance assigned to next round-robin member.

---

## Task: 6 — Dashboard + filters + overdue logic (F-06, F-07 partial)
**Goal:** Enable members to see overdue/today/my-queue at a glance and filter chores so that work is visible without hunting.
**Description:** Builds dashboard `/` with 4 cards (Overdue, Due today, My queue, Fairness teaser) and weekly calendar strip; chores list `/chores/` with table→cards responsive, HTMX filter `?assignee=me|pool|all&status=todo|overdue&category=kitchen&q=…` + `hx-push-url`. Overdue vs dueToday computed server-side by `due_at.date()` in household tz. See plan §8 IA.
**Acceptance Criteria:**
- [ ] AC1: Given chores with mix of overdue/due-today/future, when `GET /?` then counts match server query `due_at < now()` vs `due_at.date()==today` in household tz (prove: `pytest chores/tests/test_dashboard.py -q` + manual dashboard numbers)
- [ ] AC2: Given filter `?assignee=me`, when HTMX `hx-get` then response partial contains only `assignee==request.user` OR pool unclaimed, and URL pushed (prove: `pytest chores/tests/test_filters.py -q`)
- [ ] AC3: Given kitchen filter, when mobile viewport <768px then table collapses to stacked cards without horizontal scroll (prove: Playwright visual check or manual Chrome device toolbar)
**Constraints:**
- Stack: Django templates + HTMX `hx-get/hx-push-url`, Alpine minimal for disclosure, Tailwind per `design-system.md` §2–4
- Files: `templates/dashboard.html`, `templates/chores/list.html`, `chores/views.py`, `chores/filters.py`
- A11y: keyboard nav, focus ring, color not sole indicator for status (badge icon+text)
**Out of Scope:**
- Full fairness chart (#7 does detail)
- Search full-text across history (stub `q` contains title only)
**Labels:** `type:feature`, `area:dashboard`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #3, #5
**Estimate:** M
**QA Notes:** `pytest chores -q`; manual: toggle filters, check overdue sorting asc, `Lighthouse` perf ≥90.

---

## Task: 7 — Fairness meter + history + activity feed (F-06, F-12)
**Goal:** Enable households to see who did how much (effort-weighted) and audit history so that equity is transparent and disputes reduce.
**Description:** Implements `Activity` model (household, actor, action, entityType/Id, diff jsonb, createdAt) via signals on chore create/update/complete/delete. Implements fairness query `SUM(effort)` per member per window (week/month/all-time) and bar chart (server-rendered Tailwind `width: {{pct}}%`) plus line trend (Chart.js lightweight or HTMX partial). Provides History/Activity feed last 50. See plan §3.1C, §5 F-06/12, §7 indexes.
**Acceptance Criteria:**
- [ ] AC1: Given 3 chores completed with efforts 5,3,1 by members A,B,A, when fairness month query then scores {A:6, B:3} and bar shows 66/33 (prove: `pytest chores/tests/test_fairness.py::test_effort_weighted -q`)
- [ ] AC2: Given any chore mutation, when action saved then `Activity` row exists with `actor=request.user`, `diff` json includes before/after (prove: `pytest activity/tests/test_activity.py -q`)
- [ ] AC3: Given activity feed GET `/activity/`, when member views then only that household’s last 50 events appear ordered `created_at desc` (prove: `pytest activity/tests/test_feed.py -q`)
**Constraints:**
- Stack: Django signals + ORM `annotate(Sum)`, no heavy React charts, server bars per `design-system.md` §3
- Files: `activity/models.py`, `activity/signals.py`, `chores/services/fairness.py`, `templates/dashboard.html` (fairness bar), `templates/activity/list.html`, indexes `(household_id, created_at)` on Activity
- Perf: materialized via ORM, not N+1; no analytics tracker
**Out of Scope:**
- Leaderboards, streaks, rewards (V2)
- Export CSV past fairness (comes in #12)
**Labels:** `type:feature`, `area:activity`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #3
**Estimate:** M
**QA Notes:** `pytest chores activity -q`; manual: complete chores → dashboard bar updates; check history shows claim/complete events; try cross-household → 403.

---

## Task: 8 — Groceries list (shared) (F-08)
**Goal:** Enable household to share a grocery list so that shopping is coordinated and no duplicate buys happen.
**Description:** Implements `GroceryItem` (household, name, qty, checked bool, addedBy, checkedBy?). Provides list at `/groceries/` with HTMX add/check/remove, optimistic UI, quantity edit inline. Supports “move to chore” link creating a Chore `Buy groceries` if desired (optional). Concurrent edits last-write wins. See plan §3.1D.
**Acceptance Criteria:**
- [ ] AC1: Given member POSTs `name="Oat milk" qty=2`, when valid then item appears unchecked and `addedBy=user` (prove: `pytest groceries/tests/test_groceries.py::test_add -q`)
- [ ] AC2: Given unchecked item, when `POST /groceries/<id>/toggle` then `checked=True`, `checkedBy=user` and HTMX swaps row without full reload (prove: `pytest groceries/tests/test_toggle.py -q`)
- [ ] AC3: Given two users POST concurrently updating same item name, when second saves then last-write persists and no 500 (prove: `pytest groceries/tests/test_concurrent.py -q` with sequential posts)
**Constraints:**
- Stack: `groceries/models.py`, `groceries/views.py`, `templates/groceries/` with `hx-post/hx-target`, CSRF, household scoping
- Files: `groceries/`, `templates/groceries/`
- UX: mobile-friendly inline edit, empty state `“No groceries — add one”`
**Out of Scope:**
- Price tracking, store integration, barcode
- Auto-chore creation required (optional nice-to-have, not blocking)
**Labels:** `type:feature`, `area:groceries`, `role:swe`, `effort:S`, `status:groomed`
**Dependencies:** Blocked by #2
**Estimate:** S
**QA Notes:** `pytest groceries -q`; manual: add item → check → uncheck → delete; concurrent: two tabs edit same item → second wins.

---

## Task: 9 — Bills tracker (recurring) (F-09)
**Goal:** Enable households to track recurring bills with payer rotation so that due bills are not missed.
**Description:** Implements `Bill` (household, name, amount, currency, dueAt, recurrenceRule optional, payer FK?, paidAt, status `due|paid|overdue`). Reuses `core/rrule.py` for recurrence, and `generate_due_instances` job creates next Bill on paid toggle. Provides `/bills/` list with `POST /bills/<id>/toggle-paid`. Email reminder stub deferred to #11. See plan §3.1D (light, not full accounting).
**Acceptance Criteria:**
- [ ] AC1: Given a bill with `dueAt=2026-09-01` and `FREQ=MONTHLY`, when marked paid then next instance `dueAt=2026-10-01` created with `payer=nextRotation` (prove: `pytest bills/tests/test_bills.py::test_recurring_paid -q`)
- [ ] AC2: Given a bill overdue and unpaid, when `dueAt < now()` then list shows `overdue` badge (prove: `pytest bills/tests/test_overdue.py -q`)
- [ ] AC3: Given `POST /bills/<id>/toggle-paid` then `Activity` logged with `paidAt` diff (prove: `pytest bills/tests/test_activity.py -q`)
**Constraints:**
- Stack: `bills/models.py`, `bills/views.py`, `core/rrule.py`, `Activity` signals
- Files: `bills/`, `templates/bills/`
- Note: NOT a ledger/splitwise — simple paid toggle + rotation only
**Out of Scope:**
- Payment integration, splitwise, bank sync
- Full accounting reports
**Labels:** `type:feature`, `area:bills`, `role:swe`, `effort:S`, `status:groomed`
**Dependencies:** Blocked by #2, #4 (recurrence)
**Estimate:** S
**QA Notes:** `pytest bills -q`; manual: create rent bill → toggle paid → verify next month appears; check household scoping.

---

## Task: 10 — Maintenance tasks (long-cycle) (F-10)
**Goal:** Enable households to schedule infrequent maintenance (filters, gutters, etc.) so that seasonal tasks are not forgotten.
**Description:** Implements `MaintenanceTask` (household, title, description, intervalDays or rrule, lastDoneAt?, nextDueAt, assignee?) with separate nav tab `/maintenance/` (distinct from daily chores). Reuses recurrence engine but shows as long-cycle; supports “Mark done → bumps nextDueAt = now + interval”. See plan §3.1D.
**Acceptance Criteria:**
- [ ] AC1: Given maintenance with `intervalDays=90` and `lastDoneAt=2026-06-01`, when POST `mark-done` then `lastDoneAt=now()` and `nextDueAt=now()+90d` (prove: `pytest maintenance/tests/test_maintenance.py -q`)
- [ ] AC2: Given maintenance list, when GET `/maintenance/` then items sorted by `nextDueAt asc` and overdue maintenance shows `overdue` badge (prove: `pytest maintenance/tests/test_list.py -q`)
- [ ] AC3: Given `MaintenanceTask` and `Chore` share recurrence engine, when job `generate_due_instances` runs for maintenance interval then no duplicate `Chore` is created (prove: `pytest maintenance/tests/test_job_isolation.py -q`)
**Constraints:**
- Stack: `maintenance/models.py`, `maintenance/views.py`, Diet recurrence (interval vs rrule cover both), Tailwind cards
- Files: `maintenance/`, `templates/maintenance/`
- Navigation: separate tab, but may reuse chores filter UX
**Out of Scope:**
- Vendor/marketplace integration
- Photo proof for maintenance (reuse `proofUrl` optional later)
**Labels:** `type:feature`, `area:maintenance`, `role:swe`, `effort:S`, `status:groomed`
**Dependencies:** Blocked by #2, #4
**Estimate:** S
**QA Notes:** `pytest maintenance -q`; manual: create “Clean gutters 180d” → mark done → verify next due bumps 180d; check isolated from chores.

---

## Task: 11 — Notifications: in-app bell + email digest jobs (F-11)
**Goal:** Enable timely awareness via in-app and email without native push, so households see overdue/assignment changes without spam.
**Description:** Implements in-app `Notification` (or lean: unread `Activity` count) with bell polling (`hx-get` every 60s). Implements email digests: daily 08:00 per household timezone and weekly Sunday summary, plus 24h overdue reminder, toggled per user (`notificationPrefs`). Uses `django-q2` (or `cron` fallback calling `manage.py send_digests`). Dev backend console; prod SMTP → Mailpit in Docker. See plan §3.1E.
**Acceptance Criteria:**
- [ ] AC1: Given digest job runs at 08:00 household tz, when user has `emailDaily=True` then `mail.outbox` (or Mailpit API `/api/v1/messages`) contains digest with overdue + today + fairness teaser (prove: `pytest activity/tests/test_digests.py -q` with `time-machine` frozen 08:00)
- [ ] AC2: Given a chore assigned to user, when assignment changes then bell count increments and `GET /activity/?unread` returns count (prove: `pytest activity/tests/test_bell.py -q`)
- [ ] AC3: Given user disables daily email, when job runs then no email sent to that user (prove: `pytest activity/tests/test_prefs.py -q`)
**Constraints:**
- Stack: `django-q2` + `redis` per `stack-decision.md` §4.5 or `manage.py send_digests` cron; `django.core.mail`, Mailpit `axllent/mailpit`
- Files: `activity/management/commands/send_digests.py`, `core/settings.py` email backends, `templates/base.html` bell
- UX: batch digests (no email per edit), HTMX poll, configurable prefs under Settings
**Out of Scope:**
- Native mobile push, SMS/WhatsApp
- Per-edit realtime websocket (poll is enough)
**Labels:** `type:feature`, `area:activity`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #6, #7
**Estimate:** M
**QA Notes:** `pytest activity -q -k digest`; manual: `python manage.py send_digests` → check Mailpit UI `http://localhost:8025`; toggle prefs → no email.

---

## Task: 12 — Export + templates + search & filter polish (V1.1: templates, export, search)
**Goal:** Enable households to reuse setups, export data and find chores fast so that onboarding and audit are low-effort.
**Description:** Adds chore `templates` (“Starter pack” family/flatshare/couple → 10–15 chores): selection at household create and later `POST /chores/templates/apply`. Adds export: `GET /activity/export.csv` (CSV history) and `GET /chores/ical/` (iCal feed `VEVENT` for due chores). Enhances search: `q` full contains on title/description + filters `assignee, category, due, status, effort`. Adds PWA stub (optional manifest). See plan §3.2.
**Acceptance Criteria:**
- [ ] AC1: Given new household picks “Flatshare starter”, when applied then ≥10 chores created with mixed `assigned/pool/rotating` and rrules (prove: `pytest chores/tests/test_templates.py -q`)
- [ ] AC2: Given completed chores, when `GET /activity/export.csv?range=month` then CSV header and rows match filtered chores, and iCal `GET /chores/ical/` returns `BEGIN:VCALENDAR` with `VEVENT` per due chore (prove: `pytest chores/tests/test_export.py -q` + `activity/tests/test_csv.py`)
- [ ] AC3: Given search `q="bath"` + `category=bathroom`, when `GET /chores/?q=bath&category=bathroom` then only matching chores appear (prove: `pytest chores/tests/test_search.py -q`)
**Constraints:**
- Stack: `chores/fixtures/templates.json`, `core/ical.py` util, `csv` stdlib, HTMX filters polish per `design-system.md`
- Files: `chores/management/`, `chores/views.py` export, `templates/chores/`
- No heavy libs: stdlib `csv` + `ical` builder
**Out of Scope:**
- Full PWA offline sync (stub manifest only)
- Advanced full-text (`postgres` `tsvector`) — simple `icontains` is enough for V1.1
**Labels:** `type:feature`, `area:chores`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #3, #6
**Estimate:** M
**QA Notes:** `pytest chores activity -q`; manual: apply template → CSV download → iCal import into Google/Apple Calendar; search `bath` + filter bar.

---

## Task: 13 — Testing harness + e2e for 3 journeys + coverage gate (NFR)
**Goal:** Ensure every critical path is independently verified by tests so that `pytest --cov --cov-fail-under=80` is a green gate and e2e mirrors plan §4.
**Description:** Hardens `tests/conftest.py` (factories, frozen time, `client` login helper), `tests/e2e/helpers.py`, and Playwright config `playwright.config.ts` for journeys J1 (flatshare onboard), J2 (family approval), J3 (couple groceries/bills/balance). Adds CI workflow `.github/workflows/ci.yml` (`ruff`, `mypy`, `pytest --cov`, `playwright`). Enforces 80% gate (90% for `core/` + `chores/services/`). See `_docs/testing-guidelines.md`.
**Acceptance Criteria:**
- [ ] AC1: Given clean repo, when `pytest --cov --cov-fail-under=80` then passes (non-e2e excludes) and `htmlcov/` shows `core/rrule.py` ≥90% (prove: `pytest --cov --cov-report=term-missing`)
- [ ] AC2: Given `npx playwright test --project=chromium` then J1, J2, J3 pass from fresh DB with no manual seeding (prove: `playwright` run log, `trace` on first retry)
- [ ] AC3: Given CI pushes to `main` PR, when workflow runs then `ruff check`, `mypy`, `pytest` gates block on failure (prove: `.github/workflows/ci.yml` exists and `gh workflow view ci` shows steps)
**Constraints:**
- Stack: `pytest-django`, `factory-boy`, `time-machine`, `playwright` as in `testing-guidelines.md` §7–8; `pyproject.toml` coverage config already present
- Files: `tests/`, `playwright.config.ts`, `.github/workflows/ci.yml`
- No flakiness: deterministic time, no `sleep`, mock email via `mailoutbox`/Mailpit
**Out of Scope:**
- Load/performance testing (handled later)
- A11y Axe full suite (comes with perf PR)
**Labels:** `type:chore`, `area:testing`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #1; should run after #2–#12 but can scaffold harness early
**Estimate:** M
**QA Notes:** `pytest -q && pytest --cov -q`, `npx playwright test --reporter=list`; check CI badge on PR; J1 in `tests/e2e/test_j1_flatshare.py` etc.

---

## Task: 14 — Docs: README, self-host guide, backup/restore, AGENTS polish
**Goal:** Enable a self-hoster on a $5 VPS to go from clone to first chore in <10 minutes without asking for help.
**Description:** Finalizes `README.md` (now scaffolded), self-host guide in `README` + `_docs/` (env doc, TLS via Caddy/Nginx snippet, backup `pg_dump` + restore `psql`, upgrade notes). Polishes `AGENTS.md`/`CLAUDE.md` commands to match scaffolded reality. Adds `docker-compose.prod.yml` override hint and `scripts/backup.sh`. Verifies guide by spinning a clean VM/WSL docker.
**Acceptance Criteria:**
- [ ] AC1: Given clean WSL/docker without prior images, when following README Quick Start verbatim then `http://localhost:8000` serves and `createsuperuser` login works in <10 min wall-clock (prove: manual timing + CI `docker compose up -d --build` smoke)
- [ ] AC2: Given `docker compose exec db pg_dump … | gzip > backup.sql.gz`, when restoring into fresh DB then household/chore counts match pre-backup (prove: `scripts/backup.sh` + `scripts/restore.sh` dry-run in CI)
- [ ] AC3: Given `AGENTS.md` lists commands, when running each listed command then they succeed (prove: `pytest -q`, `ruff check .`, `mypy .`, `docker compose up` — no drift)
**Constraints:**
- Stack: Docker/Compose already, docs are Markdown only, no new code
- Files: `README.md`, `AGENTS.md`, `CLAUDE.md`, `_docs/plan.md` (if fixes needed), `scripts/backup.sh`, `docker-compose.prod.yml` (optional), `.env.example` docs
- Tone: calm, checklist, copy-pasteable commands
**Out of Scope:**
- Hosted SaaS marketing site
- Video walkthrough (nice later)
**Labels:** `type:chore`, `area:docs`, `role:swe`, `effort:S`, `status:groomed`
**Dependencies:** Blocked by #1, #2–#13 (docs reflect finished product)
**Estimate:** S
**QA Notes:** Follow README blind on fresh WSL; run backup.sh → restore.sh → counts match; grep `AGENTS.md` commands and execute each; check Lighthouse ≥90 on dashboard.

---

## Sync Notes for PM (`/goal sync tasks`)

- After creating Issues via `gh issue create --title "Task: N — …" --body-file <task.md slice>`, set labels `type:`, `area:`, `effort:`, `status:groomed`.
- Keep titles exactly as `## Task: N — …` first line.
- This file count: `grep -c "^## Task: " _docs/tasks.md` should equal `gh issue list --json number --limit 200 | jq length`.
- Drill: `gh issue list --label status:groomed` before `/goal implement` loops.

*End of tasks — ready for `/goal groom all issues` (already groomed) and `/goal implement issue #N` loops.*
