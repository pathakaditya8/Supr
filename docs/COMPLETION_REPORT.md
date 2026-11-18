# Project completion report

State of the repository on **2026-11-17**. It describes what is implemented and what evidence exists; it is not a claim of production readiness. Test results are reported only from actual runs (see [`TEST_PLAN.md`](TEST_PLAN.md)).

## Product features

| Acceptance area | State | Evidence / remaining gap |
|---|---|---|
| Student/vendor/admin authentication | Completed | Register and sign-in UI and API; Argon2 password hashes; signed expiring tokens. T-AUTH-01 |
| Role-based access | Completed | Role dependencies and owner filters. T-ROLE-01, T-SEC-05 to T-SEC-08, T-E2E-07 |
| Browse/search/filter/sort | Completed | Search, category, price range, dietary, campus delivery and in-stock filters; sort; pagination; product detail dialog. T-ORD-01 |
| Vendor information and delivery | Completed | Vendor cards and pages, delivery points, campus delivery flag, arrival updates. Unconfirmed delivery-terms notes are hidden from students |
| Vendor application and documents | Completed | Application form and supporting-document upload (PDF/PNG/JPEG, 5 MB). T-GOV-01 |
| Admin approval/rejection/agreement recording | Completed | Decision controls with agreement validity and remarks; approval history |
| Vendor listing management | Completed | Create, edit, pause, remove; variants and add-ons; item photo upload from the list and the edit form; mark all items in/out of stock. T-VEN-01, T-VEN-02 |
| Stop/restart vendor participation | Completed | Admin controls in the applications view; recorded in approval history |
| Vendor approval history | Completed | Admin Approval history page: newest first, vendor names, who decided, date and time, remarks and the agreement result; vendor filter; a per-vendor timeline on each vendor card including when the vendor applied (`GET /api/admin/history?vendor_id=`). T-E2E-21 |
| One-vendor cart, checkout, order status | Completed | Server-side prices and variant snapshots; vendor accept/prepare/ready/complete; student cancellation. T-ORD-01, T-ORD-02; covered by browser tests |
| Student favourites | Completed | Heart on menu cards and a Favourites tab (T-E2E-06). Stored per browser (`localStorage`), not per account |
| Student self sign-up | Completed (not email-verified) | Students create their own account with a name.yearcourse@bmu.edu.in address (e.g. dhruv.24cse@bmu.edu.in); the format is checked, ownership of the address is not (no email delivery). Admin-created accounts still work. T-AUTH-03, T-E2E-23 |
| Password reset (signed in) | Completed | Students, vendors and the University Admin can change their own password from My profile (current password required, 10+ characters); `POST /api/auth/change-password`. There is no e-mail "forgot password"; instead the admin can set a new password for any student or vendor (Reset password on the Students list and on each vendor card, `POST /api/admin/users/{id}/password`, recorded in the audit log) and share it securely. T-AUTH-02, T-E2E-14, T-E2E-15 |
| Notifications | Completed | Persisted in-app notifications with unread count and read marking |
| Admin student accounts | Completed | Admin can list, add and remove student accounts |
| Analytics and reports | Partially Completed | Summary metrics for each role; no charts or exportable reports (`recharts` is installed but unused) |
| Vendor terms confirmation | Partially Completed | API exists (`PUT /api/vendor/terms`) but there is no vendor screen to confirm minimum order and delivery terms |
| Menus for the four vendors | Partially Completed | Kolkata's Lazeez (128 items) and Kathi Junction (72) from supplied menus; Domino's (121) from the website on 2026-11-17; **Greenox not imported**. All start at zero stock until each vendor stocks them. See [`MENU_IMPORT_REPORT.md`](MENU_IMPORT_REPORT.md) |
| Database, demo seed and migrations | Completed | SQLite by default, PostgreSQL via `DATABASE_URL`; Alembic migrations 0001–0012; reset seed plus import scripts for Domino's, laptop and phone shops, and photos |
| Laptop and phone shops (Tech page) | Completed | Five public-information shops with status `listed` (visible, never orderable), separate Tech page, category filters. See [`TECH_SHOPS_REPORT.md`](TECH_SHOPS_REPORT.md) |
| Order tracking and order history | Completed | Stage tracker including out-for-delivery for campus delivery; Your orders and Order history pages. T-ORD-01, T-ORD-02 |
| English and Hindi | Completed | Header language switch; menu data stays as entered |
| Dish and shop photos | Partially Completed | Credited Unsplash photos by dish type (laptop and phone services now each have their own photo: 24 different photos instead of 3); shop images for four vendors; 11 of 56 dish photos still to fetch because of Unsplash's 50-per-hour limit. `python -m app.sync_photos` copies fetched photos to the hosted database |
| Online payment, live tracking, native mobile, non-BMU expansion | Not Applicable | Explicitly out of scope (MoSCoW "Won't") |

## Course evidence (CSE3005 handout)

