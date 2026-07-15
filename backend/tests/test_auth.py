from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings
from app.main import app

client = TestClient(app)
settings = get_settings()

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_auth_state():
    from app.auth import router as ar
    ar._REFRESH_JTI.clear()
    yield
    ar._REFRESH_JTI.clear()


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
    new_refresh = body["refresh_token"]
    assert new_refresh != refresh
    old_jti = jwt.get_unverified_claims(refresh).get("jti")
    new_jti = jwt.get_unverified_claims(new_refresh).get("jti")
    assert old_jti != new_jti
    assert new_jti is not None


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
