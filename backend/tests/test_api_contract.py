import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SNAPSHOT = Path(__file__).resolve().parent / "snapshots" / "openapi.json"


def test_openapi_contract_matches_snapshot():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert schema == snapshot


def test_openapi_required_contract_paths():
    paths = client.get("/openapi.json").json().get("paths", {})
    assert "/health" in paths
    assert "/ready" in paths


def test_openapi_servers_are_explicit():
    schema = client.get("/openapi.json").json()
    servers = schema.get("servers", [])
    if not servers:
        return
    assert servers[0].get("url") == "http://127.0.0.1:8000"


def test_openapi_api_title():
    schema = client.get("/openapi.json").json()
    assert schema.get("info", {}).get("title") == "JobHunter API"
