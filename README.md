# Expensify — Expense Classification & Reporting Tool

A secure, multi-user web app that uploads bank-statement CSVs, auto-categorizes
transactions, and visualizes spending patterns over customizable time periods —
with CSV and PDF export.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + TypeScript, Tailwind CSS, Recharts, React Router, TanStack Query |
| Backend | FastAPI (Python 3.12/3.14), SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL (Docker locally · Neon managed in production) |
| Auth | JWT (access + refresh) in `httpOnly` cookies, bcrypt password hashing |
| Classification | Deterministic rule-based keyword matching + custom categories + manual override |
| Export | CSV (backend) + ReportLab PDF report (backend) |
| Tests | pytest + FastAPI TestClient against a real Postgres test DB |
| Container | Docker (multi-stage) + Docker Compose |
| Deploy | Render (single web service) + managed Postgres |

## Quick start (Docker — one command)

```bash
docker compose up --build
```

This builds and runs **everything** (Postgres + backend + React frontend served
by FastAPI) and opens the app at **http://localhost:8000**. The migration runs
automatically on startup.

> Note: Postgres is mapped to host port **55432** (not 5432) to avoid clashing
> with any existing local PostgreSQL.

## Local development (faster iteration)

### 1. Start only the database

```bash
docker compose up -d db
```

### 2. Run the backend (hot reload)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows  (or: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env            # optional; defaults already work
alembic upgrade head            # apply migrations
uvicorn app.main:app --reload --port 8000
```

### 3. Run the frontend (Vite dev server, proxies `/api` → :8000)

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Open **http://localhost:5173**.

## Running the tests

```bash
cd backend
.venv/Scripts/python -m pytest -q
```

Tests run against a dedicated `expense_test` database (auto-created) on the
Docker Postgres instance.

## Sample data

`sample_statement.csv` is a realistic Indian bank statement (UPI / cards /
netbanking). Upload it from the dashboard to see classification + charts
instantly. The canonical CSV format is:

```
Date,Description,Amount,Type,Reference
2026-09-02,Swiggy,428.50,DEBIT,UPI-9834
2026-09-15,Salary,75000.00,CREDIT,NEFT-1122
```

## API (auto-documented)

Interactive Swagger UI is available at **`/docs`**. Key resources:

- `POST/GET /api/auth/{signup,login,logout,refresh}`, `GET /api/auth/me`
- `POST /api/uploads`, `GET /api/uploads`, `GET /api/uploads/{id}`
- `GET /api/transactions` (paginated + filters), `PATCH /api/transactions/{id}`
- `GET/POST /api/categories`, `PATCH/DELETE /api/categories/{id}`
- `GET /api/summary`, `GET /api/insights`
- `GET /api/budgets`, `PUT/DELETE /api/budgets/{category_id}`
- `GET /api/export/csv`, `GET /api/export/pdf`

All routes require auth and are scoped to the logged-in user (per-account data
isolation).

## Deployment (Render + Neon)

The app ships as **one Docker service** (API + built React app) and connects to a
managed Postgres (Neon, already wired). Render builds the image and the container
runs `alembic upgrade head` before serving.

### Option A — Blueprint (one click)

1. Push this repo to GitHub.
2. Render → **New → Blueprint** → select the repo (`render.yaml` defines the service).
3. When prompted for the two secret env vars, paste:
   - `DATABASE_URL` — your Neon connection string (same as `backend/.env`)
   - `JWT_SECRET` — the same secret from `backend/.env`
4. **Apply** — Render builds and deploys. `COOKIE_SECURE=true` is preset.

### Option B — Manual

1. Render → **New → Web Service** → select the repo → **Runtime: Docker** (root `Dockerfile`).
2. **Health check path:** `/api/health`.
3. **Environment:**

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | your Neon connection string |
   | `JWT_SECRET` | a long random string |
   | `COOKIE_SECURE` | `true` |

4. Deploy. On boot the container migrates, then serves the API + SPA on one URL.

**Notes**

- The container binds to **`$PORT`** (Render) and falls back to `8000` locally.
- Neon sits in `ap-southeast-1` → choose the **Singapore** region to minimize latency.
- Free instances **spin down when idle** (slow first request).
- Secrets are **never committed** — `.env` is git-ignored; only `.env.example` ships.

## More details

- See **[ARCHITECTURE.md](ARCHITECTURE.md)** for the architecture diagram,
  data flow, schema, security, and trade-offs.
- See **[SELF_ASSESSMENT.md](SELF_ASSESSMENT.md)** for the design-choice /
  trade-off write-up and edge cases.
