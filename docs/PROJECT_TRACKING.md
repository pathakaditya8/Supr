# Project tracking: sprints, planned vs actual, monitoring

This file is the record for the handout topics "Agile sprint planning and implementation" and "monitoring and control". It separates **what the repository proves** (dates and deliverables from files, commits and test runs) from **what only the team can supply** (hours worked, who did what, retrospective opinions). Cells marked `TEAM` must be filled in from real records. Nothing in them has been estimated or invented.

## 1. What the repository shows

| Date | Evidence |
|---|---|
| 2026-11-14 | First database backups; the full Lazeez and Kathi Junction menus were already loaded (`supr.db.backup-before-full-menu-20261114`). |
| 2026-11-15 | Vendor-managed menu status introduced (`supr.db.backup-after-vendor-managed-menu-status-20261115`). |
| 2026-11-17 | Domino's import, item photos, bulk in/out-of-stock, favourites, order tracking, section and dish photos, Tech page and listed shops, new landing page, About, language switch, door intro, logo; migrations 0008 to 0012; tests grew to 62 API and 13 browser tests. |
| 2026-11-17 | Project pushed to GitHub (`1fcb3bc`), then `PRODUCT.md` (`5f78a2b`). Earlier history is only the single "Initial commit". |

The Git history is too short to reconstruct sprints. Database backup dates and the migration sequence (0001 to 0012) are the only earlier timeline. For a stronger record, commit per sprint from now on.

## 2. Sprints: plan vs delivered

Planned goals are from `PROJECT_PLAN.md`. "Delivered" states what the repository now contains for that goal. "Dates" and "Retrospective" need the team.

| Sprint | Planned goal | Delivered (from repository) | Dates | Retrospective (went well / change next) |
|---|---|---|---|---|
| 0 | Baseline SRS, MoSCoW, architecture, repo setup | `REQUIREMENTS.md`, `ARCHITECTURE.md`, `OPEN_DECISIONS.md`, repository and tooling | TEAM | TEAM |
| 1 | Roles, secure auth, vendor application | Argon2 and signed tokens; roles; application with documents (T-AUTH-01, T-ROLE-01, T-GOV-01) | TEAM | TEAM |
| 2 | Admin review, audit, catalogue, listings | Decisions with remarks and history; search, filter, sort; vendor listing management | TEAM | TEAM |
| 3 | Cart, order, fulfilment | One-vendor cart, server-side prices, order lifecycle (T-ORD-01, T-ORD-02) | TEAM | TEAM |
| 4 | Dashboards, notifications, analytics, UX | Role dashboards, notifications; later: favourites, order tracking, Tech page, landing page, language switch | TEAM | TEAM |
| 5 | Verification, security, performance, docs | 62 API and security tests, 13 browser tests, load test, Bandit, pip-audit, npm audit, linters, documents | TEAM | TEAM |

Product backlog items still open: vendor terms screen, charts and report export, Greenox menu, higher-resolution Lazeez photo, more photo variety per dish.

## 3. Planned vs actual effort

Planned effort is from `PROJECT_PLAN.md` (108 person-days; 432 person-hours of capacity). Fill the **Actual** column from the team's own time log, then compute the variance.

| WBS | Work package | Planned (person-days) | Actual (person-days) | Variance % | Reforecast needed (> 20%)? |
|---|---|---:|---|---|---|
| 1 | Scope, SRS, elicitation, MoSCoW | 10 | TEAM | | |
| 2 | Architecture, ER/UML/DFD, plan | 9 | TEAM | | |
| 3 | Database, identity, governance | 17 | TEAM | | |
| 4 | Marketplace and listings | 14 | TEAM | | |
| 5 | Cart, checkout, orders | 15 | TEAM | | |
| 6 | React workspaces and integration | 18 | TEAM | | |
| 7 | Verification, fixes, security | 15 | TEAM | | |
| 8 | Course evidence, setup, demo | 10 | TEAM | | |
| | **Total** | **108** | TEAM | | |

Variance % = (Actual − Planned) ÷ Planned × 100.

Scope added beyond the original plan, which explains part of any overrun and should be listed as scope change: Domino's menu import, item photos and the Unsplash photo system, bilingual interface, Tech page and listed shops, order tracking and history, new landing page and brand work.

## 4. Burndown

Record remaining work at the end of each sprint (person-days) and chart it.

| End of sprint | Remaining planned work | Ideal remaining |
|---|---:|---:|
| 0 | TEAM | 90 |
| 1 | TEAM | 72 |
| 2 | TEAM | 54 |
| 3 | TEAM | 36 |
| 4 | TEAM | 18 |
| 5 | TEAM | 0 |

## 5. Issue and risk log (monitoring)

Defects and risks that actually occurred in this project, with how each was found and handled:

| ID | Item | Found by | Resolution |
|---|---|---|---|
| I-1 | Search for `%` or `_` matched the whole menu | Test-first cycle (`AI_ENGINEERING.md`) | LIKE escaping; regression test |
| I-2 | Product listing issued about 100 queries per page | Load test | `selectinload` and per-request caches; 9 queries per page, throughput more than doubled |
| I-3 | Admin listings hidden after the Domino's import (cap 250) | Manual check | Cap raised to 2000 |
| I-4 | Database CHECK constraint blocked the new tech categories | Import failure | Migration 0010 rebuilt the table |
| I-5 | Bulk availability returned 405 | Manual check | Stale server; restart after backend edits |
| I-6 | Heart buttons stacked at the top of cards | Visual check | Missing `position: relative` |
| I-7 | Header overflow at several widths | Browser checks | Media queries from 360 px up; the 320 px home page still overflows slightly |
| I-8 | Unsplash API allows 50 requests per hour | Fetch run | Resumable importer, photos grouped by dish type |
| I-9 | Frontend dev server stopped proxying `/api` after a package install, so the site showed "Unexpected end of JSON input" | User report | Dev server restarted; restart it after installing packages |
| R-1 | Greenox site blocks automated access, so no menu | Import attempt | Open; needs a menu file from the vendor |
| R-2 | Listed shops have not agreed to appear | Design review | Listed-not-orderable status, no verified badge |

## 6. Review cadence going forward

At the start of each sprint: confirm capacity and acceptance criteria. Weekly: update the time log, sections 3 and 4. At the end: retrospective in section 2, and a commit tagged `sprint-N`.
