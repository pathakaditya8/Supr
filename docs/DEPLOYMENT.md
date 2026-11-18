# Deploying Supr: Render (backend and database) and Vercel (website)

```
Browser ──► Vercel (React site) ──/api/* rewritten──► Render web service (FastAPI) ──► Render PostgreSQL
```

The browser only ever talks to the Vercel address. Vercel forwards `/api/...` calls to Render, so there is no cross-site traffic and no cookie or CORS trouble.

You will create the Render and Vercel accounts and enter any passwords yourself.

## What was changed to make this possible

- `DATABASE_URL` values beginning `postgres://` or `postgresql://` are accepted (`backend/app/config.py`); the PostgreSQL driver `psycopg` is in `requirements.txt`.
- Uploaded vendor documents and food photos are stored **in the database** (`stored_files` table, migration 0013) instead of on disk, because Render's disk is erased on every deploy and restart. Files already saved on disk are still readable.
- `render.yaml` describes the backend service and the database; `frontend/vercel.json` builds the site and forwards `/api`.
- `python -m app.copy_data` copies the catalogue from your local database into the hosted one and replaces the demo passwords.
- Tables are created automatically on first start (`create_all` in the app start-up), so no migration command is needed on a new database.

Not run against a real PostgreSQL server here (none is installed). The copy script was tested SQLite to SQLite and the PostgreSQL driver and URL handling were checked. The first deploy is therefore the real PostgreSQL test; steps 4 and 5 below tell you what to look for.

## 1. Put the code on GitHub

Already done: https://github.com/pathakaditya8/Supr. Push the latest commit before you deploy (Render and Vercel build from GitHub).

## 2. Backend and database on Render

1. Sign in at <https://render.com> (GitHub sign-in is simplest and lets Render see the repository).
2. **New → Blueprint**, choose the `Supr` repository. Render reads `render.yaml` and proposes a web service `supr-api` and a PostgreSQL database `supr-db`.
3. When asked for `ALLOWED_ORIGINS`, enter any placeholder such as `https://example.vercel.app` for now. You fix it in step 5.
4. Click **Apply** and wait for the first build and deploy (a few minutes).
5. Open `https://supr-api.onrender.com/api/health` (use the address Render shows). It should say `{"status":"ok"}`. If the name `supr-api` was taken, Render adds a suffix, so copy the real address.

Free plan facts: the web service sleeps after about 15 minutes without visits, and the first request afterwards takes roughly 30 to 60 seconds. The free PostgreSQL database expires after 30 days. For a demo this is fine; for real use choose paid plans in the dashboard.

## 3. Load the menus into the hosted database

Do this once, on your own computer, with the database's **External Database URL** from the Render dashboard (database → Connections). Treat that URL as a password; do not paste it into chat or commit it.

PowerShell, from the `backend` folder:

```powershell
$env:TARGET_DATABASE_URL = "paste-the-external-database-url"
$env:ADMIN_PASSWORD = "choose-a-strong-password-of-12-or-more-characters"
.venv311\Scripts\python -m app.copy_data
```

The script prints the row counts and, once, a new random password for each vendor account. Keep these safe and hand each vendor only their own. It copies the catalogue (menus, photos, vendors, listed shops) but not test orders, carts or notifications. It refuses to run if the target already has users.

Check: `https://<your-render-address>/api/vendors` should now list the vendors.

## 4. Website on Vercel

1. In `frontend/vercel.json`, replace `REPLACE-WITH-YOUR-RENDER-URL.onrender.com` with your real Render host name (no `https://` in that part, keep the rest of the line), then commit and push.
2. Sign in at <https://vercel.com>, **Add New → Project**, import the `Supr` repository.
3. Set **Root Directory** to `frontend`. Vercel detects Vite; the build command is `npm run build` and the output folder is `dist` (both are also set in `vercel.json`). No environment variables are needed.
4. **Deploy**. Vercel gives you an address such as `https://supr-xxxx.vercel.app`.

## 5. Tell the backend about the website address

In Render → `supr-api` → Environment, set `ALLOWED_ORIGINS` to your Vercel address (exactly, with `https://` and no trailing slash). Save; Render redeploys. Because the browser calls the site's own `/api`, this mainly protects against other websites calling your API.

## 6. Check it works

- Open the Vercel address: the door animation, then vendors and menus.
- Sign in as admin (`admin@supr.bmu.edu.in` with your `ADMIN_PASSWORD`).
- Sign in as a vendor with the password printed in step 3, stock an item, upload a photo, then reload and confirm the photo is still there. This confirms uploads survive restarts.
- Create a student account from the admin screen, sign in as that student and place a test order.

If the page shows "Unexpected end of JSON input" the backend was asleep or unreachable: wait a minute and reload, then check `/api/health` on the Render address and the rewrite address in `vercel.json`.

If Render's log shows a PostgreSQL error on start-up, send me the lines around the error and I will fix it. That is the one part not testable without a PostgreSQL server.

## Before real students use it

- Unsplash photos are hotlinked under a development key; production use requires Unsplash's approval.
- Vendors have not signed agreements and listed shops have not agreed to be listed (see `OPEN_DECISIONS.md`).
- There is no email, so there is no password reset: the admin must reset passwords.
- Set a custom domain and keep `SECRET_KEY` private; changing it signs everyone out.
- The free database expires after 30 days: upgrade or export before then.

## Dark mode and the generated stylesheet

`frontend/src/dark.css` is generated from `styles.css`. After changing colours in `styles.css`, run `npm run dark-css` from `frontend/` and commit the result. Hand fixes for the dark theme go in `frontend/src/dark-overrides.css`, which is never overwritten.
