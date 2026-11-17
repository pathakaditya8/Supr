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

