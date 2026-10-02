from fastapi.testclient import TestClient

from app.main import app

from .conftest import sample_csv_bytes, signup


def test_user_cannot_see_other_users_data(client):
    # User A uploads data
    signup(client, "a@example.com")
    r = client.post(
        "/api/uploads", files={"file": ("s.csv", sample_csv_bytes(), "text/csv")}
    )
    assert r.status_code == 201
    tx = client.get("/api/transactions").json()["items"][0]

    # User B has an empty account and cannot access A's rows
    with TestClient(app) as client_b:
        signup(client_b, "b@example.com")
        assert client_b.get("/api/transactions").json()["total"] == 0
        assert client_b.get(f"/api/transactions/{tx['id']}").status_code == 404
        # B cannot see A's categories
        b_cats = client_b.get("/api/categories").json()
        # B's categories are their own seeded set, not A's custom ones — but
        # crucially A's category ids must not be addressable by B
        a_cat_id = tx["category_id"]
        assert client_b.patch(
            f"/api/transactions/{tx['id']}", json={"category_id": a_cat_id}
        ).status_code == 404
