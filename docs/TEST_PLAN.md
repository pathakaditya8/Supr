# Verification and validation plan

## Test levels

- **Unit:** token signing/expiry, validators, single-vendor/cart and lifecycle policies. Add isolated tests where policy functions are extracted.
- **Integration:** API + relational database for login, application decisions, catalogue filtering, cart constraints, checkout and audit records.
- **System:** browser-to-API student/vendor/admin critical paths using seeded data.
- **Regression:** re-run the named requirements suite after any business-rule or schema change.
- **Performance:** measure catalogue response and checkout under expected small BMU demo load; report environment and p95, do not infer production capacity.
- **Security:** unauthorized role, cross-student order, cross-vendor listing/order, invalid token, upload extension/size and injection-shaped search inputs.
- **Automation:** pytest/FastAPI TestClient for the API and security suites; pytest + Playwright (Microsoft Edge) for browser system tests.

## Current executable API cases

All cases live in `backend/tests/test_api.py` and run against a freshly seeded SQLite test database (`backend/test_supr.db`); uploaded files go to a temporary folder.

| Test ID | Requirement | Test function | What it checks |
|---|---|---|---|
| T-AUTH-02 | FR-01 | `test_change_password_requires_current_password_and_works`, `test_admin_can_set_student_and_vendor_passwords_but_nobody_else_can`, E2E 14, 15, 17, 19 | A wrong current password, a short or unchanged password is refused; the old password stops working; only an admin can set another person's password |
| T-AUTH-03 | FR-01a | `test_student_can_sign_up_only_with_name_yearcourse_bmu_address`, E2E 23 | A valid name.yearcourse@bmu.edu.in address creates a student who can sign in; other formats, other domains, impossible years and duplicates are refused |
| T-GOV-02 | FR-04a | `test_application_needs_at_least_two_delivery_partners`, E2E 26 | A missing, 0, 1, negative, non-number or absurd count is refused and nothing is submitted; 2 is accepted and the admin sees it; the submit button stays disabled below 2 |
| T-AUTH-01 | FR-01 | `test_login_and_invalid_login` | Valid login returns 200; wrong password returns a generic 401 |
| T-GOV-01 | FR-04, FR-05, FR-13 | `test_real_vendor_profiles_are_pending_and_not_public` | All four seeded vendors start as pending applications and no vendor is publicly listed |
| T-MKT-01 | FR-02, FR-10, FR-13 | `test_menu_hidden_until_vendor_approved_then_visible_but_not_orderable` | A pending vendor's menu is hidden (list and detail 404); after approval the menu is visible at zero stock, excluded from in-stock filters and recommendations, cannot be added to a cart; an admin-paused item is hidden again |
| T-MENU-01 | FR-14, FR-15 | `test_imported_menus_are_complete_and_start_out_of_stock` | Lazeez 128, Kathi Junction 72 and Domino's 121 items imported, all published with zero stock; spot-checks exact variant prices, unpriced items, Domino's size/crust prices, name disambiguation and the GST note |
| T-MENU-02 | FR-14, FR-15 | `test_momos_matrix_exact_prices_and_addons_unpriced` | All 24 momo preparation/filling prices; roll add-on prices transcribed and disabled |
| T-ROLE-01 | FR-01, NFR-01 | `test_role_access_control` | A student calling admin and vendor endpoints gets 403 |
| T-ORD-01 | FR-02, FR-07, FR-08, FR-09, NFR-01 | `test_variant_server_price_checkout_and_vendor_isolation` | Price-range and dietary filters; server-side variant price in cart and order; another vendor cannot see the order; the student sees the variant snapshot |
| T-ORD-02 | FR-08, FR-14 | `test_missing_variant_and_unknown_addon_rejected` | Adding a variant product without a variant, or with an unknown add-on, returns 422 |
| T-VEN-01 | FR-06, NFR-01 | `test_vendor_bulk_availability_toggles_only_own_live_items` | "Mark all in/out of stock" updates every live item and its variants, leaves paused items and other vendors' items untouched, and is forbidden to students |
| T-VEN-02 | FR-06, NFR-01 | `test_vendor_uploads_food_photo_and_attaches_it` | A vendor uploads a PNG, it is served publicly and attached to an item; a file whose contents are not an image is rejected with 415 |
| T-SRCH-01 | FR-02 | `test_search_treats_wildcard_characters_literally` (5 cases) | Searching `%`, `_`, `a_b`, `100%` or `%%` returns only items that literally contain the text, never the whole menu. Written test-first; see `AI_ENGINEERING.md` |
| T-SRCH-02 | FR-02 | `test_search_still_finds_ordinary_words` | Ordinary search (`paneer`) still works after the fix |
| T-IMG-01 | FR-03 | `test_item_without_photo_shows_credited_section_photo` | An item without its own photo returns its section's Unsplash photo, marked illustrative, with photographer and Unsplash links carrying the required referral parameters |
| T-IMG-02 | FR-06 | `test_vendor_photo_always_wins` | A vendor-uploaded photo replaces the section photo and carries no stock credit |
| T-TRK-01 | FR-09 | `test_campus_delivery_goes_out_for_delivery_then_completes` | A campus delivery order moves ready → out for delivery → gate arrival → completed; the student's notifications use plain wording, never raw status codes |
| T-TRK-02 | FR-09 | `test_pickup_order_cannot_be_marked_out_for_delivery` | A pickup order cannot be marked out for delivery (409) |
| T-TRK-03 | FR-09 | `test_on_the_way_order_counts_as_active` | An order on the way still counts as in progress in the student's summary |
| T-LIST-01 | FR-16 | `test_tech_categories_exist` | The four laptop and phone categories exist |
| T-LIST-02 | FR-16 | `test_listed_shops_are_public_and_clearly_labelled` | All five listed shops are public, say they have not joined Supr, have nothing orderable, and expose phone and address |
| T-LIST-03 | FR-16 | `test_only_published_prices_are_shown` | Published prices (₹17,000, ₹500) appear; unpublished ones stay empty |
| T-LIST-04 | FR-16, NFR-01 | `test_listed_shop_cannot_take_orders` | Adding a listed shop's item to a cart is refused with an explanation |
| T-LIST-06 | FR-16 | `test_food_and_tech_items_can_be_listed_separately` | `kind=food` returns only food categories and `kind=tech` only the 34 laptop and phone listings |
| T-LIST-05 | NFR-01 | `test_nobody_can_sign_in_as_a_listed_shop` | Listed shops' placeholder accounts are disabled and cannot sign in |
| T-IMG-03 | FR-03 | `test_dish_keys_group_by_type_and_keep_diet` | Dishes group by type and diet; veg dishes never map to a non-veg photo |
| T-IMG-04 | FR-03, FR-06 | `test_item_gets_credited_dish_photo_and_own_photo_wins` | An item without a photo gets its dish-type photo with photographer credit; the shop's own photo always wins |
| T-PERF-01 | NFR-04 | `test_section_photos_do_not_add_per_item_queries` | A 48-item page loads section photos in one query and uses fewer than 20 queries in total (it was 101 before the fix) |

