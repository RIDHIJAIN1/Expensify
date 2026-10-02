# Implementation Plan — `expense-classification`

Fintech Expense Classification & Reporting Tool. Multi-user secure web app: upload bank-statement CSVs, auto-categorize transactions, visualize spending over customizable time periods, and export CSV/PDF reports.

## 1. Final tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript, Tailwind CSS, Recharts, React Router, TanStack Query | Modern SPA, fast charts, responsive UI |
| Backend | FastAPI (Python) | Typed API, auto Swagger docs, ideal for CSV/classification |
| Database | PostgreSQL via SQLAlchemy 2.0 + Alembic | Industry standard, versioned migrations, money-safe `numeric` |
| Auth | JWT (access + refresh) in `httpOnly` cookie + bcrypt | XSS-safe, fintech-grade |
| Categorization | Rule-based keyword matching + custom categories + manual override | Transparent, testable, privacy-preserving |
| Export | CSV (backend) + ReportLab PDF (backend) | Reliable, professional reports |
| Tests | pytest + FastAPI TestClient on real Postgres | Critical paths covered |
| Container | Docker (Compose for dev, multi-stage Dockerfile) | Required deliverable |
| Deploy | Render single service + Neon/Render Postgres | One URL, one deploy, free |

## 2. Architecture

```
[ React SPA (browser) ]
   │  HTTPS · JSON · JWT in httpOnly cookie
   ▼
[ FastAPI backend ]            ← single Docker service
   ├─ Auth (JWT + bcrypt)
   ├─ CSV parser → validate → dedupe → classify
   ├─ REST API (/api/*, Swagger /docs)
   │
   ▼  SQLAlchemy 2.0 + Alembic
[ PostgreSQL ]
   users · categories · uploads · transactions
```

**Data flow:** signup/login → upload CSV → parse + validate + dedupe + classify → store → `GET /api/summary` → charts → export CSV/PDF.

## 3. Data model (4 tables)

- **users** — id (UUID PK), email (unique), password_hash (bcrypt), name, created_at
- **categories** — id, user_id (FK), name, keywords (JSON), is_custom (bool), color; seeded ~8 defaults per user on signup (Food, Travel, Utilities, Shopping, Income, Entertainment, Healthcare, Other)
- **uploads** — id, user_id, filename, status (PROCESSING/COMPLETED/FAILED), total_rows, imported_count, duplicate_count, error_summary, created_at
- **transactions** — id, user_id, upload_id, date, description, amount (numeric(12,2)), type (DEBIT/CREDIT), reference (nullable), category_id (nullable FK), fingerprint (sha256), created_at; unique index on (user_id, fingerprint)

## 4. API contract

### Auth
- `POST /api/auth/signup`, `/login`, `/logout`, `/refresh`; `GET /api/auth/me`

### Uploads
- `POST /api/uploads` (multipart CSV), `GET /api/uploads`, `GET /api/uploads/{id}`

### Transactions
- `GET /api/transactions` (paginated; filters `date_from`, `date_to`, `category_id`, `type`, `search`)
- `GET /api/transactions/{id}`, `PATCH /api/transactions/{id}` (re-categorize)

### Categories
- `GET /api/categories`, `POST /api/categories`, `PATCH /api/categories/{id}`, `DELETE /api/categories/{id}`

### Dashboard & export
- `GET /api/summary` (aggregates by date range), `GET /api/export/csv`, `GET /api/export/pdf`

All endpoints auth-scoped to the logged-in user. JSON; consistent `{ "detail": "..." }` error shape; 401/403/422; Swagger at `/docs`.

## 5. Edge cases & handling

- **Malformed CSV** — reject non-CSV (extension + MIME); invalid header/empty → reject; skip bad rows + count (FAILED if all bad); UTF-8 (strip BOM) → latin-1 fallback.
- **Duplicates** — two-tier: exact (date+desc+amount+reference) via fingerprint unique index; overlapping (date+desc+amount, ref differs); both skipped + counted.
- **Session expiry mid-upload** — access token 15–30 min + refresh; frontend silently refreshes on 401 + retries, else redirect preserving file; atomic import (single-transaction commit).
- **Large files** — 10 MB / 50k rows cap; stream-read; batch insert ~1000/flush; index on (user_id, date); paginate.

## 6. Dashboard time periods

Presets (This Month, Last Month, Last 3 Months, This Year, All Time) + custom start/end. Charts: spending-by-category (donut), spending-by-month (bar), summary cards (Total Income/Spent/Net, count). Aggregation in SQL (`GROUP BY`), not in memory.

## 7. Directory layout

```
expense-classification/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, database.py
│   │   ├── models/          # users, categories, uploads, transactions
│   │   ├── schemas/         # Pydantic
│   │   ├── api/             # auth, uploads, transactions, categories, summary, export
│   │   ├── core/            # security (jwt, hashing, current_user dep)
│   │   ├── services/        # csv_parser, classifier, dedupe, report
│   │   └── migrations/      # Alembic
│   ├── tests/               # pytest critical paths
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/{pages, components, api}
├── docker-compose.yml
├── sample_statement.csv
└── README.md
```

## 8. Build order (parallelize across agents)

| Phase | Work | Depends on |
|---|---|---|
| 0 | Scaffold: docker-compose, Postgres, FastAPI + React skeletons, health check | — |
| 1 | Backend core: models + Alembic, auth, `current_user` isolation dep | 0 |
| 2 | CSV parser + classifier + dedupe + `POST /api/uploads` | 1 |
| 3 | summary/transactions/categories/export endpoints | 1 |
| 4 | Frontend: auth pages, dashboard + charts, upload, list, export | 3 (contract) |
| 5 | pytest critical paths | 2, 3 |
| 6 | Multi-stage Dockerfile + Render deploy + sample CSV | 4, 5 |
| 7 | README + architecture diagram + self-assessment | 6 |

## 9. Testing (critical paths)

Auth (hash, wrong password, 401), per-user isolation, CSV parsing (valid/malformed/BOM/encoding), categorization (keyword→category, unknown→Uncategorized, collision priority), dedupe (re-upload → 0 new rows), export (CSV + valid PDF).

## 10. Deferred / future

- Auto-remember keyword on manual override (stretch)
- Shared household combined view (documented, not built)
- Frontend Vitest tests (stretch)
- Charts embedded inside PDF (skipped — charts stay in web UI)
