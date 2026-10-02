from .conftest import sample_csv_bytes, signup


def test_set_list_and_delete_budget(client):
    signup(client, "budget@example.com")
    client.post("/api/uploads", files={"file": ("s.csv", sample_csv_bytes(), "text/csv")})

    cats = client.get("/api/categories").json()
    food = next(c for c in cats if c["name"] == "Food")

    r = client.put(f"/api/budgets/{food['id']}", json={"amount": "1000.00"})
    assert r.status_code == 200
    body = r.json()
    assert body["category_id"] == food["id"]
    assert body["category_name"] == "Food"
    assert float(body["spent"]) > 0
    assert body["over"] is True  # all-time Food spend far exceeds ₹1,000

    budgets = client.get("/api/budgets").json()
    assert len(budgets) == 1
    assert budgets[0]["percent"] > 100

    assert client.delete(f"/api/budgets/{food['id']}").status_code == 200
    assert client.get("/api/budgets").json() == []


def test_budget_requires_owned_category(client):
    signup(client, "b1@example.com")
    assert (
        client.put("/api/budgets/999999", json={"amount": "500.00"}).status_code == 404
    )
