# Team work split by website module: Aakriti, Dhruv, Aditya and Anshika

The project's planned effort is 108 person-days (see `PROJECT_PLAN.md`). It is divided here **by module of the website**, into four equal shares of **27 person-days** each. A member who owns a module owns it end to end: requirements, screen, API, database, tests and the documents about it. That way each person can explain and demonstrate a complete part of the software in the viva, which the handout grades through questions on the work presented.

This is a **plan for who owns what**, not a record of who did what, so it claims no hours already worked. Actual hours go in [`PROJECT_TRACKING.md`](PROJECT_TRACKING.md).

## 1. Shares at a glance

| Member | Modules owned | Planned person-days | Share |
|---|---|---:|---:|
| Aakriti | M3 Marketplace and discovery, M7 Look, language and content, plus 1 day of test and project evidence | 27 | 25% |
| Dhruv | M1 Accounts and access, M2 Vendor onboarding and approval | 27 | 25% |
| Aditya | M5 Cart, orders and tracking, M8 Data, deployment and operations, plus 2 days of security checks | 27 | 25% |
| Anshika | M4 Vendor shop management, M6 Admin console, plus 3 days of test and project evidence | 27 | 25% |
| **Total** | | **108** | **100%** |

## 2. The modules

| Module | What it covers in the website | Days | Owner |
|---|---|---:|---|
| **M1 Accounts and access** | Sign-in and sign-out, student self sign-up (name.yearcourse@bmu.edu.in), vendor registration form, roles and what each role may open, My profile, change password, admin sets another person's password | 12 | Dhruv |
| **M2 Vendor onboarding and approval** | Vendor application form and documents, Applications tab, approve or reject with agreement validity and remarks, stop and restart a vendor, Approval history and per-vendor timeline, "registered, not applied yet" list, admin notifications | 15 | Dhruv |
| **M3 Marketplace and discovery** | Landing page and shop listing, Menu, Discover and Vendors pages, the Tech page and listed shops, search, filters and sorting, product cards and detail, Favourites | 16 | Aakriti |
| **M4 Vendor shop management** | Vendor dashboard, adding and editing listings, item photos, stock and bulk in or out of stock, delivery places and the "All campus places" option, vendor orders screen and the order details dialog | 14 | Anshika |
| **M5 Cart, orders and tracking** | One-vendor bag and Clear bag, review and place order, server-side prices, stock locking, order lifecycle and delivery stages, Your orders, Order history, student and vendor order notifications | 17 | Aditya |
| **M6 Admin console** | Admin overview and counts, Students (add, remove, temporary password with show or hide), Food listings and Tech listings pages, admin add or edit of listings, notifications | 10 | Anshika |
| **M7 Look, language and content** | Brand, logo and door intro, header and footer, English and Hindi switch, dark mode, About, Help and How it works, responsive layouts, dish and shop photo system (credited Unsplash photos) | 10 | Aakriti |
| **M8 Data, deployment and operations** | Database models and migrations, menu and shop imports, `copy_data` and `sync_photos`, Render and Vercel setup, keep-awake ping, backups | 8 | Aditya |
| **M9 Test and project evidence** | Central test plan and traceability, security scans, lint, planned-versus-actual tracking, burndown and retrospectives | 6 | Anshika 3, Aditya 2, Aakriti 1 |
| | **Total** | **108** | |

Every module owner also writes the tests and updates the documents for their own module; that effort is already inside each module's days.

## 3. Where each module lives in the code

| Module | Backend (`backend/app/main.py` and related) | Website (`frontend/src/App.tsx`) | Tests |
|---|---|---|---|
| M1 | `/api/auth/*`, `/api/student/profile`, `/api/admin/users/{id}/password` | `AuthModal`, `StudentProfile`, `AccountProfile`, `PasswordCard`, `AdminResetPassword` | `test_security.py` (registration, passwords), E2E 1, 7, 12 to 15, 17, 19, 23 |
| M2 | `/api/vendor/applications*`, `/api/admin/applications`, `/decision`, `/participation`, `/api/admin/history` | `VendorApplication`, `AdminApplications`, `AdminHistory`, `VendorHistoryToggle` | `test_security.py` (history, new vendor), E2E 4, 21, 24 |
| M3 | `/api/products`, `/api/vendors`, `/api/categories`, `dish_photos.py` queries | Landing page, `TechPage`, `VendorMenu`, `ProductCard`, `ProductDetail`, `SavedItems` | `test_search.py`, `test_listed_shops.py`, E2E 6, 8, 11, 28 |
| M4 | `/api/vendor/products*`, `/api/vendor/delivery-points`, bulk availability, product images | `VendorDeliveryManager`, `BulkAvailabilityBar`, `VendorPhotoButton`, vendor listing screens | `test_api.py`, E2E 5, 16 |
| M5 | `/api/cart*`, `/api/orders*`, arrival and status updates | The bag, `OrderTracker`, `StudentActiveOrders`, `StudentOrderHistory` | `test_order_tracking.py`, `test_api.py`, E2E 2, 3, 20, 22, 27 |
| M6 | `/api/admin/metrics`, `/api/admin/students`, `/api/admin/listings` | `AdminStudents`, `AdminProductForm`, admin listing tabs | `test_security.py` (listings split), E2E 25 |
| M7 | `dish_photos.py`, `vendor_images.py`, `import_unsplash_photos.py` | `SuprLogo`, `DoorIntro`, `DishPhoto`, `i18n.ts`, `styles.css`, About | `test_dish_photos.py`, `test_section_photos.py`, E2E 9, 10, 29, 30 |
| M8 | `models.py`, `migrations/`, `seed.py`, `import_*.py`, `copy_data.py`, `sync_photos.py`, `keepalive.py`, `render.yaml` | `vercel.json` | `test_security.py` (keep-alive) |
| M9 | `ruff.toml`, scans | `eslint.config.js` | `perf/load_test.py`, `docs/TEST_PLAN.md` |

## 4. Open work, by module

| Module | Open item | Owner |
|---|---|---|
| M1 | Email verification or a BMU student list so that sign-up can prove ownership of an address; a "forgot password" that does not need the admin | Dhruv |
| M2 | Run the elicitation questionnaire and vendor and admin interviews and write the findings; vendor terms confirmation screen | Dhruv |
| M3 | Fix the 320 px home page overflow; add more photo variety per dish type | Aakriti |
| M4 | Vendor analytics (charts and an exportable report); import the Greenox menu once the vendor supplies it | Anshika |
| M5 | Live order-status refresh for the vendor without reloading; decide delivery charges and zones | Aditya |
| M6 | Admin charts and exportable reports; admin screens for the 25 open lint findings | Anshika |
| M7 | Fetch the remaining 11 dish photos and replace the headphones photo; check Hindi wording with a native speaker | Aakriti |
| M8 | Rotate the exposed database password; upgrade or export the free Render database before its 30-day expiry; custom domain | Aditya |
| M9 | Fill the time log, planned-versus-actual table and burndown; hold sprint retrospectives | Anshika |

## 5. Shared duties

- Every member reviews at least one other member's change before it is merged.
- Every member records their own hours weekly in the time log.
- For the viva, each member prepares to explain and demonstrate their own modules, and everyone can walk through one full journey: a student order, a vendor fulfilling it, and the admin approving a vendor.

## 6. If the split needs to change

Move whole modules or items between members, keep each member at 27 days, and update the tables here and in `PROJECT_TRACKING.md`.
