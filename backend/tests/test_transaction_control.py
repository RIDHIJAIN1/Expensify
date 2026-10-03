"""Transaction-control tests: a unit of work commits fully or not at all."""

import pytest

from app.database import SessionLocal, transaction
from app.models import User
from app.services import transaction_service

from .conftest import signup


def _new_user(email: str) -> User:
    return User(email=email, password_hash="x", name=None)


def test_transaction_commits_on_success():
    db = SessionLocal()
    try:
        with transaction(db):
            user = _new_user("commit@example.com")
            db.add(user)
            db.flush()
            user_id = user.id
    finally:
        db.close()

    check = SessionLocal()
    try:
        assert check.get(User, user_id) is not None
    finally:
        check.close()


def test_transaction_rolls_back_on_failure():
    db = SessionLocal()
    user_id = None
    try:
        with pytest.raises(RuntimeError):
            with transaction(db):
                user = _new_user("rollback@example.com")
                db.add(user)
                db.flush()
                user_id = user.id
                raise RuntimeError("boom")
    finally:
        db.close()

    check = SessionLocal()
    try:
        assert user_id is not None
        assert check.get(User, user_id) is None
    finally:
        check.close()


def test_failed_recategorization_rolls_back_keyword_learning(client, monkeypatch):
    signup(client, "txrollback@example.com")
    content = (
        "Date,Description,Amount,Type,Reference\n"
        "2026-09-01,Chai Point,120.00,DEBIT,UPI-1\n"
    ).encode()
    client.post("/api/uploads", files={"file": ("s.csv", content, "text/csv")})

    tx = client.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    food = next(c for c in client.get("/api/categories").json() if c["name"] == "Food")

    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure after keyword mutation")

    monkeypatch.setattr(transaction_service, "_reclassify_matches", boom)

    with pytest.raises(RuntimeError):
        client.patch(f"/api/transactions/{tx['id']}", json={"category_id": food["id"]})

    food_after = next(c for c in client.get("/api/categories").json() if c["name"] == "Food")
    assert "chai point" not in food_after["keywords"]
