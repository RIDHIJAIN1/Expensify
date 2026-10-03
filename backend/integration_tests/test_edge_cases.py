"""Edge cases and negative-path coverage for every API area.

Where the current behaviour is surprising, the test pins the *actual* behaviour
and names it explicitly so regressions/decisions are visible.
"""

import uuid

import httpx

from .conftest import BASE_URL, make_csv, sample_csv_bytes


def fresh_email() -> str:
    return f"edge_{uuid.uuid4().hex[:10]}@example.com"


# ---------------------------------------------------------------- auth


def test_signup_validation_errors(api):
    assert api.post("/api/auth/signup", json={"email": "not-an-email", "password": "12345678"}).status_code == 422
    assert api.post("/api/auth/signup", json={"email": fresh_email(), "password": "1234567"}).status_code == 422
    assert api.post("/api/auth/signup", json={"email": fresh_email(), "password": "x" * 129}).status_code == 422
    assert api.post("/api/auth/signup", json={}).status_code == 422


def test_signup_password_boundaries(server_ready):
    from .conftest import Api

    a = Api()
    try:
        assert a.post("/api/auth/signup", json={"email": fresh_email(), "password": "12345678"}).status_code == 201
        assert a.post("/api/auth/signup", json={"email": fresh_email(), "password": "x" * 72}).status_code == 201
    finally:
        a.close()


def test_signup_password_longer_than_bcrypt_limit(server_ready):
    from .conftest import Api

    a = Api()
    try:
        resp = a.post("/api/auth/signup", json={"email": fresh_email(), "password": "x" * 128})
        assert resp.status_code in (201, 422), resp.text
    finally:
        a.close()


def test_signup_without_name(server_ready):
    from .conftest import Api

    a = Api()
    try:
        resp = a.post("/api/auth/signup", json={"email": fresh_email(), "password": "12345678"})
        assert resp.status_code == 201 and resp.json()["name"] is None
    finally:
        a.close()


def test_login_unknown_user(api):
    resp = api.post("/api/auth/login", json={"email": fresh_email(), "password": "12345678"})
    assert resp.status_code == 401


def test_refresh_rejects_access_token_and_tampering(server_ready):
    from .conftest import Api

    a = Api()
    try:
        a.signup()
        access = a.client.cookies.get("access_token")
        assert access
        with httpx.Client(base_url=BASE_URL, timeout=30) as probe:
            assert probe.post(
                "/api/auth/refresh", headers={"Cookie": f"refresh_token={access}"}
            ).status_code == 401
            assert probe.post(
                "/api/auth/refresh", headers={"Cookie": "refresh_token=abc.def.ghi"}
            ).status_code == 401
            assert probe.post("/api/auth/refresh").status_code == 401
    finally:
        a.close()


def test_tampered_access_token_rejected(server_ready):
    from .conftest import Api

    a = Api()
    try:
        a.signup()
        resp = a.client.get(
            "/api/auth/me", headers={"Cookie": "access_token=tampered.token.value"}
        )
        assert resp.status_code == 401
    finally:
        a.close()


# ---------------------------------------------------------------- categories


def test_category_validation(api):
    cat_id = api.post("/api/categories", json={"name": "Temp", "keywords": []}).json()["id"]
    assert api.post("/api/categories", json={"name": "", "keywords": []}).status_code == 422
    assert api.post("/api/categories", json={"name": "x" * 61, "keywords": []}).status_code == 422
    assert api.post("/api/categories", json={"name": "x", "keywords": "notalist"}).status_code == 422
    assert api.patch("/api/categories/99999999", json={"name": "ok"}).status_code == 404
    assert api.delete("/api/categories/99999999").status_code == 404
    assert api.delete(f"/api/categories/{api.categories_by_name()['Food']}").status_code == 400


def test_category_rename_over_column_limit(api):
    cat_id = api.post("/api/categories", json={"name": "Temp", "keywords": []}).json()["id"]
    assert api.patch(f"/api/categories/{cat_id}", json={"name": "y" * 61}).status_code == 422


def test_patch_empty_body_leaves_category_unchanged(api):
    cat = api.post("/api/categories", json={"name": "Stable", "keywords": ["a"]}).json()
    assert api.patch(f"/api/categories/{cat['id']}", json={}).json() == cat


