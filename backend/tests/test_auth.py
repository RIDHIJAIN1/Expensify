from .conftest import signup


def test_signup_and_me(client):
    r = signup(client, "a@example.com")
    assert r.status_code == 201
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "a@example.com"


def test_password_is_hashed_not_plaintext():
    from app.core.security import hash_password, verify_password

    hashed = hash_password("supersecret1")
    assert hashed != "supersecret1"
    assert verify_password("supersecret1", hashed)
    assert not verify_password("wrong", hashed)


def test_login_wrong_password(client):
    signup(client, "b@example.com")
    client.post("/api/auth/logout")
    r = client.post(
        "/api/auth/login", json={"email": "b@example.com", "password": "wrongpass1"}
    )
    assert r.status_code == 401


def test_protected_requires_auth(client):
    assert client.get("/api/transactions").status_code == 401
    assert client.get("/api/summary").status_code == 401
    assert client.post("/api/uploads").status_code == 401
