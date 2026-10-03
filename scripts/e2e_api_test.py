"""Full end-to-end API test against the running server + real Postgres.

Covers every route in the app: health, auth, categories, uploads, transactions,
summary, insights, budgets, export. Measures per-call latency and writes a
JSON report to scripts/e2e_report.json.

Usage:
    backend/.venv/Scripts/python.exe scripts/e2e_api_test.py
    BASE_URL=http://127.0.0.1:8000 backend/.venv/Scripts/python.exe scripts/e2e_api_test.py
"""

import json
import os
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone

import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
SAMPLE_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_statement.csv"))
REPORT_PATH = os.path.join(os.path.dirname(__file__), "e2e_report.json")
FROM, TO = "2026-07-01", "2026-10-31"
DEFAULT_CATEGORY_NAMES = {
    "Food", "Travel", "Utilities", "Housing", "Shopping",
    "Entertainment", "Healthcare", "Income", "Other",
}

results: list[dict] = []
failures: list[str] = []
started = time.perf_counter()


def call(label, method, path, expect=200, **kwargs):
    t0 = time.perf_counter()
    try:
        resp = client.request(method, path, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
        ok = resp.status_code == expect
        body_hint = ""
        try:
            payload = resp.json()
            body_hint = json.dumps(payload, default=str)[:180]
        except Exception:
            body_hint = f"{len(resp.content)} bytes"
        if not ok:
            failures.append(f"{label}: expected {expect}, got {resp.status_code} — {body_hint}")
        results.append({
            "label": label, "method": method, "path": path,
            "status": resp.status_code, "expected": expect,
            "ms": round(ms, 2), "ok": ok, "response": body_hint,
        })
        return resp
    except Exception as exc:  # noqa: BLE001
        ms = (time.perf_counter() - t0) * 1000
        failures.append(f"{label}: request error — {exc}")
        results.append({
            "label": label, "method": method, "path": path,
            "status": None, "expected": expect, "ms": round(ms, 2),
            "ok": False, "response": str(exc),
        })
        return None


def expect(condition, message):
    if not condition:
        failures.append(message)


client = httpx.Client(base_url=BASE_URL, timeout=60, follow_redirects=True)
anon = httpx.Client(base_url=BASE_URL, timeout=60, follow_redirects=True)
run_id = uuid.uuid4().hex[:8]
email = f"e2e_{run_id}@example.com"
email2 = f"e2e_iso_{run_id}@example.com"
password = "E2ePassw0rd!"

print(f"=== E2E API test — {BASE_URL} — user {email} ===\n")

# ---------- Health ----------
r = call("health", "GET", "/api/health")
if r:
    expect(r.json() == {"status": "ok"}, "health payload wrong")

# ---------- Auth ----------
r = call("auth.signup", "POST", "/api/auth/signup", expect=201,
         json={"email": email, "password": password, "name": "E2E Bot"})
user_id = r.json()["id"] if r is not None and r.status_code == 201 else None
if r is not None and r.status_code == 201:
    expect(r.json()["email"] == email, "signup email mismatch")

r = call("auth.me (after signup)", "GET", "/api/auth/me")
if r is not None and r.status_code == 200:
    expect(r.json()["id"] == user_id, "me id mismatch")

call("auth.signup duplicate (400)", "POST", "/api/auth/signup", expect=400,
     json={"email": email, "password": password})
r = call("auth.login", "POST", "/api/auth/login",
         json={"email": email, "password": password})
if r is not None and r.status_code == 200:
    expect(r.json()["id"] == user_id, "login id mismatch")

call("auth.login wrong password (401)", "POST", "/api/auth/login", expect=401,
     json={"email": email, "password": "wrong-password"})
call("auth.refresh", "POST", "/api/auth/refresh")

t0 = time.perf_counter()
resp = anon.get("/api/auth/me")
ms = (time.perf_counter() - t0) * 1000
results.append({"label": "auth.me no-cookie (401)", "method": "GET", "path": "/api/auth/me",
                "status": resp.status_code, "expected": 401, "ms": round(ms, 2),
                "ok": resp.status_code == 401, "response": "unauthenticated"})
if resp.status_code != 401:
    failures.append(f"auth.me no-cookie: expected 401, got {resp.status_code}")

t0 = time.perf_counter()
resp = anon.get("/api/transactions")
ms = (time.perf_counter() - t0) * 1000
results.append({"label": "transactions.list no-cookie (401)", "method": "GET",
                "path": "/api/transactions", "status": resp.status_code, "expected": 401,
                "ms": round(ms, 2), "ok": resp.status_code == 401,
                "response": "unauthenticated"})
if resp.status_code != 401:
    failures.append(f"transactions.list no-cookie: expected 401, got {resp.status_code}")

# ---------- Categories CRUD ----------
r = call("categories.list (defaults)", "GET", "/api/categories")
cats = r.json() if r is not None and r.status_code == 200 else []
cat_names = {c["name"] for c in cats}
expect(DEFAULT_CATEGORY_NAMES.issubset(cat_names),
       f"missing default categories: {DEFAULT_CATEGORY_NAMES - cat_names}")
food_id = next((c["id"] for c in cats if c["name"] == "Food"), None)

r = call("categories.create", "POST", "/api/categories", expect=201,
         json={"name": "E2E Merchant", "keywords": ["e2etestmerchant"], "color": "#123456"})
custom_id = r.json()["id"] if r is not None and r.status_code == 201 else None

r = call("categories.list (after create)", "GET", "/api/categories")
if r is not None and r.status_code == 200:
    names = {c["name"] for c in r.json()}
    expect("E2E Merchant" in names, "created category not in list")

call("categories.create duplicate (400)", "POST", "/api/categories", expect=400,
     json={"name": "E2E Merchant", "keywords": []})

r = call("categories.update", "PATCH", f"/api/categories/{custom_id}",
         json={"name": "E2E Updated", "keywords": ["e2etestmerchant", "e2eupdated"], "color": "#654321"})
if r is not None and r.status_code == 200:
    expect(r.json()["name"] == "E2E Updated", "category rename failed")
    expect(r.json()["keywords"] == ["e2etestmerchant", "e2eupdated"], "keywords update failed")
    expect(r.json()["color"] == "#654321", "color update failed")

# ---------- Uploads ----------
csv_bytes = open(SAMPLE_CSV, "rb").read()
r = call("uploads.create (sample CSV)", "POST", "/api/uploads", expect=201,
         files={"file": ("sample_statement.csv", csv_bytes, "text/csv")})
upload_id = r.json()["id"] if r is not None and r.status_code == 201 else None
imported = r.json()["imported_count"] if r is not None and r.status_code == 201 else 0
if r is not None and r.status_code == 201:
    expect(imported > 150, f"expected >150 imported rows, got {imported}")
    expect(r.json()["duplicate_count"] == 0, "first upload reported duplicates")

r = call("uploads.create duplicate CSV", "POST", "/api/uploads", expect=201,
         files={"file": ("sample_statement.csv", csv_bytes, "text/csv")})
if r is not None and r.status_code == 201:
    expect(r.json()["imported_count"] == 0, "duplicate upload imported rows")
    expect(r.json()["duplicate_count"] == imported, "duplicate count mismatch")

r = call("uploads.list", "GET", "/api/uploads")
if r is not None and r.status_code == 200:
    expect(len(r.json()) >= 2, "uploads list too short")
call("uploads.get", "GET", f"/api/uploads/{upload_id}")
call("uploads.get missing (404)", "GET", "/api/uploads/99999999", expect=404)
call("uploads.create non-CSV (400)", "POST", "/api/uploads", expect=400,
     files={"file": ("notes.txt", b"not a csv", "text/plain")})

# ---------- Transactions ----------
r = call("transactions.list (limit 5)", "GET", "/api/transactions", params={"limit": 5})
first_tx_id = None
if r is not None and r.status_code == 200:
    data = r.json()
    expect(data["total"] == imported, f"tx total {data['total']} != imported {imported}")
    expect(len(data["items"]) == 5, "limit not respected")
    first_tx_id = data["items"][0]["id"]

r = call("transactions.list filters", "GET", "/api/transactions",
         params={"date_from": "2026-09-01", "date_to": "2026-09-30", "type": "DEBIT", "limit": 100})
if r is not None and r.status_code == 200:
    items = r.json()["items"]
    expect(len(items) > 0, "no September debits found")
    expect(all(i["type"] == "DEBIT" for i in items), "type filter leaked")
    expect(all("2026-09-01" <= i["date"] <= "2026-09-30" for i in items), "date filter leaked")

r = call("transactions.list search=Swiggy", "GET", "/api/transactions", params={"search": "Swiggy"})
if r is not None and r.status_code == 200:
    items = r.json()["items"]
    expect(len(items) > 0, "search returned nothing")
    expect(all("swiggy" in i["description"].lower() for i in items), "search filter leaked")

r = call("transactions.list category=Food", "GET", "/api/transactions",
         params={"category_id": food_id, "limit": 100})
if r is not None and r.status_code == 200:
    items = r.json()["items"]
    expect(len(items) > 0, "no Food transactions")
    expect(all(i["category_id"] == food_id for i in items), "category filter leaked")

r = call("transactions.get", "GET", f"/api/transactions/{first_tx_id}")
call("transactions.get missing (404)", "GET", "/api/transactions/99999999", expect=404)

r = call("transactions.update (categorize)", "PATCH", f"/api/transactions/{first_tx_id}",
         json={"category_id": custom_id})
if r is not None and r.status_code == 200:
    body = r.json()
    expect(body["transaction"]["category_id"] == custom_id, "category not applied")
    expect(body["learned_keyword"] is not None, "no keyword learned")

r = call("transactions.get (verify update)", "GET", f"/api/transactions/{first_tx_id}")
if r is not None and r.status_code == 200:
    expect(r.json()["category_id"] == custom_id, "update not persisted")
    expect(r.json()["category_name"] == "E2E Updated", "category name not joined")

call("transactions.update invalid category (400)", "PATCH", f"/api/transactions/{first_tx_id}",
     expect=400, json={"category_id": 99999999})

# ---------- Summary / Insights ----------
r = call("summary.all-time", "GET", "/api/summary")
if r is not None and r.status_code == 200:
    body = r.json()
    expect(body["transaction_count"] == imported, "summary count mismatch")
    expect(len(body["by_month"]) > 0, "no monthly buckets")
    expect(len(body["top_merchants"]) > 0, "no top merchants")

r = call("summary.filtered", "GET", "/api/summary",
         params={"date_from": FROM, "date_to": TO})
if r is not None and r.status_code == 200:
    expect(r.json()["transaction_count"] > 0, "filtered summary empty")

r = call("insights", "GET", "/api/insights", params={"date_from": FROM, "date_to": TO})
if r is not None and r.status_code == 200:
    expect(isinstance(r.json(), list), "insights not a list")

# ---------- Budgets ----------
r = call("budgets.set (create)", "PUT", f"/api/budgets/{food_id}",
         params={"date_from": FROM, "date_to": TO}, json={"amount": "5000.00"})
if r is not None and r.status_code == 200:
    expect(float(r.json()["limit"]) == 5000.0, "budget limit wrong")
    expect(float(r.json()["spent"]) > 0, "budget spent not computed")

r = call("budgets.list", "GET", "/api/budgets", params={"date_from": FROM, "date_to": TO})
if r is not None and r.status_code == 200:
    entry = next((b for b in r.json() if b["category_id"] == food_id), None)
    expect(entry is not None, "budget not listed")
    if entry:
        expect(float(entry["limit"]) == 5000.0, "listed budget limit wrong")
        expect(float(entry["remaining"]) == 5000.0 - float(entry["spent"]), "remaining wrong")

r = call("budgets.set (update)", "PUT", f"/api/budgets/{food_id}",
         params={"date_from": FROM, "date_to": TO}, json={"amount": "9000.00"})
if r is not None and r.status_code == 200:
    expect(float(r.json()["limit"]) == 9000.0, "budget update failed")

r = call("budgets.list (verify update)", "GET", "/api/budgets")
if r is not None and r.status_code == 200:
    entry = next((b for b in r.json() if b["category_id"] == food_id), None)
    expect(entry is not None and float(entry["limit"]) == 9000.0, "updated budget not persisted")

call("budgets.delete", "DELETE", f"/api/budgets/{food_id}")
r = call("budgets.list (verify delete)", "GET", "/api/budgets")
if r is not None and r.status_code == 200:
    expect(all(b["category_id"] != food_id for b in r.json()), "budget still listed after delete")
call("budgets.delete again (404)", "DELETE", f"/api/budgets/{food_id}", expect=404)

# ---------- Export ----------
r = call("export.csv", "GET", "/api/export/csv")
if r is not None and r.status_code == 200:
    text = r.text
    expect(text.startswith("Date,Description,Amount,Type,Reference,Category"), "CSV header wrong")
    expect(text.count("\n") >= imported, "CSV row count low")
    expect("text/csv" in r.headers.get("content-type", ""), "CSV content-type wrong")

r = call("export.csv filtered", "GET", "/api/export/csv",
         params={"date_from": "2026-09-01", "date_to": "2026-09-30", "type": "DEBIT"})
if r is not None and r.status_code == 200:
    expect(r.text.count("\n") > 1, "filtered CSV empty")

r = call("export.pdf", "GET", "/api/export/pdf", params={"date_from": FROM, "date_to": TO})
if r is not None and r.status_code == 200:
    expect(r.content[:5] == b"%PDF-", "PDF magic bytes missing")
    expect("application/pdf" in r.headers.get("content-type", ""), "PDF content-type wrong")

# ---------- Category delete ----------
call("categories.delete", "DELETE", f"/api/categories/{custom_id}")
r = call("categories.list (verify delete)", "GET", "/api/categories")
if r is not None and r.status_code == 200:
    expect(all(c["id"] != custom_id for c in r.json()), "category still listed after delete")

r = call("transactions.get (verify uncategorized)", "GET", f"/api/transactions/{first_tx_id}")
if r is not None and r.status_code == 200:
    expect(r.json()["category_id"] is None, "transaction not uncategorized after category delete")

call("categories.delete default (400)", "DELETE", f"/api/categories/{food_id}", expect=400)
call("categories.delete missing (404)", "DELETE", "/api/categories/99999999", expect=404)

# ---------- Logout / persistence / isolation ----------
call("auth.logout", "POST", "/api/auth/logout")
call("auth.me after logout (401)", "GET", "/api/auth/me", expect=401)

r = call("auth.login again", "POST", "/api/auth/login",
         json={"email": email, "password": password})
if r is not None and r.status_code == 200:
    expect(r.json()["id"] == user_id, "relogin user mismatch")

r = call("transactions.list (persisted after relogin)", "GET", "/api/transactions", params={"limit": 1})
if r is not None and r.status_code == 200:
    expect(r.json()["total"] == imported, "data not persisted across logout/login")

t0 = time.perf_counter()
r = anon.post("/api/auth/signup", json={"email": email2, "password": password, "name": "E2E Iso"})
ms = (time.perf_counter() - t0) * 1000
iso_status = r.status_code
if r.status_code == 400:
    t0 = time.perf_counter()
    r = anon.post("/api/auth/login", json={"email": email2, "password": password})
    ms = (time.perf_counter() - t0) * 1000
    iso_status = r.status_code
ok = r.status_code in (200, 201)
results.append({"label": "isolation: second user signup/login", "method": "POST",
                "path": "/api/auth/signup|login", "status": iso_status,
                "expected": "200/201", "ms": round(ms, 2), "ok": ok,
                "response": "second user session"})
if not ok:
    failures.append(f"isolation second user auth: {iso_status}")

t0 = time.perf_counter()
r = anon.get("/api/transactions")
ms = (time.perf_counter() - t0) * 1000
results.append({"label": "isolation: second user transactions", "method": "GET",
                "path": "/api/transactions", "status": r.status_code, "expected": 200,
                "ms": round(ms, 2), "ok": r.status_code == 200 and r.json()["total"] == 0,
                "response": json.dumps(r.json(), default=str)[:180]})
if r.status_code != 200 or r.json()["total"] != 0:
    failures.append("isolation broken: second user sees transactions")

t0 = time.perf_counter()
r = anon.get(f"/api/uploads/{upload_id}")
ms = (time.perf_counter() - t0) * 1000
results.append({"label": "isolation: second user upload get (404)", "method": "GET",
                "path": f"/api/uploads/{upload_id}", "status": r.status_code, "expected": 404,
                "ms": round(ms, 2), "ok": r.status_code == 404,
                "response": "not visible"})
if r.status_code != 404:
    failures.append("isolation broken: second user can read first user's upload")

# ---------- Report ----------
wall_ms = (time.perf_counter() - started) * 1000
total_api_ms = sum(x["ms"] for x in results)
passed = [x for x in results if x["ok"]]
failed = [x for x in results if not x["ok"]]
times = sorted(x["ms"] for x in results)

groups = {}
for x in results:
    area = x["label"].split(".")[0].split(" ")[0].split(":")[0]
    groups.setdefault(area, []).append(x)

print(f"{'#':>3} {'RESULT':<6} {'METHOD':<6} {'STATUS':<6} {'ms':>9}  ENDPOINT")
print("-" * 78)
for i, x in enumerate(results, 1):
    flag = "PASS" if x["ok"] else "FAIL"
    print(f"{i:>3} {flag:<6} {x['method']:<6} {str(x['status']):<6} {x['ms']:>9.1f}  {x['label']}")

print("\n=== TIMING INSIGHTS ===")
print(f"calls: {len(results)}   passed: {len(passed)}   failed: {len(failed)}")
print(f"total wall clock (test run): {wall_ms:,.0f} ms")
print(f"total time inside API calls: {total_api_ms:,.0f} ms ({total_api_ms / wall_ms * 100:.1f}% of run)")
print(f"avg per call:   {statistics.mean(times):,.1f} ms")
print(f"median:         {statistics.median(times):,.1f} ms")
print(f"p95:            {times[int(len(times) * 0.95) - 1]:,.1f} ms")
print(f"min / max:      {times[0]:,.1f} ms / {times[-1]:,.1f} ms")

print("\nSlowest 8 calls:")
for x in sorted(results, key=lambda y: -y["ms"])[:8]:
    print(f"  {x['ms']:>9.1f} ms  {x['method']:<5} {x['path']:<32} {x['label']}")

print("\nBy area (calls / avg ms / max ms):")
for area, rows in groups.items():
    print(f"  {area:<14} {len(rows):>2} calls   avg {statistics.mean(r['ms'] for r in rows):>8.1f} ms   max {max(r['ms'] for r in rows):>8.1f} ms")

if failures:
    print("\n=== FAILURES ===")
    for f in failures:
        print(f"  - {f}")

report = {
    "base_url": BASE_URL,
    "user_email": email,
    "started_at": datetime.now(timezone.utc).isoformat(),
    "wall_ms": round(wall_ms, 2),
    "total_api_ms": round(total_api_ms, 2),
    "calls": len(results),
    "passed": len(passed),
    "failed": len(failed),
    "timing": {
        "avg_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "p95_ms": round(times[int(len(times) * 0.95) - 1], 2),
        "min_ms": round(times[0], 2),
        "max_ms": round(times[-1], 2),
    },
    "results": results,
    "failures": failures,
}
with open(REPORT_PATH, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, default=str)
print(f"\nreport saved: {REPORT_PATH}")
sys.exit(1 if failures else 0)
