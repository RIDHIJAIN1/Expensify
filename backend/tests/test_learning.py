from .conftest import signup

UNKNOWN = (
    "Date,Description,Amount,Type,Reference\n"
    "2026-09-01,Chai Point,120.00,DEBIT,UPI-1\n"
    "2026-09-02,Chai Point,90.00,DEBIT,UPI-2\n"
).encode()


def test_recategorization_learns_and_reclassifies(client):
    signup(client, "learn@example.com")
    client.post("/api/uploads", files={"file": ("s.csv", UNKNOWN, "text/csv")})

    items = client.get("/api/transactions", params={"limit": 10}).json()["items"]
    assert len(items) == 2
    assert all(t["category_name"] == "Other" for t in items)

    food = next(c for c in client.get("/api/categories").json() if c["name"] == "Food")
    target = items[0]

    r = client.patch(f"/api/transactions/{target['id']}", json={"category_id": food["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["learned_keyword"] == "chai point"
    assert body["reclassified"] == 1  # the other uncategorized Chai Point row
    assert body["transaction"]["category_name"] == "Food"

    food_after = next(c for c in client.get("/api/categories").json() if c["name"] == "Food")
    assert "chai point" in food_after["keywords"]

    # A later import of the same merchant is auto-classified.
    more = (
        "Date,Description,Amount,Type,Reference\n"
        "2026-10-01,Chai Point,150.00,DEBIT,UPI-3\n"
    ).encode()
    client.post("/api/uploads", files={"file": ("s2.csv", more, "text/csv")})
    rows = client.get("/api/transactions", params={"search": "Chai"}).json()["items"]
    imported = next(t for t in rows if t["reference"] == "UPI-3")
    assert imported["category_name"] == "Food"
