from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()
_STARTED = time.time()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    return {
        "status": "ready",
        "uptime_seconds": round(time.time() - _STARTED, 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