def test_deleting_custom_category_uncategorizes_and_removes_budget(api_with_data):
    api, _ = api_with_data
    cat = api.post("/api/categories", json={"name": "TempCat", "keywords": []}).json()
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    api.patch(f"/api/transactions/{tx['id']}", json={"category_id": cat["id"]})
    api.put(f"/api/budgets/{cat['id']}", json={"amount": "1000.00"})
    assert len(api.get("/api/budgets").json()) == 1

    assert api.delete(f"/api/categories/{cat['id']}").status_code == 200
    assert api.get(f"/api/transactions/{tx['id']}").json()["category_id"] is None
    assert api.get("/api/budgets").json() == []


# ---------------------------------------------------------------- uploads


def test_upload_validation(api):
    assert api.post("/api/uploads", files={"file": ("evil.txt", b"x,y,z", "text/plain")}).status_code == 400
    assert api.post("/api/uploads", files={"file": ("empty.csv", b"", "text/csv")}).status_code == 400
    assert api.post("/api/uploads", files={"file": ("bin.csv", b"Date,Description\n\x00\x01\x02", "text/csv")}).status_code == 400
    assert api.post(
        "/api/uploads", files={"file": ("x.csv", b"D" * (10 * 1024 * 1024 + 1), "text/csv")}
    ).status_code == 400
    assert api.get("/api/uploads/99999999").status_code == 404


def test_upload_empty_data_gap(api):
    resp = api.upload(b"Date,Description,Amount,Type,Reference\n", "header_only.csv")
    assert resp.status_code == 201
    assert resp.json()["status"] == "COMPLETED"
    assert resp.json()["imported_count"] == 0


def test_upload_invalid_header_is_failed_upload_not_http_error(api):
    resp = api.upload(b"Wrong,Header\n1,2\n", "bad_header.csv")
    assert resp.status_code == 201
    assert resp.json()["status"] == "FAILED"
    assert resp.json()["error_summary"]


def test_upload_uppercase_extension_is_accepted(api):
    resp = api.upload(sample_csv_bytes(), "STATEMENT.CSV")
    assert resp.status_code == 201 and resp.json()["status"] == "COMPLETED"


def test_upload_bom_crlf_and_quoted_commas(api):
    content = (
        b"\xef\xbb\xbfDate,Description,Amount,Type,Reference\r\n"
        b'2026-09-01,"Amazon, Inc",100.00,DEBIT,UPI-1\r\n'
        b'2026-09-02,"Quoted ""merchant""",50.00,DEBIT,UPI-2\r\n'
    )
    resp = api.upload(content, "tricky.csv")
    assert resp.status_code == 201
    assert resp.json()["imported_count"] == 2
    rows = api.get("/api/transactions", params={"search": "Amazon"}).json()["items"]
    assert rows and rows[0]["description"] == "Amazon, Inc"


def test_upload_latin1_fallback(api):
    content = "Date,Description,Amount,Type,Reference\n2026-09-01,Caf\xe9 Mocha,80.00,DEBIT,X1\n".encode("latin-1")
    assert api.upload(content, "latin1.csv").json()["status"] == "COMPLETED"


def test_upload_parses_currency_formats_and_type_synonyms(api):
    content = make_csv([
        ("2026-09-01", "Rupee Vendor", "₹1,234.56", "DR", "A1"),
        ("2026-09-02", "Rs Vendor", "Rs 500", "PAYMENT", "A2"),
        ("2026-09-03", "Paren Vendor", "(250.00)", "WITHDRAWAL", "A3"),
        ("2026-09-04", "Deposit Vendor", "1000", "DEPOSIT", "A4"),
        ("2026-09-05", "Zero Vendor", "0", "DEBIT", "A5"),
    ])
    resp = api.upload(content, "formats.csv")
    assert resp.json()["imported_count"] == 5
    by_ref = {t["reference"]: t for t in api.get("/api/transactions", params={"limit": 10}).json()["items"]}
    assert by_ref["A1"]["amount"] == "1234.56" and by_ref["A1"]["type"] == "DEBIT"
    assert by_ref["A2"]["amount"] == "500.00"
    assert by_ref["A3"]["amount"] == "-250.00"
    assert by_ref["A4"]["type"] == "CREDIT" and by_ref["A4"]["category_name"] == "Income"
    assert by_ref["A5"]["amount"] == "0.00"


def test_upload_row_errors_are_reported_not_fatal(api):
    content = make_csv([
        ("bad-date", "Bad Date", "10", "DEBIT", "E1"),
        ("2026-09-01", "", "10", "DEBIT", "E2"),
        ("2026-09-02", "Bad Amount", "abc", "DEBIT", "E3"),
        ("2026-09-03", "Bad Type", "10", "TRANSFER", "E4"),
        ("2026-09-04", "6 Columns", "10", "DEBIT", "E5", "EXTRA"),
        ("2026-09-05", "Good Row", "10", "DEBIT", "E6"),
    ])
    resp = api.upload(content, "errors.csv")
    body = resp.json()
    assert body["imported_count"] == 1
    assert len(body["error_summary"]) == 5


