# Grilling log — expense-classification

## Problem statement
Build a **secure web application** ("Fintech Expense Classification & Reporting Tool") that lets a user (or their family) upload bank statements as CSV files, automatically categorize each transaction, and visualize spending patterns over customizable time periods — while ensuring data privacy and fault tolerance.

Source assignment (docx: "Expense Classification Assignment (2) (2).docx") requires:

1. **Working application** — user auth (sign-up/login/logout); CSV upload (drag-and-drop or file selector); backend to parse CSV, categorize transactions, and store data; interactive responsive dashboard with spending summaries + charts by category and time frame; export categorized data as CSV and PDF; meaningful error/edge-case handling.
2. **Architecture diagram & explanation** — frontend, backend, database, APIs, deployment; rationale for tech choices, data flow, security.
3. **Backend design & schema** — models for users, transactions, categories, uploads; RESTful or GraphQL API endpoint spec.
4. **Technology stack description** — modern stack suitable for fintech security & scalability.
5. **Edge cases & testing** — malformed/corrupt CSV; duplicate/overlapping transactions; session expiration mid-upload; large file uploads & performance; automated unit/integration tests for critical paths.
6. **Deployment & documentation** — deploy to a freely accessible environment; docs for setup/running/testing.
7. **Self-assessment** — key design choices & trade-offs; what worked well vs. could be improved; difficulties/edge cases and how resolved.

## Q&A
### Q1 — Hard constraints & evaluation context (mandated stack? timeline? solo/team? grading?)
- **Answer:** (1) whole stack is my choice; (2) ~6–7 hours available today only; (3) solo; (4) not graded.
- **Rationale:** These constraints dominate everything downstream. A 6–7h solo, ungraded build means we must prioritize a *finishable, demonstrable, understandable* solution over maximal breadth. The "modern fintech stack + scalability" requirement gets satisfied in the architecture/write-up rather than by actually provisioning heavy infra today.
- **Source:** user

### Q2 — Tech stack choice (given 6–7h budget, options A/B/C)
- **Answer:** Option C — the "full impressive" stack: React SPA + FastAPI + PostgreSQL + Docker + cloud deploy. User has AI agents to parallelize work and wants the strongest project + max learning.
- **Rationale:** With AI agents to parallelize the build, the full-stack breadth becomes feasible and directly matches the assignment's example stack (strong on paper) while giving maximum learning exposure across frontend/backend/DB/Docker/deploy.
- **Source:** user

### Q16 — Time-period semantics (dashboard)
- **Answer:** Date-range selector with presets (This Month, Last Month, Last 3 Months, This Year, All Time) + custom start/end pickers. Charts: spending-by-category (donut), spending-by-month (bar), plus summary cards (Total Income/Spent/Net, tx count). Range passed as `date_from`/`date_to` to summary + list + CSV/PDF; aggregation done in SQL (GROUP BY category / month), not in memory.
- **Rationale:** One query pattern powers the whole dashboard (consistent/testable); DB-side aggregation is scalable and a good architecture-doc point.
- **Source:** user

## Open / deferred
- **Auto-remember keyword on manual override** (Q7 nice-to-have) — deferred as stretch goal; manual override + custom categories are in scope.
- **Shared "household" combined view** (Q8 Option B) — future extension; documented in architecture but not built.
- **Frontend Vitest tests** — stretch only; backend pytest is the priority.
- **Embedding charts inside the PDF report** — skipped; charts live in the web dashboard only.
- **User's existing cloud accounts** — not yet confirmed; Render (Option A) chosen, but account specifics to verify at deploy time.

- **Answer:** Date-range selector with presets (This Month, Last Month, Last 3 Months, This Year, All Time) + custom start/end pickers. Charts: spending-by-category (donut), spending-by-month (bar), plus summary cards (Total Income/Spent/Net, tx count). Range passed as `date_from`/`date_to` to summary + list + CSV/PDF; aggregation done in SQL (GROUP BY category / month), not in memory.
- **Rationale:** One query pattern powers the whole dashboard (consistent/testable); DB-side aggregation is scalable and a good architecture-doc point.
- **Source:** user

