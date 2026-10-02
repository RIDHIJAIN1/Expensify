"""End-to-end smoke test using FastAPI TestClient (requires running Postgres)."""
import io
import os
import sys
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def main():
    email = f"smoke{int(time.time())}@example.com"
    password = "supersecret1"

    print("1. health:", client.get("/api/health").json())

    r = client.post("/api/auth/signup", json={"email": email, "password": password, "name": "Smoke"})
    print("2. signup:", r.status_code, r.json())

    r = client.get("/api/auth/me")
    print("3. me (after signup):", r.status_code, r.json())

    # upload sample CSV
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_statement.csv")
    csv_text = open(sample_path, "rb").read()
    r = client.post("/api/uploads", files={"file": ("sample_statement.csv", csv_text, "text/csv")})
    print("4. upload:", r.status_code, r.json())

    r = client.get("/api/summary")
    print("5. summary:", r.status_code, r.json())

    r = client.get("/api/transactions", params={"limit": 5})
    data = r.json()
    print("6. transactions total:", data.get("total"), "first:", data.get("items", [{}])[0])

    r = client.get("/api/categories")
    print("7. categories:", [c["name"] for c in r.json()])

    # re-upload same file -> all duplicates
    r = client.post("/api/uploads", files={"file": ("sample_statement.csv", csv_text, "text/csv")})
    print("8. re-upload (dup):", r.status_code, r.json())

    # export csv
    r = client.get("/api/export/csv")
    print("9. export csv:", r.status_code, r.headers.get("content-type"), "bytes:", len(r.content))

    # export pdf
    r = client.get("/api/export/pdf")
    print("10. export pdf:", r.status_code, r.headers.get("content-type"), "bytes:", len(r.content))

    # logout + me should fail
    r = client.post("/api/auth/logout")
    print("11. logout:", r.status_code)
    r = client.get("/api/auth/me")
    print("12. me (after logout):", r.status_code, r.json())


if __name__ == "__main__":
    main()
