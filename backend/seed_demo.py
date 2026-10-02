"""Seed the demo account + sensible budgets, and print verification."""
import os

import httpx

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
FROM, TO = "2026-07-02", "2026-10-02"

c = httpx.Client(base_url=BASE, timeout=30, follow_redirects=True)
email, password = "demo@example.com", "demo12345"

r = c.post("/api/auth/signup", json={"email": email, "password": password, "name": "Demo"})
if r.status_code != 201:
    r = c.post("/api/auth/login", json={"email": email, "password": password})
print("auth:", r.status_code)

with open("../sample_statement.csv", "rb") as f:
    data = f.read()
r = c.post("/api/uploads", files={"file": ("sample_statement.csv", data, "text/csv")})
print("upload:", r.status_code, r.json().get("imported_count"), "imported,", r.json().get("duplicate_count"), "dup")

summary = c.get("/api/summary", params={"date_from": FROM, "date_to": TO}).json()
by_cat = {x["category_name"]: float(x["total"]) for x in summary["by_category"]}
print("by_category:", by_cat)

cats = {x["name"]: x["id"] for x in c.get("/api/categories").json()}
factors = {
    "Food": 0.9, "Travel": 1.3, "Shopping": 0.8,
    "Utilities": 1.2, "Housing": 1.5, "Entertainment": 0.7, "Healthcare": 1.4,
}
for name, factor in factors.items():
    spend = by_cat.get(name, 0)
    if name not in cats or spend <= 0:
        continue
    amount = max(500, round(spend * factor / 500) * 500)
    r = c.put(
        f"/api/budgets/{cats[name]}",
        params={"date_from": FROM, "date_to": TO},
        json={"amount": f"{amount:.2f}"},
    )
    print(f"budget {name}: {amount} -> {r.status_code}")

print("--- budgets ---")
for b in c.get("/api/budgets", params={"date_from": FROM, "date_to": TO}).json():
    print(f"  {b['category_name']}: {b['spent']}/{b['limit']} = {b['percent']}% over={b['over']}")

print("--- insights ---")
for i in c.get("/api/insights", params={"date_from": FROM, "date_to": TO}).json():
    print(f"  [{i['tone']}] {i['title']} — {i['detail']}")
