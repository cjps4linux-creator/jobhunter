from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "app.jsonl"


def test_correlation_header_present():
    response = client.get("/api/jobs/today")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    cid = response.headers["X-Correlation-ID"]
    assert len(cid) > 0


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert "uptime_seconds" in body


def test_metrics_endpoint_exposes_prometheus_text():
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "jobhunter_request_total" in response.text


def test_request_logs_written():
    response = client.get("/api/jobs/today")
    assert response.status_code == 200
    cid = response.headers["X-Correlation-ID"]
    assert LOG_PATH.exists(), "log file not created"
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    matches = [
        json.loads(line)
        for line in lines
        if json.loads(line).get("correlation_id") == cid
    ]
    assert len(matches) >= 1
    record = matches[-1]
    assert record["event"] == "request_complete"
    assert "duration_ms" in record
    assert record["path"] == "/api/jobs/today"
