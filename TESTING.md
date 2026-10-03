# Testing Report — Expense Classification & Reporting Tool

All testing for this project in one place: unit, integration, end-to-end,
migration, concurrency, performance and load tests — with the actual metrics we
measured. Runs were done on **2026-10-03** on Windows with Docker Postgres; the
integration suite was also run against the live Vercel deployment.

---

## 1. Summary

| Layer | Location | What it proves | Latest result |
|---|---|---|---|
| Unit + API tests | `backend/tests/` | Logic and endpoints in-process against a disposable Postgres DB | **46 passed** in 23.2s |
| Integration (live server) | `backend/integration_tests/` | Real HTTP against a running app — every endpoint, edges, concurrency | **59 passed, 6 skipped** (stress opt-in) in 176.9s |
| End-to-end (E2E) | `scripts/e2e_api_test.py` | One scripted user journey across the whole API | **54/54 checks passed** in 3.4s |
| Migration cycle | `backend/tests/test_migrations.py` | Alembic upgrade → downgrade → upgrade + model/schema diff | **1 passed**; zero schema drift |
| Concurrency / idempotency | `backend/integration_tests/test_concurrency_idempotency.py` | Parallel uploads, signups, budget writes, re-categorization | **12 passed** |
| Load / performance (k6) | `loadtests/k6/` + `loadtests/results/` | Smoke, mixed-API load, upload stress, max-size upload, over-limit, exports | 6 scenarios; 3 fully green, 1 latency threshold missed, max-upload known bottleneck |
| Frontend build | `frontend/` (Vite) | TypeScript compile + production bundle | Build succeeded (2,548 modules; 772.8 kB JS / 58.8 kB CSS) |

**Test database setup.** Unit/integration tests create a throwaway database
(`expense_test`) from the SQLAlchemy models and truncate every table between
tests, so runs are repeatable. The migration test uses its own database
(`expense_migration_test`) and drops it afterwards.

---

## 2. How to run everything

```bash
cd backend

# Unit + API tests (46)
.venv/Scripts/python.exe -m pytest                 # Windows
# .venv/bin/python -m pytest                        # macOS/Linux

# Integration tests against a running server (65 collected; 6 skipped by default)
docker compose up -d
.venv/Scripts/python.exe -m pytest integration_tests -q

# Integration tests against the deployed app
INTEGRATION_BASE_URL=https://expensify-teal.vercel.app .venv/Scripts/python.exe -m pytest integration_tests -q

# Optional heavy stress tests
RUN_STRESS=1 .venv/Scripts/python.exe -m pytest integration_tests -q

# End-to-end journey (server must be up)
.venv/Scripts/python.exe ../scripts/e2e_api_test.py
```

```bash
# Load tests (k6 via Docker; app must be up on localhost:8000)
loadtests/run_k6.sh
```

---

## 3. Unit & API tests — 46 passed

In-process FastAPI `TestClient` + real Postgres. Full inventory:

| File | Tests | Covers |
|---|---|---|
| `test_auth.py` | 4 | signup + `/me`, password is hashed (never stored plaintext), wrong password rejected, protected route requires auth |
| `test_upload.py` | 6 | all rows imported, re-upload fully deduplicated, malformed header → FAILED record, non-CSV rejected, bad rows skipped + counted, categories classified |
| `test_csv_parser.py` | 7 | valid parse, invalid header, empty file, BOM stripping, per-row errors, currency symbols, latin-1 fallback |
| `test_classifier.py` | 6 | known keywords, case-insensitivity, unknown → "Other", empty/None descriptions, first match wins |
| `test_learning.py` | 1 | re-categorizing learns a keyword and reclassifies matching rows |
| `test_validation.py` | 9 | email/name normalization, blank name → null, overlong fields, bcrypt 72-byte cap, category sanitization, hex colors, budget precision bounds, query bounds, CSV row sanitization |
| `test_upload_limits.py` | 4 | at/over row limit, duplicate category names on create and rename |
| `test_transaction_control.py` | 3 | commit on success, rollback on failure, failed re-categorization leaves no keyword behind |
| `test_budgets.py` | 2 | set/list/delete budget, budget requires owned category |
| `test_export.py` | 2 | CSV and PDF export |
| `test_isolation.py` | 1 | one user cannot see another user's data |
| `test_migrations.py` | 1 | upgrade → downgrade → upgrade, no ORM/schema drift |
| **Total** | **46** | **23.2s runtime** |

---

## 4. Integration tests — 59 passed, 6 skipped (176.9s)

Real HTTP against a running server (local Docker, and separately against the
production Vercel deployment). 65 tests collected, 6 stress tests skipped unless
`RUN_STRESS=1`:

| File | Tests | Covers |
|---|---|---|
| `test_edge_cases.py` | 29 | malformed/empty/binary CSVs, BOM + CRLF + quoted commas, header-only uploads, extensions, oversized/invalid values, auth edge cases (bad/expired/tampered tokens, long passwords), category/budget validation, unknown IDs |
| `test_endpoints_all.py` | 11 | every endpoint's happy path and error responses |
| `test_concurrency_idempotency.py` | 12 | sequential re-upload, repeated PATCH/PUT/DELETE/logout idempotency, 5 concurrent identical uploads import once, 4 concurrent distinct uploads all import, concurrent signup/category/budget races |
| `test_export_integration.py` | 7 | CSV/PDF exports reflect filters and learned categories, per-user isolation, empty user |
| `test_upload_stress.py` | 6 | **opt-in**: max-size upload, over-limit rejection, 60k-row rejection, concurrent max-size uploads, lightweight requests not starved |

Highlights proven under concurrency:

- **5 simultaneous identical uploads → exactly 1 import**: imported counts
  summed to the file's rows once; every other response reported all rows as
  duplicates; only one upload record shows the rows.