| Handout topic | State | Evidence / remaining gap |
|---|---|---|
| SE concepts, SDLC models, Agile choice, ethics | Completed | [`SDLC_AND_ETHICS.md`](SDLC_AND_ETHICS.md) |
| Requirements: functional, non-functional, MoSCoW, traceability | Completed | [`REQUIREMENTS.md`](REQUIREMENTS.md), [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) |
| Requirement elicitation record | Partially Completed | Plan, questionnaire, interview guides and findings template in [`REQUIREMENT_ELICITATION.md`](REQUIREMENT_ELICITATION.md). **Findings are blank until the team collects real answers** |
| UML use case diagram | Completed | [`diagrams/USE_CASE.md`](diagrams/USE_CASE.md) |
| UML sequence diagrams | Completed | [`diagrams/SEQUENCE.md`](diagrams/SEQUENCE.md): sign-in and role check, placing an order, vendor fulfilment, vendor application and admin approval/stop-restart; traced from the implemented routes |
| DFD context, Level-0 and Level-1 | Completed | [`diagrams/DFD.md`](diagrams/DFD.md): context diagram, Level-0 with 7 processes and 8 data stores, Level-1 for placing orders and for marketplace governance; levels balanced |
| ER diagram | Completed | [`diagrams/ER.md`](diagrams/ER.md): all 14 tables with keys, cardinalities and constraints, checked against the live database |
| Coding standards | Completed (frontend cleanup open) | Ruff configured, 183 findings fixed, 0 remain; ESLint configured, 25 findings (15 errors, 10 warnings) recorded and not yet fixed. See [`QUALITY_MAINTENANCE.md`](QUALITY_MAINTENANCE.md) |
| Unit and integration testing, automation | Completed | 62 API, security and search pytest cases, **62 passed** on 2026-11-18 |
| System, regression, performance, security testing | Completed | System: 13 Playwright browser tests (13 passed on 2026-11-18); security: 29 attack-style tests plus Bandit, pip-audit and npm audit; performance: load test at 1–50 users and a last-item race (no overselling), with a query fix that more than doubled throughput. Two assumed response-time targets are still missed on one worker; see [`TEST_PLAN.md`](TEST_PLAN.md) |
| Effort, cost and time estimation, CPM, PERT | Completed (estimates) | [`PROJECT_PLAN.md`](PROJECT_PLAN.md); PERT network drawn in [`diagrams/PERT.md`](diagrams/PERT.md), critical path 45.0 days, standard deviation 3.24 days |
| Monitoring and control (planned vs actual) | Partially Completed | Template, issue and risk log (10 real items) and burndown table in [`PROJECT_TRACKING.md`](PROJECT_TRACKING.md). **Actual hours are blank until the team enters them** |
| Agile sprint evidence | Partially Completed | Sprint-by-sprint delivered evidence recorded in `PROJECT_TRACKING.md`; **dates and retrospectives need the team**. Git history is only three commits |
| Risk management | Completed | Risk register in `PROJECT_PLAN.md` |
| QA/QC, maintenance types, reverse engineering | Completed | [`QUALITY_MAINTENANCE.md`](QUALITY_MAINTENANCE.md) |
| AI-assisted engineering, human validation, static analysis, TDD | Completed | Validation log, scan results and a recorded red/green/refactor cycle (search wildcard defect) in [`AI_ENGINEERING.md`](AI_ENGINEERING.md) |

## Change log since 2026-11-14

