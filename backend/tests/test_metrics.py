from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_prometheus_text():
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_metrics_records_request_counters():
    client.get("/health")
    client.get("/metrics")
    response = client.get("/metrics")
    body = response.text
    assert "http_requests_total" in body
    assert "http_errors_total" in body


def test_metrics_records_active_requests():
    client.get("/health")
    response = client.get("/metrics")
    assert "http_requests_in_flight" in response.text
