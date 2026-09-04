# Testing Guidelines — Household Chores Manager

> **Load when:** `area:testing`, touching `tests/`, `chores/`, or coverage/Playwright work.
> **Stack:** Django 5.1 + pytest + pytest-django + factory-boy + ruff/mypy + Playwright
> **Gates:** `ruff check` pass, `mypy` pass, `pytest --cov --cov-fail-under=80` (domain logic), Playwright J1-J3.

## 1. Strategy

- **Pyramid:** Many fast unit tests (services, models) → fewer integration (views, ORM) → very few e2e (3 journeys). Mock only email/clock/S3.
- **Domain logic is critical:** recurrence, assignment, fairness, overdue — all have DST/boundary edge cases. Cover 100% branches there; gate is 80% overall but 90%+ for `core/` and `chores/services/`.
- **No flaky tests:** No sleep, no real network, deterministic time via `freezegun` / `time-machine`.

## 2. Layout

```
tests/
├── conftest.py              # fixtures: user, household, client, time-machine fixtures
├── factories.py             # factory-boy factories
├── test_fairness.py         # unit: service pure functions
├── test_rrule.py
├── e2e/
│   ├── test_j1_flatshare.py # Playwright
│   ├── test_j2_family.py
│   └── test_j3_couple.py
household/ (or apps)
├── chores/tests/test_models.py
├── chores/tests/test_views.py
├── chores/tests/test_assignment.py
├── accounts/tests/test_auth.py
```
- `pytest.ini`: `DJANGO_SETTINGS_MODULE = core.settings`, `pythonpath = .`, `markers = e2e, unit, integration`.
- `conftest.py` provides `db`, `client`, `user_factory`, `household_factory`, `frozen_time` (time-machine).

## 3. Unit Tests (fast, pure)

**Target:** `core/rrule.py`, `chores/services/assignment.py`, `chores/services/fairness.py`, model methods.

Example fairness:

```python
def test_fairness_effort_weighted(db, household, users):
    create_chore(household, assignee=users[0], effort=5, completed_at=now())
    create_chore(household, assignee=users[1], effort=1, completed_at=now())
    scores = fairness_scores(household, window="month")
    assert scores[users[0].id] == 5
    assert scores[users[1].id] == 1
```

- Use `factory-boy` for data, `pytest.mark.parametrize` for boundaries (DST last Sunday, leap, monthly 31→30).

## 4. Integration Tests (views, ORM)

```python
def test_create_chore_csrf_and_auth(client, household):
    client.force_login(household.admin)
    resp = client.post(
        reverse("chores:create", args=[household.id]),
        {"title": "Dishes", "effort": 3, "due_at": ...},
    )
    assert resp.status_code in (200, 302)  # HTMX may 200 partial
    assert Chore.objects.filter(title="Dishes").exists()


def test_overdue_computed_server_side(freezer, household):
    freezer.move_to("2026-09-05 09:00 Europe/Berlin")
    chore = Chore.objects.create(
        due_at="2026-09-04 09:00", household=household, status="todo"
    )
    assert chore.is_overdue() is True  # never trust client clock
```

- Always assert server-side `is_overdue` logic: `due_at < now()` AND `status != completed`.
- Use `django.test.Client` with `HTTP_HX_REQUEST="true"` for HTMX partial assertions.

## 5. Factories (factory-boy)

```python
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = Faker("email")
    password = PostGenerationMethodCall("set_password", "testpass123")


class HouseholdFactory(...):
    name = Faker("company")
    type = "roommates"
    timezone = "Europe/Berlin"
```

## 6. Recurrence Edge Cases (required)

- DST spring forward (02:00 missing), fall back (duplicated hour), monthly on 31st, `every 2nd Sunday` rrule, timezone per-household stored UTC but renders in household tz.
- Test util `next_due(rrule_str, after: datetime, tz: ZoneInfo) -> datetime`.

## 7. E2E — Playwright (3 journeys)

Run: `npx playwright test` or `pytest --e2e` wrapper. Base `http://127.0.0.1:8000`.

**J1 Flatshare onboard:** Create household → invite link → claim chore → dashboard fairness bar.
**J2 Family approval:** Parent assigns to child (needs approval) → child marks done → parent approves → points appear.
**J3 Couple balance:** Groceries add/check, bill paid toggle, Sunday digest email (check Mailpit `http://localhost:8025/api/v1/messages`).

Helpers: `tests/e2e/helpers.py` with `login(page, user)`, `invite_and_join(page, token)`.

Config `playwright.config.ts`:
```ts
export default defineConfig({
  webServer: { command: "python manage.py runserver 8000", url: "http://127.0.0.1:8000", reuseExistingServer: true },
  use: { trace: "on-first-retry" },
});
```

## 8. Coverage & Gates

```bash
uv run pytest --cov --cov-fail-under=80 --cov-report=term-missing --cov-report=html
# CI also runs: ruff check . && ruff format --check . && mypy . && npx playwright test
```

- Ignore `migrations/`, `static/`, `tests/` from coverage.
- Domain modules (`core/rrule.py`, `chores/services/*`) should hit ≥90% — add `# pragma: no cover` only for `if TYPE_CHECKING` blocks.

## 9. Mocking & Fixtures

- **Time:** `time-machine` or `freezegun` in `conftest` fixture `frozen_time("2026-09-04")`.
- **Email:** `django.core.mail.outbox` (pytest `mailoutbox`) or Mailpit API; never hit real SMTP.
- **Media:** `override_settings(MEDIA_ROOT=tmp_path)` and `SimpleUploadedFile`.
- **Redis/Celery:** In tests, use `CELERY_ALWAYS_EAGER=True` or `django-q2` sync.

## 10. Lint / Type / Format

```bash
uv run ruff check .        # fail on error
uv run ruff format --check .
uv run mypy .              # strict for core/, chores/services/, loose for migrations
```

`pyproject.toml` sets `[tool.ruff]`, `[tool.mypy]` strict.

## 11. What to Test Per Issue Template

Each task’s AC maps to tests:

| AC type | Test layer | Example proof |
|---|---|---|
| Model/service logic | unit | `test_assignment.py` parametrized |
| View auth/CSRF | integration | `client.post` + `assertRedirect` |
| Filter/sort/overdue logic | integration | GET with `?status=overdue` asserts qs |
| Full flow J1-J3 | e2e | Playwright script |

SWE must commit tests with code; QA reruns same suite fresh.

## 12. Anti-patterns (fail PR if seen)

- `time.sleep` in tests, randomized data without seed, hitting real email/DB outside test, asserting client-side overdue, skipping CSRF in POST tests.
