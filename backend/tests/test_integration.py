from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "app.jsonl"


def test_login_flow_end_to_end():
    payload = {"username": "user", "password": "password"}
    login = client.post("/auth/token", data=payload)
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "user"