Acceptance cases still needed: invalid registration fields beyond password length, application document MIME/size (photo uploads are covered), inventory race under real concurrency, notification creation per event, and audit-log assertions.

## Security tests (`backend/tests/test_security.py`)

29 automated cases (some parameterised) that attack the API the way a curious or malicious user would:

| Test ID | Area | What it checks |
|---|---|---|
| T-SEC-01 | Registration | Self-registration cannot create admin or student accounts; weak passwords and duplicate emails are refused |
| T-SEC-02 | Tokens | A token whose role is edited to "admin" is rejected (signature check); garbage and missing tokens get 401; tokens stop working after expiry |
| T-SEC-03 | Accounts | A student removed by an admin can no longer use an existing token |
| T-SEC-04 | Login | Unknown email and wrong password return the identical 401 message, so accounts cannot be discovered |
| T-SEC-05 | Role boundaries | Six admin endpoints refuse students and vendors (403); vendor endpoints refuse students |
| T-SEC-06 | Ownership | One student cannot see or cancel another student's order |
| T-SEC-07 | Ownership | One vendor cannot edit, delete or change variants of another vendor's item, or update or see another vendor's order |
| T-SEC-08 | Ownership | A user cannot mark someone else's notification as read |
| T-SEC-09 | FR-07 | The cart refuses a second vendor's item (409) |
| T-SEC-10 | FR-10 | A stopped vendor's items disappear and checkout from them is refused |
| T-SEC-11 | FR-09 | Order status cannot skip steps; students cannot cancel once accepted |
| T-SEC-12 | FR-08 | Cancelling an order puts the stock back |
| T-SEC-13 | Price tampering | Extra price fields sent by the client are ignored; the server price is charged |
| T-SEC-14 | Injection | SQL- and script-shaped search terms return 200 with no results and leave the data intact |
| T-SEC-15 | Uploads | PHP, SVG, mislabelled and over-5 MB files are refused; a `../../` file name is replaced by a random name |
| T-SEC-16 | Path traversal | The public image route refuses `../` and non-image names |
| T-SEC-17 | Error leakage | Error replies contain no tracebacks, SQL, password hashes or secrets |

## Static analysis and dependency scans (2026-11-17)

