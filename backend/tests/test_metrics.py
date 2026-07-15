from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_prometheus_format():
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "jobhunter_request_total" in body
    assert "jobhunter_request_latency_ms_last_request" in body
    assert "jobhunter_active_requests" in body
