from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict

REQUEST_COUNT: Dict[str, int] = defaultdict(int)
REQUEST_LATENCY: Dict[str, float] = {}
ERROR_COUNT: Dict[str, int] = defaultdict(int)
ACTIVE_REQUESTS: int = 0


class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        global ACTIVE_REQUESTS
        ACTIVE_REQUESTS += 1
        method = scope["method"]
        path = scope["path"]
        start = time.perf_counter()
        status_code = 500
        try:
            await self.app(scope, receive, send)
            status_code = 200
            return
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            key = f"{method.upper()} {path}"
            REQUEST_COUNT[key] += 1
            REQUEST_LATENCY[key] = duration_ms
            if status_code >= 400:
                ERROR_COUNT[key] += 1
            ACTIVE_REQUESTS -= 1


def router():
    from fastapi import APIRouter
    from fastapi.responses import PlainTextResponse

    router = APIRouter()

    @router.get(
        "/metrics",
        response_class=PlainTextResponse,
        tags=["metrics"],
        summary="Return application metrics",
    )
    async def get_metrics():
        lines = [
            "# HELP jobhunter_request_total Total HTTP requests",
            "# TYPE jobhunter_request_total counter",
        ]
        for key, value in sorted(REQUEST_COUNT.items()):
            lines.append(f'jobhunter_request_total{{route="{key}"}} {value}')

        lines += [
            "",
            "# HELP jobhunter_request_latency_ms_last_request Last request latency",
            "# TYPE jobhunter_request_latency_ms_last_request gauge",
        ]
        for key, value in sorted(REQUEST_LATENCY.items()):
            line = (
                f'jobhunter_request_latency_ms_last_request{{route="{key}"}} '
                f'{value:.3f}'
            )
            lines.append(line)

        lines += [
            "",
            "# HELP jobhunter_request_errors_total Total failed requests",
            "# TYPE jobhunter_request_errors_total counter",
        ]
        for key, value in sorted(ERROR_COUNT.items()):
            line = f'jobhunter_request_errors_total{{route="{key}"}} {value}'
            lines.append(line)

        lines += [
            "",
            "# HELP jobhunter_active_requests Current in-flight requests",
            "# TYPE jobhunter_active_requests gauge",
            f"jobhunter_active_requests {ACTIVE_REQUESTS}",
            "",
        ]
        return "\n".join(lines) + "\n"

    return router


metrics_router = router()