| Tool | Scope | Result | Action |
|---|---|---|---|
| Bandit 1.9.4 (`python -m bandit -r app`) | 1,287 lines of backend code | 0 high, 0 medium, 2 low | Both lows are false positives: B105 flags the literal `"bearer"` (the OAuth token type) as a possible password. No change needed |
| pip-audit 2.10.1 (`python -m pip_audit -r requirements.txt`) | Backend dependencies | 1 advisory: PYSEC-2026-1845 in pytest 8.4.2 (shared `/tmp` directory on UNIX allows local denial of service) | Test-only dependency and not exploitable on this Windows setup, but fixed anyway: requirement raised to `pytest>=9.0.3,<10`; re-scan reports no known vulnerabilities; all tests still pass |
| npm audit | Frontend dependencies | 0 vulnerabilities | None |

## System tests in a browser (`e2e/test_e2e.py`)

Playwright drives the installed Microsoft Edge (headless) against an isolated stack: `e2e/stack.py` seeds a throwaway database in a temporary folder and starts the backend on port 8101 and the frontend on port 5181, so the real database is never touched. Run from the project root with `backend/.venv311/Scripts/python.exe -m pytest e2e -v`.

| Test ID | Journey | What it checks |
|---|---|---|
| T-E2E-01 | Sign-in | A wrong password shows the error and no workspace opens |
| T-E2E-02 | Order to fulfilment | Student signs in, opens Kathi Junction from the Vendors page, adds an item, places the order; the vendor accepts it and marks it preparing; the student's tracker shows "Being prepared" with two steps done; after the vendor marks it ready and collected it moves to Order history as "Collected" |
| T-E2E-03 | One-vendor bag | Adding a second vendor's item asks before clearing the bag; Cancel keeps the original item, OK restarts the bag with the new vendor |
| T-E2E-04 | Vendor approval | The admin approves Greenox from Applications; Greenox becomes public and the approval is in the history |
| T-E2E-05 | Bulk stock | Domino's marks all 121 items out of stock, then back in stock; the public in-stock count follows |
| T-E2E-06 | Favourites | A student hearts an item (the heart must sit inside its own card) and finds it in the Favourites tab |
| T-E2E-07 | Role UI | A student sees no admin or vendor tabs |
| T-E2E-08 | Pages | A visitor sees Join the marketplace beside Explore food; Menu, Discover and Vendors are separate pages; menu cards show name tiles and no images; the header is sticky |
| T-E2E-10 | Language | Switching to Hindi translates navigation, buttons and headings (including pages opened afterwards), is remembered after reload, and switching back restores English |
| T-E2E-11 | Tech page | Menu has no laptop or phone categories; the Tech page lists services without veg labels, offers Details instead of ordering, filters by category, and shows the five shops |
| T-E2E-12 | Sign out | Signing out from the account dropdown ends the session |
| T-E2E-13 | Account menu | Signed out, the Account menu offers Sign in and Join the marketplace (no Sign out), and Sign in opens the sign-in form |
| T-E2E-09 | Intro | The door animation shows on load, removes itself within seconds, and plays again after a refresh |

**Defect found by system testing:** every menu card's heart (favourite) button was positioned against the page instead of its own card, so all hearts stacked in one corner and a click saved whichever item's heart happened to be on top. Fixed by giving `.product-card` `position: relative`; T-E2E-06 now asserts the heart lies within its card.

## Performance and concurrency testing (`perf/load_test.py`)

**Method.** The script starts an isolated backend on a freshly seeded temporary database, creates throwaway student accounts, and runs three scenarios for 15 seconds at each load level of 1, 10, 25 and 50 simultaneous users: **browse** (catalogue pages, search, category and vendor menus, item detail), **login** (Argon2 password check), and **order** (clear cart, add an item, place the order). It reports the 50th, 95th and 99th percentile response time, throughput and errors, then runs a **last-item race**: 30 students hold the same item (stock 5) and all check out at the same instant. Run with `backend/.venv311/Scripts/python.exe perf/load_test.py`; raw results are saved in `perf/results-*.json`.

**Environment.** Windows 11 laptop, 16 logical CPUs, Python 3.11.9, Uvicorn, SQLite file database; load generator on the same machine. Absolute numbers are for this machine only.

**Targets (assumed, not agreed with stakeholders).** For a single-campus marketplace, 25 simultaneous active users is taken as a lunchtime peak. Targets at that level: 95th percentile browse under 500 ms, login under 1,500 ms, order under 1,000 ms, and no errors.

**Results: 95th percentile response time in ms (errors in brackets)**

