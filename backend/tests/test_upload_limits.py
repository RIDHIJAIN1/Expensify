"""API-limit guards: MAX_UPLOAD_ROWS and per-user category name uniqueness."""

from .conftest import signup


def _csv(rows: int) -> bytes:
    lines = ["Date,Description,Amount,Type,Reference"]
    for i in range(rows):
        lines.append(
            f"2026-09-{(i % 28) + 1:02d},Merchant{i},{10 + i}.00,DEBIT,ROW-{i}"
        )
    return "\n".join(lines).encode()


def test_upload_at_row_limit_is_accepted(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_ROWS", 3)
    signup(client, "rowlimit-ok@example.com")
    r = client.post("/api/uploads", files={"file": ("ok.csv", _csv(3), "text/csv")})
    assert r.status_code == 201
    assert r.json()["imported_count"] == 3


def test_upload_over_row_limit_is_rejected(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_ROWS", 3)
    signup(client, "rowlimit-bad@example.com")
    r = client.post("/api/uploads", files={"file": ("big.csv", _csv(4), "text/csv")})
    assert r.status_code == 400
    assert "too many rows" in r.json()["detail"].lower()
    assert client.get("/api/transactions").json()["total"] == 0
    assert client.get("/api/uploads").json() == []


def test_duplicate_category_name_is_rejected(client):
    signup(client, "dupcat@example.com")
    first = client.post("/api/categories", json={"name": "Dupes"})
    assert first.status_code == 201
    r = client.post("/api/categories", json={"name": "Dupes"})
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"].lower()


def test_rename_category_to_existing_name_is_rejected(client):
    signup(client, "renamedup@example.com")
    alpha = client.post("/api/categories", json={"name": "Alpha"}).json()
    beta = client.post("/api/categories", json={"name": "Beta"}).json()
    r = client.patch(f"/api/categories/{beta['id']}", json={"name": "Alpha"})
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"].lower()
    names = {c["name"] for c in client.get("/api/categories").json()}
    assert names == {"Alpha", "Beta"} | {
        "Food", "Travel", "Utilities", "Housing", "Shopping",
        "Entertainment", "Healthcare", "Income", "Other",
    }
    assert alpha["id"] != beta["id"]
