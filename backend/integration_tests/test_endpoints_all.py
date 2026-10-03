"""End-to-end coverage of every API endpoint against a live server + Postgres."""

from decimal import Decimal

from .conftest import PASSWORD


def test_health(api):
    resp = api.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_auth_full_flow(server_ready):
    from .conftest import Api

    a = Api()
    try:
        signup = a.signup()
        assert signup.status_code == 201
        body = signup.json()
        assert set(body) == {"id", "email", "name"}
        assert body["email"] == a.email

        me = a.get("/api/auth/me")
        assert me.status_code == 200 and me.json()["id"] == body["id"]

        assert a.post("/api/auth/refresh").status_code == 200
        assert a.get("/api/auth/me").status_code == 200

        assert a.post("/api/auth/logout").status_code == 200
        assert a.get("/api/auth/me").status_code == 401

        login = a.post("/api/auth/login", json={"email": a.email, "password": PASSWORD})
        assert login.status_code == 200 and login.json()["id"] == body["id"]
        assert a.get("/api/auth/me").status_code == 200
    finally:
        a.close()


def test_signup_seeds_nine_default_categories(api):
    names = [c["name"] for c in api.get("/api/categories").json()]
    assert sorted(names) == sorted(
        ["Food", "Travel", "Utilities", "Housing", "Shopping",
         "Entertainment", "Healthcare", "Income", "Other"]
    )


