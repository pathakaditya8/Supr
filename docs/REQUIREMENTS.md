# Supr requirements baseline

## Source precedence

The supplied Supr SRS v1.0 is authoritative for system behavior and its open questions. The CSE3005 July-Dec 2026 handout defines the course learning activities and expected evidence. The user-supplied project brief elaborates implementation scope while preserving those constraints. Hyperpure is a visual reference for commerce hierarchy, catalogue discovery and product cards; its identity and business rules are not copied.

## Stakeholders and functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Authenticate student, vendor and University Admin; enforce role boundaries. | Must |
| FR-01a | Students create their own account with a BMU address of the form name.yearcourse@bmu.edu.in (format checked; admins can still create and remove student accounts). Not verified by email. | Should |
| FR-02 | Browse only available listings from approved, active vendors; search, category/price filter and sort. | Must |
| FR-03 | Display vendor identity and BMU delivery availability at discovery and order review. | Must |
| FR-04 | Accept vendor business application information and supporting documents. | Must |
| FR-05 | Admin reviews application/document evidence; records agreement validity; approves or rejects with remarks and history. | Must |
| FR-06 | Approved vendor creates, edits, pauses and removes permitted listings; manages availability and delivery flag. | Must |
| FR-07 | A student's active cart contains items from one vendor only; enforce server-side. | Must |
| FR-08 | Validate availability and quantity, create a persisted order request transactionally and retain item snapshots. | Must |
| FR-09 | Vendor advances order through a defined fulfilment lifecycle; student sees own history and status. | Must |
| FR-10 | Admin stops and restarts approved vendor participation; record actor, target, action, decision, remarks, timestamp. | Must |
| FR-11 | Persist and display in-app notifications for application and order events. | Should |
| FR-12 | Provide role-limited vendor and admin summaries/reports. | Should |
| FR-13 | Keep source-backed profiles for the four requested vendors and gate publication on vendor approval. | Must |
| FR-14 | Support priced product variants, preparations, portion labels and optional add-ons; recalculate selections on the server and snapshot order prices. | Must |
| FR-15 | Preserve menu import provenance and mark unclear, unavailable, unpriced or unverified data for review rather than guessing. | Must |
| FR-16 | Show nearby laptop and phone repair / sales shops from public information, clearly marked as not on Supr, with contact details and published prices only; refuse orders to them. | Should |
| NFR-01 | Protect passwords, validate requests, prevent cross-role and cross-owner access, avoid sensitive error leakage. | Must |
| NFR-02 | Persist related business records consistently and create orders atomically. | Must |
| NFR-03 | Responsive, clear browser experience with loading/empty/error/confirmation states. | Should |
| NFR-04 | Modular design, common relational database support, paginated/filterable catalogue. | Should |
| NFR-05 | Auditability and privacy through authorization and governance history. | Must |

## MoSCoW

**Must:** role authentication/access, vendor onboarding and decision, approval history, catalogue discovery, listing management, one-vendor cart, order creation and status, delivery disclosure, persistent database, responsive browser UI.

**Should:** in-app notifications, admin/vendor analytics, seeded demo dataset, document download, report history and Docker support.

**Could:** richer catalogue imagery, exportable reports, notification preferences, additional account recovery and administrative search.

**Won't for release 1:** online payments, real-time courier tracking, native mobile app, expansion outside BMU, automated legal-agreement verification, delivery fees/zones, external email notification.

## Traceability matrix (planned against delivered source)

Test IDs refer to [`TEST_PLAN.md`](TEST_PLAN.md). Last runs on 2026-11-17: API and security suite 39 passed; browser suite 7 passed.

