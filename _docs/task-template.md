# Task Template — Use for every issue in `_docs/tasks.md` and GitHub

> Copy this template verbatim. PM grooms every issue to this shape. SWE implements against AC only.

```markdown
## Task: <short imperative title, e.g., "Add rotating chore assignment">
**Goal:** Enable <actor> to <action> so that <value> — one sentence, imperative.
**Description:** 2–4 sentences: context from plan, user value, where in stack. Link to plan section.

**Acceptance Criteria (checkable):**
- [ ] AC1: Given <precondition> when <action> then <verifiable outcome> (prove via: `command` or UI step)
- [ ] AC2: ...
- [ ] AC3: ...

**Constraints:**
- Stack: e.g., Django 5.1 + HTMX + Tailwind per `_docs/stack-decision.md` §A; do not introduce React/Vue
- Files: e.g., `chores/services/assignment.py`, `templates/chores/`, `tests/test_assignment.py`
- Security/perf: e.g., CSRF, rate limit, server-side overdue, indexes

**Out of Scope:**
- Explicitly not doing: e.g., “No native push, no AI suggestions, no React”

**Labels:** `type:feature|chore|bug`, `area:auth|chores|groceries|bills|maintenance|activity|infra|docs|ui|testing`, `role:swe`, `effort:S|M|L`, `status:groomed`
**Dependencies:** Closes #N, Blocked by #M, Related to #K
**Estimate:** S (<4h), M (0.5–2d), L (2–5d)
**QA Notes:** How QA will verify (e.g., `pytest chores/tests -q`, Playwright J1 steps, Mailpit API).
```

## Checklist for PM Grooming (must pass before `groomed`)

- [ ] Goal is one sentence, starts with verb, names actor and value
- [ ] AC are checkable (each has Given/When/Then + proof command/UI)
- [ ] At least 2 AC, at most 6 (3–4 ideal)
- [ ] Constraints name files/stack, no out-of-ADR tech
- [ ] Out-of-Scope has 2–4 bullets (prevents scope creep)
- [ ] Labels include `type:`, `area:`, `role:swe`, `effort:` and `status:groomed`
- [ ] Dependencies referenced if any; no orphan blocked task
- [ ] QA Notes tell QA exactly how to prove

## Example (filled)

```markdown
## Task: Auth — email/password + invite + membership
**Goal:** Enable any user to create or join a household via email/password and invite links so that flatshares/families can onboard in <3 minutes.
**Description:** Implements F-01, F-02 from plan §5. Custom User (email login), Household+Membership with roles (admin/member/parent/child), invite tokens valid 7d. Uses Django Auth + session cookie HttpOnly/Secure/SameSite=Lax + CSRF + rate limit 5/min. See plan §4 J1/J2.

**Acceptance Criteria:**
- [ ] AC1: Given a fresh DB, when POST /accounts/signup email+password then User created with hashed password and redirected to /households/new (prove: `pytest accounts/tests/test_auth.py -q` + manual signup shows household form)
- [ ] AC2: Given an admin invites invitee@example.com, when invitee follows /invite/<token> within 7d then membership created as member and token single-use (prove: unit test token expiry + Playwright invite flow)
- [ ] AC3: Given 5 failed logins/min from same IP, when 6th attempt then 429 and email not leaked (prove: `pytest accounts/tests/test_rate_limit.py -q`)

**Constraints:**
- Stack per `_docs/stack-decision.md` §4.1: Django Auth, no allauth yet, `households/models.py` + `accounts/models.py`
- Files: `accounts/`, `households/`, `templates/accounts/`, `tests/`
- Security: bcrypt/PBKDF2, HttpOnly cookie, CSRF on all POST, rate limit

**Out of Scope:**
- OAuth/SSO, 2FA, social login
- Payment or billing integration

**Labels:** `type:feature`, `area:auth`, `role:swe`, `effort:M`, `status:groomed`
**Dependencies:** Blocked by #1 (scaffolding)
**QA Notes:** Run `pytest accounts -q`, check Mailpit for reset email, try expired token shows 410.
```
