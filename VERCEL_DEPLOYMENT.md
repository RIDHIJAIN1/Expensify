# Deploying Expensify on Vercel

This is a plain-English record of how this app was deployed to Vercel.

**What gets deployed:** one Vercel project serves *both* the React frontend and the
FastAPI backend. The frontend is built as static files during the Vercel build, and the
backend runs as a serverless function. Both live on the same domain, so cookies and the
frontend's relative `/api/...` calls just work — no CORS setup needed.

**Database:** PostgreSQL is not hosted on Vercel. We use a Neon Postgres database
(pooled connection) that the serverless function connects to.

**Live URL:** https://expensify-teal.vercel.app

---

## 1. What you need

- The GitHub repo: `https://github.com/RIDHIJAIN1/Expensify`
- A Vercel account
- Vercel CLI:

  ```bash
  npm install -g vercel
  vercel login
  ```

- A Postgres database. We used **Neon** (free tier). Copy the **pooled** connection
  string — the host contains `-pooler`, and it looks like:

  ```
  postgresql://user:password@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
  ```

  Use the pooled one because Vercel runs many short-lived function instances and the
  pooler keeps the number of real database connections under control.

## 2. Run the database migrations first

Vercel does **not** run migrations for us (the Docker startup command does not apply
here). Run them from your machine, pointed at the production database:

```bash
cd backend

# Windows
set DATABASE_URL=postgresql://...your-neon-url...
.venv\Scripts\python.exe -m alembic upgrade head

# macOS / Linux
export DATABASE_URL="postgresql://...your-neon-url..."
.venv/bin/python -m alembic upgrade head
```

Do this every time the models change. The database is the part that outlives every
deployment.

## 3. The files that make Vercel work

These were added at the repo root:

| File | Why it exists |
|---|---|
| `index.py` | Vercel looks for a FastAPI `app` object. This small file adds `backend/` to Python's import path and re-exports the real app: `from app.main import app`. |
| `requirements.txt` | Vercel installs Python packages from here. It must list the packages **directly** — Vercel's parser does not understand `-r backend/requirements.txt` (that exact line made the first build fail). Keep it in sync with `backend/requirements.txt`. |
| `vercel.json` | Tells Vercel to build the frontend (`npm --prefix frontend ci && npm --prefix frontend run build`), run the function in `sin1` (Singapore, next to Neon), and allow up to 60 seconds per request. |
| `.vercelignore` | Keeps `.venv`, `backend/.env`, logs, etc. out of the upload — important so secrets are never shipped to the platform. |

One small code change was needed:

- `backend/app/database.py` — when the `VERCEL` environment variable is present, the app
  uses SQLAlchemy's `NullPool`. On a normal server it keeps a small pool; on serverless
  it's better to open one connection per request and release it immediately.

The frontend needs no changes. It was already calling `/api/...` relative URLs, and
`backend/app/main.py` already knows how to serve the built SPA from `STATIC_DIR`.

## 4. Set the environment variables

In the Vercel dashboard: **Project → Settings → Environment Variables** (Production),
or with the CLI. We set:

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | Neon pooled URL | |
| `JWT_SECRET` | long random string | generates and signs login tokens |
| `COOKIE_SECURE` | `true` | cookies only over HTTPS |
| `STATIC_DIR` | `../frontend/dist` | where `main.py` finds the built SPA |
| `MAX_UPLOAD_MB` | `4` | Vercel rejects bodies over 4.5 MB before the app runs, so 4 MB is the honest limit |
| `MAX_UPLOAD_ROWS` | `50000` | unchanged app limit |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | |

`CORS_ORIGINS` is not needed: the frontend and API share one origin.

## 5. Create the project and deploy

```bash
# from the repo root
vercel link --yes --project expensify   # creates/links the project + connects GitHub
vercel --prod --yes                     # build + deploy
```

The first build failed with *"could not parse requirements.txt"*, which is why the root
`requirements.txt` was made self-contained. After that fix, the build compiled the React
app, installed the Python packages, and deployed in under a minute.

Pushing to `main` on GitHub now deploys automatically too (the repo is connected).

## 6. Turn off deployment protection

Vercel puts an authentication wall ("Vercel Authentication") in front of new projects.
For a public app you want that off: **Project → Settings → Deployment Protection →
Vercel Authentication → Disable** (or set `ssoProtection` to `null` through the API).
Without this, every request — including tests — gets redirected to a Vercel login page.

## 7. Verify the deployment

```bash
# API is alive
curl https://expensify-teal.vercel.app/api/health
# -> {"status":"ok"}

# Frontend is served
curl -I https://expensify-teal.vercel.app/
```

Then run the full integration test suite against production:

```bash
cd backend
INTEGRATION_BASE_URL=https://expensify-teal.vercel.app .venv/Scripts/python.exe -m pytest integration_tests -q
```

Result at the time of writing: **59 passed, 6 skipped** (the 6 skipped are the opt-in
stress tests). One integration test was relaxed to accept either `400` or `413` for
oversized uploads, because on Vercel the platform answers `413` before our own
"file too large" check can return `400`.

## 8. Things to be aware of on Vercel

- **4.5 MB request/response limit.** Uploads and exports larger than that fail at the
  platform level. That's why `MAX_UPLOAD_MB=4`. The sample statement and normal usage
  are far below this. If you need the full 10 MB / 50k-row imports, run the API on a
  normal server instead (the `Dockerfile` + `render.yaml` in this repo still work).
- **Migrations are manual.** Always run `alembic upgrade head` yourself after a schema
  change — Vercel won't do it.
- **60-second function limit.** Big CSV parses can approach this; the `maxDuration`
  value in `vercel.json` controls it.
- **Cold starts.** The first request after a quiet period takes a bit longer.
- **Region matters.** The function was moved to `sin1` because the Neon database is in
  Singapore; otherwise every database query pays a cross-continent round trip.

## 9. Everyday workflow

```bash
# deploy a new version
vercel --prod

# or just push to GitHub (auto-deploys)

# changed the database models?
cd backend && .venv\Scripts\python.exe -m alembic upgrade head

# changed environment variables?
# update them in the dashboard, then redeploy so the function picks them up
```

## 10. Quick troubleshooting

| Symptom | Cause / fix |
|---|---|
| Build fails: "could not parse requirements.txt" | Root `requirements.txt` must not use `-r`. List packages directly. |
| Every request asks for Vercel login | Deployment Protection is on — disable Vercel Authentication. |
| Upload returns `413` | File is bigger than the 4.5 MB Vercel limit. |
| `database ... does not exist` / missing tables | Migrations were not run against the deployed `DATABASE_URL`. |
| Login works, then user gets logged out | `COOKIE_SECURE=true` requires HTTPS (Vercel gives you HTTPS). |
