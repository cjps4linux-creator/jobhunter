from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.jobs import (
    matches_keywords,
    make_id,
    normalize,
    parse_date,
)


client = TestClient(app)


# ---- Unit tests for pure helpers ----


def test_normalize_lowercases_and_strips_noise():
    assert normalize("Python & React!") == "pythonreact"


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


def test_parse_date_invalid_returns_none():
    assert parse_date("not-a-date") is None
    assert parse_date("") is None


def test_matches_keywords_true_on_title_hit():
    assert matches_keywords(
        type(
            "Job",
            (),
            {"title": "Senior Python Backend Engineer", "tags": []},
        )()
    ) is True


def test_matches_keywords_false_when_no_hit():
    assert matches_keywords(
        type(
            "Job",
            (),
            {"title": "Office Receptionist", "tags": []},
        )()
    ) is False


# ---- FastAPI route checks ----


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_jobs_today_returns_list_schema():
    response = client.get("/api/jobs/today")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    if body:
        assert "id" in body[0]
        assert "title" in body[0]
        assert "source" in body[0]


# ---- Error-path coverage for fetchers ----


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