def test_categories_crud(api):
    created = api.post(
        "/api/categories",
        json={"name": "Pets", "keywords": ["vet", "petfood"], "color": "#aabbcc"},
    )
    assert created.status_code == 201
    cat = created.json()
    assert cat["name"] == "Pets" and cat["is_custom"] is True
    assert cat["keywords"] == ["vet", "petfood"] and cat["color"] == "#aabbcc"

    listed = api.get("/api/categories").json()
    assert [c for c in listed if c["id"] == cat["id"]][0]["name"] == "Pets"

    updated = api.patch(
        f"/api/categories/{cat['id']}",
        json={"name": "Pet Care", "keywords": ["vet", "grooming"], "color": "#000000"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Pet Care"
    assert updated.json()["keywords"] == ["vet", "grooming"]

    assert api.delete(f"/api/categories/{cat['id']}").status_code == 200
    ids = [c["id"] for c in api.get("/api/categories").json()]
    assert cat["id"] not in ids


def test_uploads_create_dedupe_list_get(api, sample_csv, sample_count):
    first = api.upload(sample_csv, "sample_statement.csv")
    assert first.status_code == 201
    body = first.json()
    assert body["status"] == "COMPLETED"
    assert body["total_rows"] == sample_count
    assert body["imported_count"] == sample_count
    assert body["duplicate_count"] == 0
    assert body["error_summary"] is None

    second = api.upload(sample_csv, "sample_statement.csv")
    assert second.status_code == 201
    assert second.json()["imported_count"] == 0
    assert second.json()["duplicate_count"] == sample_count

    uploads = api.get("/api/uploads").json()
    assert len(uploads) == 2
    assert uploads[0]["id"] == second.json()["id"]

    fetched = api.get(f"/api/uploads/{first.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["imported_count"] == sample_count


def test_transactions_pagination_filters_and_order(api_with_data, sample_count):
    api, _ = api_with_data

    page1 = api.get("/api/transactions", params={"limit": 10, "offset": 0}).json()
    page2 = api.get("/api/transactions", params={"limit": 10, "offset": 10}).json()
    assert page1["total"] == sample_count
    assert len(page1["items"]) == 10 and len(page2["items"]) == 10
    assert {t["id"] for t in page1["items"]}.isdisjoint({t["id"] for t in page2["items"]})
    dates = [t["date"] for t in page1["items"]]
    assert dates == sorted(dates, reverse=True)

    sept = api.get(
        "/api/transactions",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30", "limit": 1000},
    ).json()
    assert sept["total"] > 0
    assert all("2026-09-01" <= t["date"] <= "2026-09-30" for t in sept["items"])

    debits = api.get("/api/transactions", params={"type": "debit", "limit": 1000}).json()
    assert debits["total"] > 0
    assert all(t["type"] == "DEBIT" for t in debits["items"])

    food = api.categories_by_name()["Food"]
    food_rows = api.get(
        "/api/transactions", params={"category_id": food, "limit": 1000}
    ).json()
    assert food_rows["total"] > 0
    assert all(t["category_id"] == food for t in food_rows["items"])

    swiggy = api.get("/api/transactions", params={"search": "swiggy"}).json()
    assert swiggy["total"] > 0
    assert all("swiggy" in t["description"].lower() for t in swiggy["items"])

    assert api.get("/api/transactions", params={"type": "NOPE"}).json()["total"] == 0


def test_transaction_get_and_patch(api_with_data):
    api, _ = api_with_data
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    got = api.get(f"/api/transactions/{tx['id']}")
    assert got.status_code == 200 and got.json()["id"] == tx["id"]

    pets = api.post("/api/categories", json={"name": "Misc", "keywords": []}).json()
    patched = api.patch(
        f"/api/transactions/{tx['id']}", json={"category_id": pets["id"]}
    )
    assert patched.status_code == 200
    result = patched.json()
    assert result["transaction"]["category_id"] == pets["id"]
    assert result["learned_keyword"] == tx["description"].lower()
    assert result["reclassified"] >= 0

    verified = api.get(f"/api/transactions/{tx['id']}").json()
    assert verified["category_id"] == pets["id"]
    assert verified["category_name"] == "Misc"


def test_summary_matches_transactions(api_with_data, sample_count):
    api, _ = api_with_data
    rows = api.get("/api/transactions", params={"limit": 1000}).json()["items"]
    assert len(rows) == sample_count

    income = sum(Decimal(str(t["amount"])) for t in rows if t["type"] == "CREDIT")
    spent = sum(Decimal(str(t["amount"])) for t in rows if t["type"] == "DEBIT")

    summary = api.get("/api/summary").json()
    assert Decimal(str(summary["total_income"])) == income
    assert Decimal(str(summary["total_spent"])) == spent
    assert Decimal(str(summary["net"])) == income - spent
    assert summary["transaction_count"] == sample_count

    cat_total = sum(Decimal(str(c["total"])) for c in summary["by_category"])
    cat_count = sum(c["count"] for c in summary["by_category"])
    assert cat_total == spent
    assert cat_count == sum(1 for t in rows if t["type"] == "DEBIT")

    month_total = sum(Decimal(str(m["debit"])) for m in summary["by_month"])
    assert month_total == spent
    assert len(summary["top_merchants"]) <= 5
    amounts = [Decimal(str(m["total"])) for m in summary["top_merchants"]]
    assert amounts == sorted(amounts, reverse=True)

    filtered = api.get(
        "/api/summary", params={"date_from": "2026-09-01", "date_to": "2026-09-30"}
    ).json()
    assert 0 < filtered["transaction_count"] < sample_count


def test_insights_shape(api_with_data):
    api, _ = api_with_data
    resp = api.get("/api/insights", params={"date_from": "2026-07-01", "date_to": "2026-10-31"})
    assert resp.status_code == 200
    for item in resp.json():
        assert set(item) == {"icon", "tone", "title", "detail"}
        assert item["tone"] in {"positive", "warning", "neutral", "info"}


def test_budgets_crud(api_with_data):
    api, _ = api_with_data
    food = api.categories_by_name()["Food"]
    window = {"date_from": "2026-07-01", "date_to": "2026-10-31"}

    created = api.put(f"/api/budgets/{food}", params=window, json={"amount": "5000.00"})
    assert created.status_code == 200
    body = created.json()
    assert Decimal(str(body["limit"])) == Decimal("5000.00")
    assert Decimal(str(body["spent"])) > 0
    assert Decimal(str(body["remaining"])) == Decimal("5000.00") - Decimal(str(body["spent"]))
    assert body["category_name"] == "Food"

    listed = api.get("/api/budgets", params=window).json()
    assert len(listed) == 1 and listed[0]["category_id"] == food
    assert listed[0]["percent"] == round(float(Decimal(str(listed[0]["spent"])) / Decimal("5000") * 100), 1)

    updated = api.put(f"/api/budgets/{food}", params=window, json={"amount": "9000.00"})
    assert Decimal(str(updated.json()["limit"])) == Decimal("9000.00")
    assert len(api.get("/api/budgets").json()) == 1

    assert api.delete(f"/api/budgets/{food}").status_code == 200
    assert api.get("/api/budgets").json() == []
    assert api.delete(f"/api/budgets/{food}").status_code == 404


def test_user_isolation(api_with_data, second_api):
    api, _ = api_with_data
    other_upload = api.get("/api/uploads").json()[0]
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]

    assert second_api.get("/api/transactions").json()["total"] == 0
    assert second_api.get(f"/api/transactions/{tx['id']}").status_code == 404
    assert second_api.get(f"/api/uploads/{other_upload['id']}").status_code == 404
    assert second_api.get("/api/uploads").json() == []
    assert second_api.get("/api/summary").json()["transaction_count"] == 0

    foreign_cat = api.categories_by_name()["Food"]
    assert second_api.patch(
        f"/api/transactions/{tx['id']}", json={"category_id": foreign_cat}
    ).status_code == 404
    assert second_api.delete(f"/api/categories/{foreign_cat}").status_code == 404
