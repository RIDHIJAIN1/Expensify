from .conftest import sample_csv_bytes, sample_row_count, signup

N = sample_row_count()


def _upload(client, filename="s.csv", content=None):
    return client.post(
        "/api/uploads",
        files={"file": (filename, content if content is not None else sample_csv_bytes(), "text/csv")},
    )


def test_upload_imports_all_rows(client):
    signup(client, "u@example.com")
    r = _upload(client)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert body["imported_count"] == N
    assert body["duplicate_count"] == 0


def test_reupload_is_fully_deduplicated(client):
    signup(client, "u@example.com")
    _upload(client)
    r2 = _upload(client)
    body = r2.json()
    assert body["status"] == "COMPLETED"
    assert body["imported_count"] == 0
    assert body["duplicate_count"] == N


def test_malformed_header_fails_upload(client):
    signup(client, "m@example.com")
    r = _upload(client, content=b"Wrong,Header,Cols\n1,2,3\n")
    assert r.status_code == 201
    assert r.json()["status"] == "FAILED"


def test_non_csv_extension_rejected(client):
    signup(client, "n@example.com")
    r = client.post(
        "/api/uploads", files={"file": ("evil.txt", b"hello world", "text/plain")}
    )
    assert r.status_code == 400


def test_partial_bad_rows_skipped(client):
    signup(client, "p@example.com")
    content = (
        "Date,Description,Amount,Type,Reference\n"
        "2026-09-01,Swiggy,428.50,DEBIT,UPI-1\n"
        "bad-date,Bad,99,DEBIT,X\n"
    ).encode()
    r = _upload(client, content=content)
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert body["imported_count"] == 1
    assert body["error_summary"] is not None
    assert len(body["error_summary"]) == 1


def test_categories_are_classified(client):
    signup(client, "c@example.com")
    _upload(client)
    items = client.get("/api/transactions", params={"limit": 100}).json()["items"]
    by_desc = {t["description"]: t["category_name"] for t in items}
    assert by_desc["Swiggy"] == "Food"
    assert by_desc["Uber"] == "Travel"
    assert by_desc["Amazon"] == "Shopping"
    assert by_desc["Salary"] == "Income"