- **4 simultaneous distinct uploads → all 160 rows imported** and visible in
  both `/transactions` and `/summary`.
- Concurrent duplicate signup/category/budget races currently still return a
  500 in some interleavings (tracked as known limitations, marked `xfail`).

**Production run (Vercel):** same suite executed against
`https://expensify-teal.vercel.app` — **59 passed, 6 skipped**. One test was
adjusted to accept `400` or `413` for oversized uploads, because Vercel's 4.5 MB
platform body limit answers `413` before the app's own check runs.

---

## 5. End-to-end test — 54/54 passed

`scripts/e2e_api_test.py` walks one complete user journey and records every
call with timing into `scripts/e2e_report.json`:

| Metric | Value |
|---|---|
| Checks | **54 / 54 passed, 0 failed** |
| Wall-clock | 3,421 ms |
| API time total | 2,417 ms |
| Avg / median latency | 44.8 ms / 12.9 ms |
| p95 / max latency | 307.1 ms / 405.9 ms |

Flow covered (all verified): health → signup → duplicate-signup 400 →
login/wrong-password 401 → refresh → unauthenticated 401s → default categories →
category create/update/duplicate-400 → CSV upload → duplicate CSV → uploads
list/get/404/non-CSV-400 → transaction list/filters/search/category/get/404 →
re-categorize (learning) → invalid category 400 → summary all-time + filtered →
insights → budgets set/list/update/delete/delete-again-404 → CSV + filtered CSV +
PDF exports → category delete (uncategorized rows verified) → default/missing
category delete errors → logout → login again → data persists → **second user
isolation** (separate transactions, cannot fetch the first user's upload).

---

## 6. Migration test

`tests/test_migrations.py` (1 test, part of the 46):

- `alembic upgrade head` → all expected tables exist.
- Autogenerate diff between the migrated schema and the SQLAlchemy models is
  **empty** (migrations match the models exactly).
- `alembic downgrade base` → only `alembic_version` remains.
- `upgrade head` again → schema restored, diff still empty.

This proves the two data-integrity migrations (composite indexes +
`CHECK` constraints) are reversible and in sync with the ORM.

---

## 7. Load & performance tests (k6)

Run with `loadtests/run_k6.sh` (k6 in Docker, app on localhost:8000).
Recorded run: `loadtests/results/run_k6_final.log`, raw summaries in
`loadtests/results/*.json`.

| Scenario | Load | Requests | Failed | Checks | Latency | Verdict |
|---|---|---|---|---|---|---|
| `smoke.js` | 1 VU, 1 iteration | 13 | 0% | 100% (16/16) | avg 53 ms, p95 180 ms | **PASS** |
| `load_all_apis.js` | ramp 0→20 VUs over ~75s | 2,300 | 0% | 100% (2,509/2,509) | avg 449 ms, p95 **2.52 s**, p99 **6.18 s** | Checks pass; **latency thresholds missed** (targets p95<1.5s, p99<4s) |
| `upload_stress.js` | 4 VUs, 12 uploads × 1,000 rows | 13 | 0% | 100% (36/36) | upload avg 6.77 s, p95 9.06 s; **12,000 rows imported** | **PASS** |
| `upload_over_limit.js` | 1 VU | 2 | 0% | 100% (2/2) | avg 1.0 s, p95 1.28 s | **PASS** (oversized file rejected) |
| `export_test.js` | 5 VUs, 20 iterations | 62 | 0% | 100% (180/180) | avg 1.57 s, p95 2.32 s | **PASS** |
| `upload_max.js` | 3–4 VUs, max-size files | 5 | **20% failed** | **75%** | avg 60.2 s, p95 **108.9 s** | **FAIL — known bottleneck** (final k6 attempt hit a client-side OOM before summary) |

**Reading these results**

- The API stayed **error-free** in every scenario except max-size uploads, and
  every functional check passed where the run completed.
- Mixed-API p95 exceeded the 1.5 s goal under 20 concurrent VUs. This is the
  local single-worker Uvicorn + Docker setup; the likely wins are caching hot
  summary/insights queries and running multiple workers (documented in
  `ARCHITECTURE.md` §12).
- **Max-size uploads are the real weak spot** (~1–2 minutes synchronous, one
  failed request, client OOM). This is exactly the case that motivates the
  deferred background worker + queue trade-off described in
  `SELF_ASSESSMENT.md`: it is not worth paying for at current volumes, but it
  is the first thing to add when traffic grows.
- The concurrency planning target is **~50 concurrent users** on normal
  file sizes (per `SELF_ASSESSMENT.md`); the recorded scripts exercised up to
  20 concurrent VUs for mixed APIs and 4 concurrent upload workers locally.

---

## 8. What is not covered (known gaps)

- **Frontend automated tests** — the UI relies on the TypeScript build and
  manual verification; adding Vitest component tests is on the improvement list.
- **Stress scenarios are opt-in** (`RUN_STRESS=1`) because they need large
  fixtures (~10 MB / 60k rows) and time.
- **Serverless limits** — exports/uploads above Vercel's 4.5 MB body cap cannot
  be tested there; the Docker deployment supports the full 10 MB path.
- **Frontend CI** — no pipeline runs the tests automatically yet; commands
  above are manual.

---

## 9. Where the evidence lives

| Artifact | Path |
|---|---|
| Unit/API tests | `backend/tests/` |
| Integration tests | `backend/integration_tests/` |
| E2E script + JSON report | `scripts/e2e_api_test.py`, `scripts/e2e_report.json` |
| k6 scripts | `loadtests/k6/` |
| k6 results (JSON + log) | `loadtests/results/` |
| CI-style runner for k6 | `loadtests/run_k6.sh` |