def test_upload_intra_file_duplicates_counted(api):
    content = make_csv([
        ("2026-09-01", "Same Merchant", "10.00", "DEBIT", "DUP-1"),
        ("2026-09-01", "Same Merchant", "10.00", "DEBIT", "DUP-1"),
        ("2026-09-01", "Same Merchant", "10.00", "DEBIT", "DUP-2"),
    ])
    body = api.upload(content, "dups.csv").json()
    assert body["imported_count"] == 1
    assert body["duplicate_count"] == 2


# ---------------------------------------------------------------- transactions


def test_transaction_query_validation(api):
    assert api.get("/api/transactions", params={"limit": 0}).status_code == 422
    assert api.get("/api/transactions", params={"limit": 1001}).status_code == 422
    assert api.get("/api/transactions", params={"offset": -1}).status_code == 422
    assert api.get("/api/transactions", params={"date_from": "not-a-date"}).status_code == 422
    assert api.get("/api/transactions/99999999").status_code == 404


def test_transaction_search_percent_is_wildcard(api_with_data, sample_count):
    api, _ = api_with_data
    resp = api.get("/api/transactions", params={"search": "%"})
    assert resp.json()["total"] == sample_count


def test_transaction_patch_validation(api_with_data):
    api, _ = api_with_data
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    assert api.patch("/api/transactions/99999999", json={"category_id": None}).status_code == 404
    assert api.patch(f"/api/transactions/{tx['id']}", json={"category_id": 99999999}).status_code == 400


def test_transaction_patch_empty_body_clears_category(api_with_data):
    api, _ = api_with_data
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    assert tx["category_id"] is not None
    resp = api.patch(f"/api/transactions/{tx['id']}", json={})
    assert resp.status_code == 200
    assert resp.json()["transaction"]["category_id"] is None


# ---------------------------------------------------------------- budgets


def test_budget_validation(api_with_data):
    api, _ = api_with_data
    food = api.categories_by_name()["Food"]
    assert api.put(f"/api/budgets/{food}", json={"amount": "0"}).status_code == 422
    assert api.put(f"/api/budgets/{food}", json={"amount": "-1"}).status_code == 422
    assert api.put(f"/api/budgets/{food}", json={}).status_code == 422
    assert api.put(f"/api/budgets/{food}", json={"amount": "abc"}).status_code == 422
    assert api.put("/api/budgets/99999999", json={"amount": "100"}).status_code == 404
    assert api.delete("/api/budgets/99999999").status_code == 404


def test_budget_future_window_shows_zero_spend(api_with_data):
    api, _ = api_with_data
    food = api.categories_by_name()["Food"]
    resp = api.put(
        f"/api/budgets/{food}",
        params={"date_from": "2099-01-01", "date_to": "2099-12-31"},
        json={"amount": "1000.00"},
    )
    body = resp.json()
    assert body["spent"] == "0" and body["percent"] == 0.0 and body["over"] is False


# ---------------------------------------------------------------- summary / insights


def test_summary_reversed_range_is_empty(api_with_data):
    api, _ = api_with_data
    body = api.get(
        "/api/summary", params={"date_from": "2026-12-31", "date_to": "2026-01-01"}
    ).json()
    assert body["transaction_count"] == 0
    assert body["total_income"] == "0" and body["total_spent"] == "0"
    assert body["by_category"] == [] and body["by_month"] == []


def test_insights_requires_dates(api):
    assert api.get("/api/insights").status_code == 422
    assert api.get("/api/insights", params={"date_from": "bad", "date_to": "2026-01-01"}).status_code == 422
    assert api.get("/api/insights", params={"date_from": "2026-01-01", "date_to": "2026-01-31"}).status_code == 200


def test_summary_insights_export_require_auth(server_ready):
    with httpx.Client(base_url=BASE_URL, timeout=30) as anon:
        assert anon.get("/api/summary").status_code == 401
        assert anon.get("/api/insights", params={"date_from": "2026-01-01", "date_to": "2026-01-02"}).status_code == 401
        assert anon.get("/api/export/csv").status_code == 401
        assert anon.get("/api/export/pdf").status_code == 401
        assert anon.get("/api/uploads").status_code == 401
        assert anon.get("/api/categories").status_code == 401
        assert anon.get("/api/budgets").status_code == 401
        assert anon.patch("/api/transactions/1", json={"category_id": None}).status_code == 401
