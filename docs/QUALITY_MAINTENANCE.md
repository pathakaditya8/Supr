# Quality assurance, maintenance and reverse engineering

## QA and QC

Quality objectives: correct role authorization; understandable, responsive student experience; reliable persistence; auditable governance; maintainable modules; portable modern-browser UI. QA is process-focused: requirement reviews, coding conventions, threat review, peer review, migration review and definition of done. QC is product-focused: execute cases, inspect API responses and database effects, review browser flows, and record defects. A release gate requires critical Must scenarios to pass with no open severe privacy/security defect. Performance targets should be set after expected load is agreed.

## Maintenance plan

| Type | Example | Response |
|---|---|---|
| Corrective | Checkout accepts stale stock | Reproduce, add regression test, fix transaction, record migration if needed |
| Adaptive | BMU changes identity provider or PostgreSQL version | Update integration/config, test compatibility and deployment rollback |
| Perfective | Students need faster catalogue search | Measure query behavior, add index/pagination, compare response metrics |
| Preventive | Authorization logic is repeated in routes | Refactor shared policy, retain tests, review attack surface |

## Reverse engineering

For an inherited Supr deployment, inventory the repository and dependency lockfile; inspect route map and role dependencies; derive an entity-relationship diagram from ORM models and live schema; trace user journeys from API and UI calls; compare observed behavior with requirements; recover undocumented constraints such as order transitions; then produce an architecture and data-flow view with evidence. Confirm inferred behavior with stakeholders before changing data or governance rules. Current weaknesses to revisit include a single API module, token revocation/logout semantics, upload retention, database migration management, and concurrent-stock conflict handling.


## Coding standard enforcement (linters)

Added 2026-11-18. The standard is now checked by tools rather than only described.

| Tool | Command | Configuration | Result on 2026-11-18 |
|---|---|---|---|
| Ruff 0.17.5 (backend) | `python -m ruff check app tests` from `backend/` | `backend/ruff.toml`: pyflakes, pycodestyle, isort, bugbear, pyupgrade, blind-except | First run: 183 findings. After fixing: **0 findings**, 62 tests still pass |
| ESLint 9 + typescript-eslint + react-hooks (frontend) | `npm run lint` from `frontend/` | `frontend/eslint.config.js` | **25 findings: 15 errors, 10 warnings** (see below). Not yet fixed |
| TypeScript compiler, strict mode | `npx tsc -b --noEmit` from `frontend/` | `frontend/tsconfig.json` | 0 errors |

What the backend run changed: 30 import-order, unused-import and similar items fixed automatically; `== True` comparisons in database queries rewritten with SQLAlchemy's `.is_(True)`; two lambda assignments rewritten as functions; and the token check in `security.py` now catches only the malformed-token errors (`ValueError`, `KeyError`, `TypeError`) instead of every exception.

Deliberate rule exceptions in `ruff.toml`, with reasons: B008 (FastAPI's `Depends(...)` in defaults is the documented pattern); E701, E702, E401, E501 (the code base uses compact one-line statements and long lines, which the team has not decided to reformat); E741 (short loop names); E402 and F403 only in `seed.py` and `tests/conftest.py`, which must configure the environment before importing the app.

Open frontend findings: unused variables (a few leftover state hooks in the vendor application form, an unused icon import, two unused helper values), one empty `catch` block, and ten `react-hooks/exhaustive-deps` warnings where effects omit stable function dependencies. None caused a failing test or a known defect, but they are the next cleanup.

`ruff format` was not applied: it would reformat 14 files and make the history harder to read for no behaviour change.
