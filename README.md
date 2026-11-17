# Supr | BMU Campus Market

Supr is a BMU-scoped marketplace for student discovery and ordering, vendor onboarding and operations, and University Admin governance. This repository is a greenfield implementation based on SRS v1.0 and the CSE3005 course handout.

## Current scope and open decisions

- Order requests are recorded without online payment.
- Carts are constrained to one vendor by the API and database model.
- Campus delivery is a vendor-declared yes/no value. No charge, zone, or delivery-time rule is assumed.
- Agreement validity is recorded by an administrator. The application does not claim external legal verification.
- Notifications are persisted in-app; email delivery and retry policy are deferred.
- SQLite is the local default. PostgreSQL can be selected through `DATABASE_URL`.

## Run locally

1. Create and activate a Python virtual environment in `backend/`.
2. Install `backend/requirements.txt`.
3. Copy `backend/.env.example` to `backend/.env` and set a unique `SECRET_KEY`.
4. Run `alembic upgrade head` from `backend/`, then `python -m app.seed` to reset and populate the demo database.
5. Run `uvicorn app.main:app --reload` from `backend/`.
6. Install frontend packages with `npm install` in `frontend/`, then run `npm run dev`.

The API docs are at `/docs`. Demo credentials (change before deployment), password `Demo@12345` for each: student `student@supr.bmu.edu.in`; admin `admin@supr.bmu.edu.in`; vendors `lazeez@supr.demo`, `kathijunction@supr.demo`, `greenox@supr.demo`, `dominos@supr.demo`. The seed creates the four vendors as pending; approve them from the admin Applications view.

To add the Domino's menu to an existing database without resetting it, run `python -m app.import_dominos` from `backend/`. After changing backend code, restart Uvicorn: `--reload` has not always picked up edits on Windows.

## Laptop and phone shops

`python -m app.import_tech_vendors` (from `backend/`) adds six nearby repair and sales shops found in public listings. They are shown as **listed** shops: visible with contact details, but they cannot take orders until they join. Sources and rules are in `docs/TECH_SHOPS_REPORT.md`.

## Dish photos

`python -m app.dish_photos` (from `backend/`) fetches one credited Unsplash photo per dish type and diet (about 35 cover the whole menu). Use `--dry-run` to preview, `--redo "pizza|vegetarian"` to replace one. Unsplash allows 50 requests an hour, so it stops partway; run it again later to finish.

## Menu photos from Unsplash

Items without a vendor photo can show an illustrative photo for their menu section, credited to the photographer as Unsplash requires. A photo the vendor uploads always replaces it.

1. Create a free app at https://unsplash.com/oauth/applications and copy its **Access Key**.
2. Add `UNSPLASH_ACCESS_KEY=<your key>` to `backend/.env` (git-ignored; keep the key private).
3. From `backend/`, run `python -m alembic upgrade head` once, then `python -m app.import_unsplash_photos`. Use `--dry-run` to see the planned searches, `--refresh` to replace every photo, or `--redo "Vendor/Section"` to replace one section's photo. Sections that mix veg and non-veg items get one photo per diet.

New Unsplash apps allow 50 requests per hour and each section uses two, so the import stops partway; run it again after an hour to finish the remaining sections.

## Tests

From `backend/`, with the virtual environment's Python (`.venv311/Scripts/python.exe` on this machine):

- `python -m pip install -r requirements-dev.txt` installs the test and security tools.
- `python -m pytest tests -q` runs the API and security tests against a throwaway test database.
- `python -m bandit -r app` and `python -m pip_audit -r requirements.txt` run the security scans; `npm audit` in `frontend/` checks frontend packages.

From the project root, `backend/.venv311/Scripts/python.exe -m pytest e2e -v` runs the browser tests. They start their own backend (port 8101) and frontend (port 5181) on a temporary seeded database and drive the installed Microsoft Edge; set `E2E_BROWSER_CHANNEL=chrome` to use Chrome, or `E2E_HEADED=1` to watch.

From the project root, `backend/.venv311/Scripts/python.exe perf/load_test.py` runs the performance test on its own temporary backend (about 4 minutes); set `SUPR_WORKERS=4` to try several server processes.

## Repository map

- `backend/app/`: API, database models, schemas, auth, policy and seed.
- `frontend/`: React + TypeScript marketplace and role workspaces.
- `docs/`: traceability, architecture/design, project planning and quality records.
- `backend/tests/`: executable API and business-rule tests.

## Verification status

See `docs/COMPLETION_REPORT.md`. A capability is marked complete only when implemented; test status is reported only after execution. No deployment, external legal verification, email provider, or payment integration is included.

## Deploying

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the Render (backend and database) and Vercel (website) steps.
