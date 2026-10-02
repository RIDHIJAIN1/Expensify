# Self-Assessment — Expense Classification & Reporting Tool

## Key design choices and trade-offs

- **PostgreSQL over MongoDB** — relational integrity (foreign keys, a unique
  fingerprint index, exact `numeric(12,2)` money) matters more than document
  flexibility for financial transactions; precision is non-negotiable.
- **Rule-based classification over ML/LLM** — deterministic, unit-testable, and
  keeps sensitive financial data on our own server (privacy requirement).
  Trade-off: it misses keywords it doesn't know — recovered via custom
  categories, manual override, and an `Other` fallback.
- **Stateless JWT over server-side sessions** — scales cleanly and is idiomatic
  for FastAPI + React. Trade-off: a token can't be instantly revoked, so we use
  short-lived access tokens + refresh tokens.
- **`httpOnly` cookie over localStorage** — immune to XSS token theft.
  Trade-off: needs CSRF mitigation (`SameSite=Lax`).
- **Single-service deploy (Render) over a microservices split** — one URL, no
  CORS, faster to ship reliably. The ideal split is documented as the
  production scaling path.
- **pg8000 (pure-Python Postgres driver) over psycopg** — no native libpq/DLL,
  so the exact same code runs on Windows dev and Linux Docker/cloud.
- **Seeded defaults + user-defined categories (hybrid taxonomy)** — works
  out-of-the-box yet grows to fit real spending.

## What worked well

- **End-to-end verification early.** A TestClient smoke script exercised
  signup → upload → classify → summarize → export → logout before touching the
  frontend, catching the `date_trunc` GROUP BY bug immediately.
- **Two-tier dedupe.** Exact matches are enforced by a DB unique index;
  overlapping (same date+description+amount) is caught in Python. Re-uploading
  the sample file imported 0 rows and reported 19 duplicates — correct and
  transparent.
- **DB-side aggregation.** `GROUP BY category` and `date_trunc(month, …)` kept
  the dashboard fast regardless of row count, with paginated lists.
- **Atomic import.** Parse + validate + single-transaction commit means a failed
  upload never leaves half-imported rows.
- **26 passing tests** cover auth, isolation, parsing, classification, dedupe,
  and export against a real Postgres test database.

## What could be improved

- **Async upload processing** — currently synchronous; a large file blocks the
  request. A background worker with status polling would scale better.
- **Shared "household" view** — family members are isolated accounts today; a
  combined household dashboard is a natural extension.
- **Richer categorization** — per-merchant learning from manual overrides was
  deferred (stretch goal).
- **Frontend tests** — only the backend has automated tests; a few Vitest
  component tests would harden the UI.
- **Cache hot summary queries** to cut latency on repeat dashboard loads.

## Difficulties / edge cases and how they were resolved

- **Python 3.14 wheel gaps** — the pinned `pydantic` and `psycopg` lacked
  `cp314` wheels, and `pydantic-core` tried (and failed) to compile from source
  without MSVC. Resolved by bumping to versions with prebuilt wheels and
  dropping the native psycopg driver entirely.
- **Windows "Application Control" blocked psycopg's libpq DLL** — the native
  `psycopg-binary` import failed at runtime. Resolved by switching to **pg8000**,
  a pure-Python driver (no DLL, no libpq).
- **Port conflict with a native local PostgreSQL** — Docker's `5432` mapping
  collided with an existing Windows `postgres.exe`. Resolved by remapping Docker
  Postgres to **55432** and reading the connection string from env.
- **`date_trunc('month', …)` GROUP BY error** — binding `'month'` as a query
  parameter broke PostgreSQL's expression matching. Resolved by passing it as a
  `literal_column` so the GROUP BY / SELECT / ORDER BY expressions match.
- **Malformed CSVs** — extension + MIME sniffing, header validation, per-row
  skip-and-count, and UTF-8 (with BOM stripping) → latin-1 encoding fallback.
- **Session expiry mid-upload** — silent refresh-and-retry on 401 via the API
  client; atomic import so no partial rows are ever committed.
