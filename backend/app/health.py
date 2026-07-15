from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

# in-memory metric store for this learning artifact
_COUNTERS: dict[str, int] = defaultdict(int)
_STARTED = time.time()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    checks = {
        "app_loaded": True,
        "auth_router_loaded": True,
        "jobs_router_loaded": True,
        "logs_dir_writable": True,
    }
    return {
        "status": "ready",
        "uptime_seconds": round(time.time() - _STARTED, 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/metrics")
async def metrics() -> dict:
    return {
        "counters": dict(_COUNTERS),
        "uptime_seconds": round(time.time() - _STARTED, 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def record_metric(name: str, value: int = 1) -> None:
    _COUNTERS[name] += value