| Scenario | Users | Run 1: baseline, 1 worker | Run 2: after query fix, 1 worker | Run 3: after fix, 4 workers |
|---|---:|---:|---:|---:|
| Browse | 1 | 98 | 55 | 38 |
| Browse | 10 | 708 | 467 | 119 |
| Browse | 25 | 1,607 | 736 | **292** |
| Browse | 50 | 2,988 | 1,287 | 627 |
| Login | 1 | 75 | 59 | 61 |
| Login | 25 | 1,025 | **1,086** | 1,241 |
| Login | 50 | invalid (machine paused mid-run) | 2,766 | 2,233 |
| Order | 1 | 91 | 30 | 32 |
| Order | 10 | 1,067 | 651 | 681 |
| Order | 25 | 2,003 | 1,476 | 2,832 (4 errors) |
| Order | 50 | 3,027 | 2,210 | 30,131 (27 errors) |
| Browse throughput, 25 users | | 20 req/s | 47 req/s | 163 req/s |

**Last-item race (all runs):** 30 buyers, stock 5 → exactly 5 orders created, 25 refused with 409, final stock 0, **no overselling**. The conditional stock update in checkout works under real concurrency.

**Findings and actions**

1. **Bottleneck found and fixed (perfective maintenance).** Listing products ran two extra database queries per item to load its variants and add-ons (the "N+1 query" problem): about 34 ms for a 24-item page. The four product-list endpoints now load these for the whole page in two queries (`selectinload`). A page now takes about 14 ms, browse throughput more than doubled, and the 25-user browse p95 fell from 1,607 ms to 736 ms. All 45 API tests still pass.
2. **Single server process is the remaining limit.** With one Uvicorn worker, throughput levels off at about 25–47 requests per second. With 4 workers, browsing meets its target easily (292 ms at 25 users).
3. **SQLite cannot handle concurrent writes from several processes.** With 4 workers, ordering under load produced HTTP 500 errors ("database is locked") and 30-second timeouts. SQLite allows one writer at a time. Recommendation for deployment: PostgreSQL (already supported through `DATABASE_URL`) before running more than one worker. This was not tested here.
4. **Login is CPU-bound by design.** Each Argon2 password check takes about 55 ms, which caps a single worker at about 25 logins per second. This is deliberate protection against password guessing; at 25 users the p95 (about 1.1 s) meets the target.

**Against the targets at 25 users (deployed configuration of 1 worker, run 2):** browse **fails** (736 ms against 500), login **passes** (1,086 against 1,500), order **fails** (1,476 against 1,000). With 4 workers browse passes but ordering fails with errors, so the recommended next step is PostgreSQL plus several workers, then repeat this test.

## Test report

| Date | Command (from `backend/`) | Result |
|---|---|---|
| 2026-11-14 | `python -m pytest tests -q` | 5 passed (original five cases) |
| 2026-11-17 | `python -m pytest tests -q` | 6 passed, 2 failed: two tests still expected imported menus to stay hidden until admin publication, which the vendor-managed publishing change had replaced |
| 2026-11-17 | `python -m pytest tests -q` | 10 passed, 0 failed, 1 warning (Starlette TestClient deprecation for `httpx`), 3.3 s. Environment: Windows 11, Python 3.11.9, `backend/.venv311` |
| 2026-11-17 | `python -m pytest tests -q` (API + security) | **39 passed**, 0 failed, 1 warning, about 10 s; same result after upgrading pytest to 9.2.0 |
| 2026-11-17 | `python -m pytest tests -q` | **45 passed** after adding the test-first search tests and the query fix |
| 2026-11-18 | `python -m pytest -q` (backend) and `python -m pytest e2e -q` (project root) | **62 API and security tests passed; 13 browser tests passed** (about 70 s) after the lint fixes. Bandit: 0 high, 0 medium, 2 low (same two false positives); Ruff: 0 findings |
| 2026-11-18 | `python -m pytest -q`; `python -m pytest e2e -q` | **64 API and security tests passed; 15 browser tests passed** after adding password reset (wrong current password, too-short and unchanged password refused; old password stops working; student and vendor flows in the browser) |
| 2026-11-17 | `python -m pytest tests -q` | **48 passed** after adding section-photo tests and the per-request lookup cache |
| 2026-11-17 | `python -m pytest e2e -q` | Two runs while the machine was heavily loaded each had one timeout in a different test; both passed alone. The vendor-opening step now waits for the page to settle and retries, and the default wait is 15 s. Then **7 passed** on three consecutive runs |
| 2026-11-17 | `python -m pytest e2e -v` (from project root) | **7 passed** on two consecutive runs, about 50 s each, Microsoft Edge headless; first run found the heart-button defect above |

**Regression note:** the two stale tests were rewritten to check the current rule (menu visible once the vendor is approved, but not orderable until the vendor stocks it) instead of being deleted. Adding the Domino's menu also exposed a defect: the admin listings endpoint returned only the newest 250 items, hiding older vendors' items once there were 321. The cap was raised and T-MENU-01/T-MENU-02 cover it.

These suites cover API integration, security, browser system and performance testing.