| ID | Implementation location | Evidence/status |
|---|---|---|
| FR-01 | `backend/app/main.py` auth routes/dependencies; `security.py`; frontend sign-in and registration | Implemented; tested (T-AUTH-01, T-ROLE-01) |
| FR-02 | `GET /api/products`, `GET /api/products/{id}`, marketplace filters and product detail dialog | Implemented; tested (T-MKT-01, T-ORD-01) |
| FR-03 | `product_out`, vendor public routes, cart and order snapshots; vendor cards and pages | Implemented; checked manually in the browser, no automated test |
| FR-04 | application route, vendor document route and upload form, `VendorApplication`/`VendorDocument` | Implemented; seeded applications tested (T-GOV-01); document upload not yet tested |
| FR-05 | admin application/document/decision routes, approval history, admin decision controls | Implemented; agreement validity is admin-recorded input; tested in the browser (T-E2E-04) |
| FR-06 | vendor product create/update/delete, bulk availability, product photo upload, delivery routes | Implemented; tested (T-VEN-01, T-VEN-02, T-SEC-07, T-SEC-15, T-E2E-05) |
| FR-07 | cart route and one-vendor integrity check; bag asks before switching vendor | Implemented; tested (T-SEC-09, T-E2E-03) |
| FR-08 | checkout and order item snapshots | Implemented; tested (T-ORD-01, T-ORD-02) |
| FR-09 | vendor status transitions, student cancellation, role-filtered orders | Implemented; tested (T-ORD-01, T-SEC-06, T-SEC-11, T-SEC-12, T-E2E-02) |
| FR-10 | participation route, `ApprovalHistory`/`AuditLog`, admin stop/restart controls; admin pause of listings | Implemented; tested (T-MKT-01, T-SEC-10) |
| FR-11 | notification persistence, inbox/read API, header notification panel | Implemented; not yet tested |
| FR-12 | vendor/admin/student metric routes and dashboards | Partial; summary metrics only, no charts or exportable reports |
| FR-13 | vendor approval gates menu visibility; menus start at zero stock | Implemented; tested (T-GOV-01, T-MKT-01) |
| FR-14 | product variants, add-ons, server-side price recalculation and snapshots | Implemented; tested (T-MENU-01, T-MENU-02, T-ORD-01, T-ORD-02) |
| FR-15 | menu provenance in `MENU_IMPORT_REPORT.md`, review notes on items (hidden from students) | Implemented; tested (T-MENU-01) |
| FR-16 | `tech_vendors.py`, `import_tech_vendors.py`, vendor status `listed`, cart refusal, listed-shop UI | Implemented; tested (T-LIST-01 to T-LIST-05) |
| NFR-01 | HMAC signed expiring bearer token, Argon2 password hash, Pydantic validation, role checks, upload type checks | Implemented; tested (T-SEC-01 to T-SEC-17); Bandit, pip-audit and npm audit run on 2026-11-17 |
| NFR-02 | SQLAlchemy relational models, Alembic migrations 0001–0012, transactional checkout | Implemented; checkout tested (T-ORD-01); last-item race tested (no overselling) |
| NFR-03 | responsive catalogue/dashboard views, empty/loading states, larger type | Implemented; main journeys covered by browser tests (T-E2E-01 to T-E2E-07); no mobile-width automated check |
| NFR-04 | FastAPI modules, SQLite/PostgreSQL via `DATABASE_URL`, paginated catalogue | Partial; API is still largely one module (`main.py`) |
| NFR-05 | approval history and audit logs, including bulk availability changes | Implemented; audit entries not yet asserted in tests |

## Course topic evidence

| CSE3005 topic | Project evidence |
|---|---|
| SE concepts, professional responsibility, challenges | `SDLC_AND_ETHICS.md` |
| SDLC models and Agile | `SDLC_AND_ETHICS.md`, `PROJECT_PLAN.md` |
| Elicitation, analysis, functional/non-functional requirements, MoSCoW | This file and `OPEN_DECISIONS.md` |
| Design characteristics, UML use case/sequence, DFD context/level 0/1 | `ARCHITECTURE.md`, `diagrams/USE_CASE.md`, `diagrams/SEQUENCE.md`, `diagrams/DFD.md`, `diagrams/ER.md` |
| Coding guidelines, verification/validation, test levels/automation | `TEST_PLAN.md`, source formatting and `backend/tests/` |
| Monitoring/control, cost/effort/time, CPM, PERT | `PROJECT_PLAN.md` |
| QA/QC, maintenance, reverse engineering | `QUALITY_MAINTENANCE.md` |
| AI-assisted engineering, human validation, static/security analysis, AI-TDD | `AI_ENGINEERING.md` |

