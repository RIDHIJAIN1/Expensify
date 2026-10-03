# Self-Assessment — Expense Classification & Reporting Tool

## Key design choices and trade-offs

- **PostgreSQL over MongoDB** — relational integrity (foreign keys, a unique
  fingerprint index, exact `numeric(12,2)` money) matters more than document
  flexibility for financial transactions; precision is non-negotiable.
- **Rule-based classification over ML/LLM** — deterministic, unit-testable, and
  keeps sensitive financial data on our own server (privacy requirement).
  Trade-off: it misses merchants it doesn't know — recovered via custom
  categories, manual override, and an `Other` fallback.
- **Stateless JWT over server-side sessions** — scales cleanly and is idiomatic
  for FastAPI + React. Trade-off: a token can't be instantly revoked, so we use
  short-lived access tokens + refresh tokens.
- **`httpOnly` cookie over localStorage** — immune to XSS token theft.
  Trade-off: needs CSRF mitigation (`SameSite=Lax`).
- **Single service, one origin (Docker/Render locally, Vercel for the live
  deploy)** — the React app and the API share one domain, so there is no CORS
  and cookies are first-party. Trade-off on Vercel: serverless functions cap
  request bodies at 4.5 MB, so the hosted demo runs with `MAX_UPLOAD_MB=4`; the
  Docker path still supports the full 10 MB.
- **Synchronous upload processing for now, instead of a background worker +
  queue.** A worker (Celery/RQ + Redis) with async processing and status
  polling is the "textbook" answer, but it adds real monthly cost and
  operational complexity. Before paying for it, we load-tested the synchronous
  path with maximum-size files and concurrent uploads, and it comfortably
  handles our target of **~50 concurrent users**. So we deliberately saved the
  worker for later: when real traffic grows past that point, the API already
  returns an upload record with `PROCESSING/COMPLETED/FAILED` status, so the
  client contract won't need to change — only the processing behind it.
- **One CSV format for now, pluggable formats later.** Today we accept a single
  statement layout (`Date, Description, Amount, Type, Reference`). In production
  banks export many different layouts, so the plan is a configurable
  per-bank/per-source mapping layer (column aliases and date/amount formats)
  rather than hard-coding more parsers up front.
- **Thin routers + a service layer, with one unit of work.** Routers only
  handle HTTP; services own all business logic and DB access, and every write
  goes through a `transaction()` context manager (commit on success, rollback
  on failure). Trade-off: a bit more structure, but no half-written data and
  the logic is testable without HTTP.
- **Validation in two layers** — Pydantic sanitizes inputs at the API boundary,
  and matching DB `CHECK` constraints stop bad data even if something bypasses
  the API. Trade-off: rules live in two places, kept honest by a migration test.
- **pg8000 (pure-Python Postgres driver) over psycopg** — no native
  libpq/DLL issues, so the same code runs on Windows dev, Linux Docker, and
  serverless.
- **Seeded defaults + user-defined categories (hybrid taxonomy)** — works
  out-of-the-box yet grows to fit real spending.

## What worked well

- **End-to-end verification early.** A smoke script exercised signup → upload →
  classify → summarize → export → logout before the frontend existed, catching
  the `date_trunc` GROUP BY bug immediately; the same flow now runs as a live
  integration suite.
- **Two-tier dedupe holds up under concurrency.** Exact duplicates are blocked
  by a unique `(user_id, fingerprint)` index; overlapping rows (same
  date+description+amount) are caught with a soft fingerprint. Tests fire five
  identical uploads at once and exactly one row set is imported; re-uploading
  the sample file imports 0 and reports every duplicate.
- **Atomic imports and rollback.** Parse → validate → single transaction. A
  failure part-way through a 1,000-row batch never leaves half-imported data,
  and a failed re-categorization never leaves a half-learned keyword.
- **DB-side aggregation.** `GROUP BY category` and `date_trunc(month, …)` keep
  the dashboard fast as data grows; lists are paginated and indexed for the
  actual query patterns.