- Domino's menu imported from the website (121 items, 534 size/crust prices); combos, toppings and photos not imported.
- Admin listings cap raised from 250 to 2000 items after the import hid older vendors' items.
- Vendors can upload item photos from the listing and edit form, and mark all items in or out of stock.
- Students have a Favourites tab; the overview shows up to 8 in-stock items with a link to the full menu.
- Internal sourcing and "Manual review" notes are no longer shown to students; vendor descriptions rewritten for customers.
- Larger font sizes across the site for readability.
- Two stale tests rewritten for the current publishing rule; two tests added; suite now 10/10 passing.
- Four UML sequence diagrams added (`docs/diagrams/SEQUENCE.md`).
- Security test suite (29 cases), Bandit/pip-audit/npm audit scans, and 7 Playwright browser tests added; pytest raised to 9.x for advisory PYSEC-2026-1845.
- Fixed by test-first development: searching `%` or `_` matched the whole menu.
- Performance test added (`perf/load_test.py`); fixed an N+1 query problem in product listings (about 2.5× faster pages).
- Illustrative Unsplash photos per menu section, credited to photographers (migrations 0008–0009, `app.import_unsplash_photos`). Mixed veg/non-veg sections get a photo per diet so vegetarian items never show meat; vendor photos always take priority. 14 of 47 photos imported so far (Unsplash allows 50 requests an hour).
- Product listings now take 9 database queries per page instead of about 100 (vendor and category lookups cached per request).
- Home page: below the unchanged hero, a Zomato-inspired listing of all shops (food and laptop/phone) with filter chips (All, Food, Laptops & phones, Delivers to BMU), name-tile cards showing item count, main categories, "from" price (only real prices) and delivery mode. Site-wide type scale aligned to 16px body text (13px minimum). Header fits from 360px phones to wide screens.
- Product cards redesigned with dish photos: items are grouped into about 35 dish types (separately for veg and non-veg), each with a credited Unsplash photo (`app/dish_photos.py`, migration 0012); the name tile remains the fallback. 19 of 35 photos fetched so far (Unsplash allows 50 requests an hour).
- Shop photos and logos (migration 0011, `app/vendor_images.py`, files in `frontend/public/vendors/`): Lazeez storefront and Domino's logo supplied by the project owner; Kathi Junction badge cropped from its supplied menu photo; Hi-Tech Computer and Make My Lappy logos from their own websites. Greenox (site blocks automated access), Shivam, Vislor and AJ Mobile (no own website) keep name tiles.
- About Supr redesigned as one card: short intro, stats panel, four equal feature cards and a note on listed shops.
- Laptop and phone shops have their own **Tech** page; Menu, Discover and Vendors show food only (API `kind=food|tech` filter). The **Account** button always opens a menu: signed out it offers Sign in, Join the marketplace and Help; signed in it ends with **Sign out**.
- Five laptop and phone repair / sales shops near BMU listed from public information (new vendor status `listed`, four new categories, migration 0010): visible with contact details, never orderable, prices only where published. See [`TECH_SHOPS_REPORT.md`](TECH_SHOPS_REPORT.md). Active Menu chip now uses the site's teal.
- New Supr logo (shop front with striped awning and "s.") in the header, footer, door intro and browser tab; **About Supr** section with live vendor and dish counts on the home page; blue category chips on the Menu page.
- The full menu ("Find your next favourite bite") has its own **Menu** page; product cards and the item view show the dish name as a coloured tile instead of photos (vendor and Unsplash photos are no longer shown to students).
- Liquid-glass header that stays fixed while scrolling; the home-page photo zooms slightly on hover.
- **English / हिंदी** language switch in the header (interface text, placeholders and order updates; menu data stays as entered); the choice is remembered.
- Discover and Vendors are now separate pages; visitors get a **Join the marketplace** button beside **Explore food** on the home page.
- Every page load opens with a short shop-doors animation (about 2 seconds; click to skip; off for reduced-motion users).
- Students track each order step by step on **Your orders** (auto-refreshing), with a new **Order history** page; campus deliveries gain an "out for delivery" status. Fixed: Your orders previously showed only the five most recent orders.
- Fixed: favourite (heart) buttons all stacked in one spot instead of sitting on their own cards (found by the browser tests).
- Data flow diagrams redone as context, Level-0 and Level-1; full ER diagram added (`docs/diagrams/ER.md`), replacing the menu-only one, which had a syntax error and never rendered.

## Known issues

- `backend/.venv` points to a Python install that no longer exists; use `backend/.venv311`.
- Uvicorn's `--reload` did not always pick up backend edits on this Windows machine; restart the server after backend changes.
- Performance: on one server process, browsing (736 ms) and ordering (1,476 ms) miss the assumed 95th-percentile targets at 25 users. More workers need PostgreSQL first, because SQLite fails under concurrent writes.
- 2026-11-18: Ruff and ESLint configured and run (backend now clean); PERT diagram, sprint and monitoring record, and elicitation pack added; a stray `except Exception` in token checking narrowed; PRODUCT.md pushed to GitHub. 62 API and 13 browser tests pass.
- 2026-11-18: Reset password card on the student profile and a new vendor profile page (API `POST /api/auth/change-password`); Render and Vercel deployment files, keep-awake ping, and `copy_data` loader. 64 API and 17 browser tests pass; vendors can tick "All campus places" for delivery; admin profile page.
- 2026-11-18: Admin can set a new password for a student or vendor who forgot theirs; show/hide on temporary passwords; vendors can tick "All campus places". 65 API and 19 browser tests pass.
- 2026-11-18: Laptop and phone services get their own photos (22 new rules, 22 photos fetched); `app.sync_photos` copies photos to the hosted database; admin reset-password row fixed to equal button heights.
- 2026-11-18: Fixed a cart bug: removing the last item left the cart tied to its old vendor, so adding from another vendor asked to "clear your existing cart" even though the bag showed 0. Fixed in the remove handler and the add check; API and browser tests added (66 API, 20 browser tests pass).
- 2026-11-18: Approval history rebuilt as a readable timeline with vendor filter and per-vendor history on each vendor card. 67 API and 22 browser tests pass; the bag has a Clear bag button.
- 2026-11-18: Student self sign-up with name.yearcourse@bmu.edu.in; demo-account hint hidden in production builds; work split among four members (`TEAM_WORK_SPLIT.md`). 68 API and 23 browser tests pass.
