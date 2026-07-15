from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_returns_tokens():
    payload = {"username": "user", "password": "password"}
    response = client.post("/auth/token", data=payload)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_rejects_wrong_password():
    payload = {"username": "user", "password": "wrong"}
    response = client.post("/auth/token", data=payload)
    assert response.status_code == 401


def test_me_returns_user_profile():
    payload = {"username": "user", "password": "password"}
    login = client.post("/auth/token", data=payload).json()
    access = login["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "user"
    assert body["role"] == "user"


def test_refresh_rotates_tokens():
    payload = {"username": "user", "password": "password"}
    login = client.post("/auth/token", data=payload).json()
    refresh = login["refresh_token"]
    body = client.post("/auth/refresh", json={"refresh_token": refresh}).json()
    assert body["refresh_token"] != refresh


def test_reused_refresh_token_is_rejected():
    payload = {"username": "user", "password": "password"}
    login = client.post("/auth/token", data=payload).json()
    refresh = login["refresh_token"]
    client.post("/auth/refresh", json={"refresh_token": refresh})
    response = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 401


def test_me_rejects_invalid_access():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer eyJhbG...invalid"},
    )
    assert response.status_code == 401
