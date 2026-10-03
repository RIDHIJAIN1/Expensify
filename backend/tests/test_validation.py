"""Schema-layer validation and sanitization tests.

Every value must be validated and sanitized before it can reach the database,
so these tests exercise the boundary inputs directly through the API.
"""

from .conftest import signup


def _signup(client, email="val@example.com", **extra):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret1", **extra},
    )


# ---------------------------------------------------------------- auth


def test_signup_normalizes_email_and_name(client):
    r = _signup(client, email="  MiXeD@Example.COM ", name="  Ada   Lovelace ")
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "mixed@example.com"
    assert body["name"] == "Ada Lovelace"
    assert client.get("/api/auth/me").json()["email"] == "mixed@example.com"


def test_signup_blank_name_becomes_null(client):
    r = _signup(client, name="   ")
    assert r.status_code == 201 and r.json()["name"] is None


def test_signup_rejects_overlong_fields(client):
    assert _signup(client, name="x" * 121).status_code == 422
    assert _signup(client, password="x" * 73).status_code == 422
    # 40 multi-byte chars = 80 UTF-8 bytes, over bcrypt's 72-byte limit
    assert _signup(client, password="\u00e9" * 40).status_code == 422


def test_login_password_length_is_capped(client):
    assert _signup(client).status_code == 201
    r = client.post(
        "/api/auth/login",
        json={"email": "val@example.com", "password": "x" * 200},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------- categories


def test_category_sanitizes_name_and_keywords(client):
    signup(client, "catsanitize@example.com")
    r = client.post(
        "/api/categories",
        json={
            "name": "  Coffee   Shops ",
            "keywords": ["  Cafe ", "CAFE", "latte", "   "],
            "color": "#4f46e5",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Coffee Shops"
    assert body["keywords"] == ["cafe", "latte"]


def test_category_rejects_bad_values(client):
    signup(client, "catbad@example.com")
    assert client.post("/api/categories", json={"name": "   "}).status_code == 422
    assert client.post("/api/categories", json={"name": "x" * 61}).status_code == 422
    assert (
        client.post("/api/categories", json={"name": "Ok", "keywords": ["a,b"]}).status_code
        == 422
    )
    assert (
        client.post("/api/categories", json={"name": "Ok", "keywords": ["k" * 61]}).status_code
        == 422
    )
    assert (
        client.post("/api/categories", json={"name": "Ok", "color": "not-a-color"}).status_code
        == 422
    )
    assert (
        client.post("/api/categories", json={"name": "Ok", "color": "#" + "a" * 30}).status_code
        == 422
    )


# ---------------------------------------------------------------- budgets / transactions


def _food_id(client) -> int:
    cats = client.get("/api/categories").json()
    return next(c["id"] for c in cats if c["name"] == "Food")


def test_budget_amount_matches_db_precision(client):
    signup(client, "budgetval@example.com")
    food = _food_id(client)
    assert client.put(f"/api/budgets/{food}", json={"amount": "0"}).status_code == 422
    assert client.put(f"/api/budgets/{food}", json={"amount": "10.999"}).status_code == 422
    assert (
        client.put(f"/api/budgets/{food}", json={"amount": "10000000000.00"}).status_code
        == 422
    )
    assert (
        client.put(f"/api/budgets/{food}", json={"amount": "9999999999.99"}).status_code
        == 200
    )


def test_transaction_query_and_patch_bounds(client):
    signup(client, "txval@example.com")
    assert client.get("/api/transactions", params={"search": "x" * 201}).status_code == 422
    assert (
        client.patch("/api/transactions/1", json={"category_id": -1}).status_code == 422
    )


# ---------------------------------------------------------------- uploads


def test_upload_sanitizes_rows_and_filename(client):
    signup(client, "uploadval@example.com")
    long_desc = "M" * 600
    long_ref = "R" * 300
    content = (
        "Date,Description,Amount,Type,Reference\n"
        f"2026-09-01,{long_desc},10.00,DEBIT,{long_ref}\n"
        "2026-09-02,Overflow,10000000000.00,DEBIT,X1\n"
        "2026-09-03,NaN,nan,DEBIT,X2\n"
        "2026-09-04,Three Decimals,10.999,DEBIT,X3\n"
    ).encode()

    r = client.post(
        "/api/uploads",
        files={"file": ("nested/dir/" + "f" * 300 + ".csv", content, "text/csv")},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert body["imported_count"] == 2  # long/rounded rows kept, bad amounts skipped
    assert len(body["error_summary"]) == 2
    assert len(body["filename"]) == 255 and "/" not in body["filename"]

    items = client.get("/api/transactions", params={"limit": 10}).json()["items"]
    by_desc = {t["description"]: t for t in items}
    assert by_desc["M" * 500]["reference"] == "R" * 200
    assert by_desc["Three Decimals"]["amount"] == "11.00"  # 10.999 rounded half-up
