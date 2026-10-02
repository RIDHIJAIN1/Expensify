from .conftest import sample_csv_bytes, signup


def _setup(client):
    signup(client, "e@example.com")
    client.post(
        "/api/uploads", files={"file": ("s.csv", sample_csv_bytes(), "text/csv")}
    )


def test_export_csv(client):
    _setup(client)
    r = client.get("/api/export/csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text = r.text
    assert "Date" in text and "Category" in text
    assert "Swiggy" in text


def test_export_pdf(client):
    _setup(client)
    r = client.get("/api/export/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