- **Answer:** Auth: `POST /api/auth/{signup,login,logout,refresh}`, `GET /api/auth/me`. Uploads: `POST /api/uploads`, `GET /api/uploads`, `GET /api/uploads/{id}`. Transactions: `GET /api/transactions` (paginated; filters date_from/date_to/category_id/type/search), `GET /api/transactions/{id}`, `PATCH /api/transactions/{id}` (re-categorize). Categories: `GET/POST /api/categories`, `PATCH/DELETE /api/categories/{id}`. Dashboard/export: `GET /api/summary` (aggregates by date range), `GET /api/export/csv`, `GET /api/export/pdf`. All auth-scoped to logged-in user; JSON; consistent `{detail}` error shape; 401/403/422; Swagger at `/docs`.
- **Rationale:** Standard RESTful contract; per-user ownership enforced on every route; Swagger auto-docs double as the API-spec deliverable.
- **Source:** user

- **Answer:** **Option A — single service on Render**: FastAPI serves the API + built React static files (one Dockerfile), with managed Postgres (Render free tier or Neon free). One URL, no CORS. Local dev via Docker Compose (Postgres + app). Architecture diagram will still show the "ideal" split frontend/backend/DB as the production-scaling story.
- **Rationale:** One deploy/URL minimizes deployment-debugging risk in a 6h build; Docker experience still demonstrated; split-into-three (Vercel+Render+Neon) deferred to the diagram only.
- **Source:** user

- **Answer:** `pytest` + FastAPI TestClient, run against a dedicated **Postgres test database** (Docker Compose) with fixtures creating/tearing down schema per run. Critical-path tests: auth (hash, wrong password, 401), per-user isolation, CSV parsing (valid/malformed/BOM/encoding), categorization (keyword→category, unknown→Uncategorized, collision priority), dedupe (re-upload → 0 new rows), export (CSV + valid PDF). Frontend Vitest = stretch only.
- **Rationale:** Backend holds the correctness-critical logic; real Postgres (not SQLite) faithfully exercises ORM/constraints/fingerprint unique-index; frontend tests deferred to protect the 6h budget.
- **Source:** user

- **Answer:** (1) Malformed CSV: reject non-CSV by extension + MIME sniffing; reject invalid header/empty file; skip bad rows + count them (FAILED if all rows bad); UTF-8 (strip BOM) → fall back to latin-1 on UnicodeDecodeError; expose upload status + error_summary. (2) Duplicates: two-tier dedupe — exact (date+desc+amount+reference via fingerprint unique index) and overlapping (date+desc+amount, ref differs/missing); both skipped + counted. (3) Session expiry mid-upload: 15–30min access token + refresh token; frontend silently refreshes on 401 and retries once, else redirect to login preserving the file; atomic import (parse+validate then single-transaction commit). (4) Large files: 10 MB / 50k rows cap; stream-read line-by-line; batch insert ~1000 rows/flush; index on transactions(user_id, date); paginate list endpoint.
- **Rationale:** Finance apps must never silently double-count (dedupe) nor half-import (atomic commit); caps bound resource use; graceful encoding fallback avoids crashes on Excel/legacy files.
- **Source:** user

- **Answer:** Vite + React + TypeScript; React Router; TanStack Query. Charts = **Recharts**; styling = **Tailwind CSS**.
- **Rationale:** Recharts gives pie/bar/line charts declaratively (the dashboard deliverable) with minimal code; Tailwind gives fast responsive UI. Vite+TS+Router+TanStack Query are the standard modern SPA baseline.
- **Source:** user

### Q11 — Export (CSV + PDF)
- **Answer:** CSV via a backend endpoint (Python `csv` module, respecting current date/category filters). PDF report via **ReportLab** on the backend — a summary report (title, date range, spending-by-category table, top-N transactions), no embedded charts (charts stay interactive in the web dashboard).
- **Rationale:** Server-generated PDF is more reliable/controllable and keeps report logic with the data (more professional + secure); embedding charts in PDF is a time sink we skip. Rejected FPDF2 (fewer features) and jsPDF (finicky formatting client-side).
- **Source:** user

