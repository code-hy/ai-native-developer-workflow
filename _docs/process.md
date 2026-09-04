# Process — Household Chores Manager

> **Required reading:** `AGENTS.md` → `_docs/plan.md` → this file every session.

## 1. Principles

- **Spec-driven, not assumption-driven.** If AC is ambiguous, open a `question` issue and block. Do not invent behavior.
- **Single source of truth = GitHub Issues.** `_docs/tasks.md` is a generated snapshot; `gh issue list` is canonical. Keep them in sync.
- **Checkable > subjective.** Every goal has a command or UI step that proves it (e.g., `pytest -q`, `gh issue view 12`, curl, Playwright). Never close on “looks cleaner.”
- **Continuous feedback.** When you fix a recurring mistake, update the relevant `_docs/*.md` in the same PR (plan, design-system, testing-guidelines, etc.).

## 2. Roles & Responsibilities (Graph Engineering)

| Role | File | Owns | May | Must NOT |
|---|---|---|---|---|
| **PM** (Product Manager) | `_docs/team/pm.md` | Grooming, labels, AC, priorities, `tasks.md` ↔ Issues sync | Create/edit issues, set milestones, run `/goal groom` | Write code, close implemented issues |
| **SWE** (Software Engineer) | `_docs/team/software-engineer.md` | Implementation + unit tests per AC, commits, PR | Comment AC checklist, ask questions via `question` label | Close issues, bypass AC, choose stack outside ADR |
| **QA** (QA Engineer) | `_docs/team/qa-engineer.md` | Independent verification, `PASS`/`FAIL` with logs, close only on `PASS` | Open follow-up bug issues, run `pytest`/`playwright` locally | Fix code directly, approve without evidence |

Routing state machine:

```
backlog (needs-grooming) → groomed → in_progress → in_review (qa) → done
                                              ↘︎ fail → in_progress (new commit)
```

Labels drive automation: `role:pm|swe|qa`, `status:needs-grooming|groomed|in_progress|in_review|done`, `type:feature|chore|bug`, `area:auth|chores|groceries|bills|maintenance|activity|infra|docs`, `effort:S|M|L`.

## 3. Issue Lifecycle

1. **Creation:** Anyone may create raw issue with title + 1-line description. PM triages daily, adds `needs-grooming`.
2. **Grooming (PM only, `/goal groom all issues`):** For each open issue, ensure template filled: Goal, Description, AC (checkable), Constraints, Out-of-Scope, Labels, Dependencies. Remove `needs-grooming`, add `groomed`. Stop condition: `gh issue list --label needs-grooming` is empty and every `groomed` issue has all sections.
3. **Implementation (SWE, `/goal implement issue #N`):**
   - Checkout `feat/issue-#N-slug` from `main`.
   - Implement commit-by-AC (e.g., `feat(#12): add rotating assignment — AC1, AC2`).
   - Write unit tests co-located, run `ruff`, `mypy`, `pytest -q`; include evidence in PR body.
   - Comment on issue with AC checklist ` - [x] AC1 …` + logs/screenshot.
   - Open PR (`Closes #N` in body). Move issue `groomed → in_progress → in_review`. Never close.
4. **QA (QA, `/goal qa issue #N`):**
   - Fresh checkout, `pytest -q`, `playwright test` if UI, manual walk-through of AC.
   - Post verdict comment: `PASS` + evidence OR `FAIL` + diagnostic logs + failing AC numbers.
   - On `PASS`: merge PR, close issue → `done`. On `FAIL`: add `status:fail`, reopen via comment, SWE continues.
5. **Sync (`/goal sync tasks`):** PM ensures `gh issue list --json number,title | jq length` == lines in `_docs/tasks.md` (excluding header) and titles match; if drift, regenerate `tasks.md` from Issues.

## 4. Branching & Commits

- `main` is protected; PR required; linear history via squash or rebase; require `ruff`, `mypy`, `pytest` passing + QA PASS comment.
- Branches: `feat/issue-#N-slug` (feat), `fix/issue-#N-slug` (bugs), `docs/issue-#N-slug`.
- Commits: `feat(#12): …`, `fix(#8): …`, `chore(#1): …`, `docs(#1): …`, `test(#5): …`. Include AC refs when possible.
- PR template: Summary → AC checklist → How tested (`pytest` output) → Screenshots → Notes for QA.

## 5. Loop Goals (Harness Contracts)

| Goal | Agent | Checkable Stop Condition | Command Proof |
|---|---|---|---|
| `groom all issues` | PM | 0 issues with `needs-grooming`; every open issue has Goal/AC/Constraints/Out-of-scope + ≥1 `area:` + `effort:` | `gh issue list --label needs-grooming` empty; script validates body contains `## Goal` etc. |
| `implement issue #N` | SWE | Code committed + tests green + AC checklist commented on issue | `pytest -q` exit 0; `gh issue view N --json body` contains `- [x] AC` lines |
| `qa issue #N` | QA | Issue has `PASS` or `FAIL` comment with logs and verdict | `gh issue view N --json comments` contains `PASS`/`FAIL` + `pytest` log or screenshot |
| `sync tasks` | PM | Issue count == tasks.md count | `gh issue list` count vs `grep -c "^## Task" _docs/tasks.md` |

Harness loops agent until condition true; agent must self-check and continue without asking user.

## 6. Context Loading Rules

- **Every session:** Load `AGENTS.md`, `_docs/plan.md`, `_docs/process.md`.
- **Dynamic by label/file:**
  - `area:ui` or touching `templates/`, `static/` → load `_docs/design-system.md`
  - `area:testing` or touching `tests/` → load `_docs/testing-guidelines.md`
  - `area:infra` or touching `Dockerfile`, `docker-compose.yml` → load stack decision §4.8
- Before editing `_docs/*`, read the file; after correction, update it so next session benefits.

## 7. Quality Gates

- **Lint:** `ruff check .` must pass (no errors).
- **Type:** `mypy .` must pass (strict for `core/`, `chores/services/`).
- **Unit coverage:** `pytest --cov --cov-fail-under=80` for domain logic.
- **E2E:** `npx playwright test` for J1/J2/J3; tagged `e2e` tests run nightly or on `qa` label.
- **Perf/a11y:** Lighthouse ≥90 (perf), Axe 0 violations.

## 8. Meetings & Cadence (Async-friendly)

- **Daily triage (PM 10m):** Run `/goal groom`, label new issues.
- **Weekly sync:** `/goal sync tasks`, review milestone burndown in `tasks.md`.
- **PR review SLA:** SWE opens → QA within 24h.

## 9. Exceptions & Escalation

- Ambiguous AC → SWE adds `question` label, blocks, pings PM in issue; do not unblock by assumption.
- Stack deviation (e.g., adding React) → requires ADR update in `_docs/stack-decision.md` + PM approval.
- Security incident → open `priority:critical` bug, notify PM, do not wait for groom.