- **A layered test story that all passes:** 46 backend unit/API tests, a
  migration upgrade→downgrade→upgrade test that also diffs migrations against
  the ORM models, 59 integration tests against the deployed app, and k6 load
  scripts for smoke, full-API load, upload stress, and max-size uploads.
- **Same-origin deployment.** The live app runs as one Vercel project (static
  frontend + FastAPI function + Neon Postgres), so cookies and relative
  `/api/*` calls work unchanged.

## What could be improved

- **Async uploads when load justifies it.** Keep the synchronous path while
  ~50 concurrent users are fine; move to a queue + worker (and return to
  polling the upload status) once volume or file sizes grow. This is the main
  known scaling trade-off we are consciously carrying.
- **Multiple CSV/bank formats.** Add a configuration layer for column aliases
  and date/amount formats so new banks don't require code changes.
- **Household/shared view** — accounts are isolated today; a combined view is a
  natural extension.
- **Richer categorization** — stronger per-merchant learning from overrides.
- **Frontend tests** — only the backend has automated tests; a few component
  tests would harden the UI.
- **Cache hot summary/insights queries** to cut latency on repeat dashboard
  loads, and split the JS bundle (the build warns about its size).

## Difficulties / edge cases faced and how they were resolved

- **Concurrent identical uploads (race).** Two users/clicks can upload the same
  file at the same time and both pass the "is this a duplicate?" checks before
  either commits. Resolved by keeping the DB unique index as the final
  authority plus a unit-of-work rollback; the integration test proves exactly
  one import even with five simultaneous uploads. The losing requests still
  return a successful, fully-deduplicated upload record.
- **Malformed / corrupt CSV files.** Extension check, MIME sniffing (NUL bytes),
  header validation, blank-line skipping, per-row skip-and-count with an error
  summary, and UTF-8 (BOM-stripped) → latin-1 fallback. A completely unreadable
  file is stored as a `FAILED` upload instead of an HTTP error.
- **Dirty or oversized values.** Description/reference/filename are whitespace-
  collapsed and truncated to their column limits, amounts are rounded half-up
  to 2 decimals and range-checked, dates are bounded to 1900–2100. Bad rows are
  skipped and counted, not silently written.
- **Session expiry mid-upload.** The API client transparently calls
  `/api/auth/refresh` and retries once on a 401; if refresh fails the user is
  sent to a clean login. Because imports are atomic, a dropped session can
  never leave a partial import.
- **Large files and performance.** 10 MB / 50k-row caps, 1,000-row batch
  flushes instead of one row at a time, DB-side aggregation, pagination, and
  composite indexes. k6 scripts measure single max-size uploads and concurrent
  uploads; this is also how we validated the "no worker yet" decision.
- **Serverless body limit (Vercel).** Uploads over 4.5 MB are rejected by the
  platform with a 413 before our code runs. Handled by lowering the hosted cap
  to 4 MB, documenting the difference from the Docker deployment, and accepting
  either 400 (app check) or 413 (platform) in the integration test.
- **Database connections on serverless.** Many short-lived function instances
  could exhaust Postgres connections, so the engine uses `NullPool` when it
  detects Vercel and points at Neon's pooled connection string.
- **Python 3.14 wheel gaps.** Pinned `pydantic` and the native `psycopg` lacked
  `cp314` wheels and tried to compile without MSVC. Resolved by upgrading to
  versions with prebuilt wheels and dropping the native driver.
- **Windows "Application Control" blocked psycopg's libpq DLL.** The import
  failed at runtime; resolved by moving to pure-Python **pg8000**.
- **Docker port conflict with a local PostgreSQL.** Remapped the container to
  **55432** and kept the connection string in env.
- **`date_trunc('month', …)` GROUP BY error.** Binding `'month'` as a query
  parameter broke PostgreSQL's expression matching; passing it as a
  `literal_column` made the SELECT/GROUP BY/ORDER BY expressions match.
- **bcrypt's 72-byte limit.** Long passwords (including multi-byte characters)
  used to reach bcrypt and return a 500; the schema now rejects them with a
  clear 422 before hashing.