- **Answer:** Confirmed schema: `users` (id, email unique, password_hash bcrypt, name, created_at); `categories` (id, user_id FK, name, keywords JSON, is_custom bool, color); `uploads` (id, user_id, filename, status PROCESSING/COMPLETED/FAILED, total_rows, imported_count, duplicate_count, error_summary, created_at); `transactions` (id, user_id, upload_id, date, description, amount numeric(12,2), type DEBIT/CREDIT, reference nullable, category_id nullable, fingerprint sha256, created_at). Unique index on (user_id, fingerprint).
- **Rationale:** `user_id` on every table enforces isolation; `numeric(12,2)` avoids float money bugs; fingerprint + unique index dedupes at DB level; nullable `category_id` = Uncategorized fallback.
- **Source:** user

- **Answer:** **Option A — multi-user with per-account data isolation** (NOT single-user). Many accounts (each family member registers separately); every `Transaction`/`Category`/`Upload` is owned by a `user_id`; every API query is filtered by the logged-in user so no one sees another account's data.
- **Rationale:** Demonstrates real secure multi-user auth + data privacy (the assignment's core theme). Shared "household" combined view (Option B) is noted as a future extension in the architecture doc, not built today (time risk). Clarified for the user the distinction between "single-user" (one shared DB, no login) and "multi-user with isolation" (like Gmail — many accounts, each private).
- **Source:** user

- **Answer:** **Hybrid (Option C)** — seed ~8 default categories on signup (Food, Travel, Utilities, Shopping, Income, Entertainment, Healthcare, Other); user can add custom categories (with optional keywords); any transaction can be manually re-categorized via a dropdown override.
- **Rationale:** Works out-of-the-box for the demo *and* grows to fit the user's real life (answers "not every category can be predefined"). Slight extra schema cost (categories table with `user_id` / `is_custom`).
- **Source:** user

- **Answer:** **Rule-based keyword matching** (deterministic). A keyword→category map; scan the transaction `Description` for matches, case-insensitive, with priority ordering on collisions. User raised the valid concern that *not every category can be predefined* → handled by an `Uncategorized`/`Other` fallback + manual override + user-defined custom categories (see Q7).
- **Rationale:** Transparent (can show *why* each row was classified → easy to unit-test and explain), deterministic, zero cost, and keeps sensitive financial data on our own server (no third-party/LLM). Rejected ML (needs training data we lack, black-box, unpredictable) and LLM API (violates data-privacy requirement, costs money, non-deterministic).
- **Source:** user

- **Answer:** No real bank CSV → use a **canonical format** and generate a realistic sample CSV. Columns: `Date, Description, Amount, Type (DEBIT/CREDIT), Reference`.
- **Rationale:** Minimum columns needed to categorize + chart; `Type` separates spending from income; `Reference` gives a fingerprint for duplicate detection (a required edge case). Keeps the parser clean and makes malformed-CSV handling demonstrable.
- **Source:** user

- **Answer:** Token-based (stateless) auth — JWT **access token (~15–30 min) + refresh token**, delivered in an **`httpOnly`, `Secure`, `SameSite=Lax` cookie** (NOT localStorage). Passwords hashed with **bcrypt**. Rejected localStorage JWT (XSS-exposed) and server-side sessions (stateful, DB lookup per request, harder to scale).
- **Rationale:** httpOnly cookie makes the token invisible to JS → immune to XSS token theft (the fintech-grade choice); `SameSite=Lax` + `X-Requested-With` header check mitigate CSRF. Short-lived access + refresh token directly supports the "session expiration mid-upload" edge case. bcrypt is the ubiquitous, defensible password-hashing standard.
- **Source:** user

- **Answer:** PostgreSQL, accessed via **SQLAlchemy 2.0 + Alembic**. Local Postgres runs in Docker Compose; connection string comes from an env var so the same code targets local Docker Postgres and cloud Postgres unchanged.
- **Rationale:** Industry-standard ORM with the largest docs/answer pool (best for debugging under time pressure), Alembic gives a versioned-migrations story for the architecture write-up. Rejected SQLModel (younger, fewer examples, "translation tax" when SQLAlchemy errors surface) and raw SQL/asyncpg (too much hand-written SQL, error-prone).
- **Source:** user
