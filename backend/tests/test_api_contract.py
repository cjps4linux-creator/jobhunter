from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
OPENAPI_PATH = Path(__file__).resolve().parents[2] / "tests" / "snapshots" / "openapi.json"


def test_openapi_contract_snapshot_exists():
    assert OPENAPI_PATH.exists(), f"Missing snapshot: {OPENAPI_PATH}"


def test_openapi_contract_matches_snapshot():
    current = client.get("/openapi.json").json()
    expected = __import__("json").loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert current["info"]["title"] == expected["info"]["title"]
    assert current["info"]["version"] == expected["info"]["version"]
    assert set(current.get("paths", {}).keys()) == set(expected.get("paths", {}).keys())
    for path, methods in expected.get("paths", {}).items():
        for method, meta in methods.items():
            assert method in current.get("paths", {}).get(path, {}), f"missing {path.upper()} {method}"
            current_method = current["paths"][path][method]
            assert current_method.get("summary") == meta.get("summary"), f"summary drift {path.upper()} {method}"
            current_schema = current_method.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})
            expected_schema = meta.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})
            assert current_schema == expected_schema, f"schema drift {path.upper()} {method}"


def test_openapi_required_contract_paths():
    paths = client.get("/openapi.json").json().get("paths", {})
    assert "/health" in paths
    assert "/ready" in paths
    assert "/metrics" in paths
    assert "/auth/token" in paths
    assert "/auth/refresh" in paths
    assert "/auth/me" in paths
    assert "/api/jobs/today" in paths
