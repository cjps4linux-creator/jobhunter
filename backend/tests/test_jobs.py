from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.jobs import (
    make_id,
    matches_keywords,
    normalize,
    parse_date,
)

client = TestClient(app)


# ---- Fixtures ----

@pytest.fixture
def sample_job_factory():
    """Factory fixture for creating test job dicts with safe defaults."""
    def _factory(**overrides):
        base = {
            "id": "test-1",
            "title": "Senior Python Engineer",
            "company": "Acme Corp",
            "location": "Remote",
            "url": "https://acme.com/jobs/1",
            "posted_at": "2025-01-15T00:00:00Z",
            "source": "TestSource",
            "job_type": "Full-time",
            "tags": ["python", "remote"],
        }
        base.update(overrides)
        return base
    return _factory


# ---- Unit tests with parametrize ----

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Python & React!", "pythonreact"),
        ("Senior  Engineer", "seniorengineer"),
        ("C++ / Go", "cgo"),
        ("", ""),
    ],
)
def test_normalize_lowercases_and_strips_noise(text, expected):
    assert normalize(text) == expected


def test_make_id_deterministic_for_same_inputs():
    assert make_id("https://example.com/1", "src") == make_id(
        "https://example.com/1", "src"
    )
    assert make_id("a", "b") != make_id("a", "c")


@pytest.mark.parametrize(
    ("raw", "expected_tz"),
    [
        ("2025-01-02T03:04:05Z", "UTC"),
        ("2025-01-02T03:04:05+00:00", "UTC"),
        ("2025-01-02", "UTC"),
    ],
)
def test_parse_date_common_formats(raw, expected_tz):
    dt = parse_date(raw)
    assert dt is not None
    assert dt.tzinfo is not None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("not-a-date", None),
        ("", None),
        ("9999-99-99", None),
        ("2025-01-02T03:04:05", None),  # naive ISO needs explicit tz
    ],
)
def test_parse_date_invalid_returns_none(raw, expected):
    assert parse_date(raw) is expected


@pytest.mark.parametrize(
    ("title", "tags", "expected"),
    [
        ("Senior Python Backend Engineer", [], True),
        ("Office Receptionist", [], False),
        ("DevOps Engineer", ["aws", "kubernetes"], True),
        ("Marketing Manager", ["sales"], True),  # "manager" is in KEYWORDS by design
    ],
)
def test_matches_keywords_parametrized(title, tags, expected):
    assert matches_keywords(
        type("Job", (), {"title": title, "tags": tags})()
    ) is expected


# ---- Integration-style route checks ----


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_jobs_today_returns_list_schema():
    response = client.get("/api/jobs/today")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    if body:
        required_keys = [
            "id",
            "title",
            "company",
            "location",
            "url",
            "posted_at",
            "source",
            "job_type",
            "tags",
        ]
        for key in required_keys:
            assert key in body[0], f"missing {key}"


# ---- Async error-path coverage ----


@pytest.mark.anyio
async def test_fetch_remoteok_handles_timeout():
    from app.routers import jobs as jobs_mod

    fake_exc = Exception("boom")
    with patch.object(
        jobs_mod.httpx.AsyncClient, "get", side_effect=fake_exc
    ), patch.object(jobs_mod.httpx, "AsyncClient", return_value=AsyncMock()):
        result = await jobs_mod.fetch_remoteok(AsyncMock())
    assert result == []


@pytest.mark.anyio
async def test_fetch_remotive_returns_empty_on_failure():
    from app.routers import jobs as jobs_mod

    with patch.object(
        jobs_mod.httpx.AsyncClient, "get", side_effect=Exception("boom")
    ), patch.object(jobs_mod.httpx, "AsyncClient", return_value=AsyncMock()):
        result = await jobs_mod.fetch_remotive(AsyncMock())
    assert result == []
