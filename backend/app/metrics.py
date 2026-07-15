from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Response

router = APIRouter(prefix="/metrics", tags=["metrics"])

REQUEST_COUNT = "http_requests_total"
REQUEST_LATENCY = "http_request_duration_seconds"
ERROR_COUNT = "http_errors_total"
ACTIVE_REQUESTS = "http_requests_in_flight"

_labels = ["method", "path", "status"]


def _counter_value(counter: dict[tuple[str, ...], int], labels: tuple[str, ...]) -> int:
    return counter.get(labels, 0)


class MetricsStore:
    def __init__(self) -> None:
        self._counters: dict[tuple[str, ...], int] = {}
        self._latencies: list[float] = []
        self._in_flight: dict[tuple[str, ...], int] = {}

    def record_request(
        self, method: str, path: str, status: int, duration: float
    ) -> None:
        labels = (method, path, str(status))
        self._counters[labels] = _counter_value(self._counters, labels) + 1
        self._latencies.append(duration)
        active_labels = (method, path)
        self._in_flight[active_labels] = max(
            0, self._in_flight.get(active_labels, 1) - 1
        )

    def increment_in_flight(self, method: str, path: str) -> None:
        active_labels = (method, path)
        self._in_flight[active_labels] = self._in_flight.get(active_labels, 0) + 1

    def render(self) -> str:
        lines: list[str] = []

        total = sum(self._counters.values())
        lines.append(f"# TYPE {REQUEST_COUNT} counter")
        total_labels = "method=\"all\",path=\"all\",status=\"all\""
        lines.append(f"{REQUEST_COUNT}{{{total_labels}}} {total}")
        for labels, value in self._counters.items():
            method, path, status = labels
            label_parts = (
                f'{_labels[0]}="{method}"',
                f'{_labels[1]}="{path}"',
                f'{_labels[2]}="{status}"',
            )
            lines.append(f"{REQUEST_COUNT}{{{','.join(label_parts)}}} {value}")

        lines.append(f"# TYPE {REQUEST_LATENCY} histogram")
        if self._latencies:
            buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
            for bucket in buckets:
                count = sum(1 for latency in self._latencies if latency <= bucket)
                lines.append(f"{REQUEST_LATENCY}_bucket{{le=\"{bucket}\"}} {count}")
            lines.append(
                f"{REQUEST_LATENCY}_bucket{{le=\"+Inf\"}} {len(self._latencies)}"
            )
            lines.append(f"{REQUEST_LATENCY}_sum {sum(self._latencies):.6f}")
            lines.append(f"{REQUEST_LATENCY}_count {len(self._latencies)}")
        else:
            lines.append(f"{REQUEST_LATENCY}_bucket{{le=\"+Inf\"}} 0")
            lines.append(f"{REQUEST_LATENCY}_sum 0")
            lines.append(f"{REQUEST_LATENCY}_count 0")

        error_total = sum(
            value
            for labels, value in self._counters.items()
            if int(labels[2]) >= 500
        )
        lines.append(f"# TYPE {ERROR_COUNT} counter")
        lines.append(f"{ERROR_COUNT} {error_total}")
        for labels, value in self._counters.items():
            method, path, status = labels
            if int(status) >= 500:
                label_parts = (
                    f'{_labels[0]}="{method}"',
                    f'{_labels[1]}="{path}"',
                )
                lines.append(f"{ERROR_COUNT}{{{','.join(label_parts)}}} {value}")

        lines.append(f"# TYPE {ACTIVE_REQUESTS} gauge")
        lines.append(f"{ACTIVE_REQUESTS} {sum(self._in_flight.values())}")
        for labels, value in self._in_flight.items():
            method, path = labels
            label_parts = (
                f'{_labels[0]}="{method}"',
                f'{_labels[1]}="{path}"',
            )
            lines.append(f"{ACTIVE_REQUESTS}{{{','.join(label_parts)}}} {value}")

        return "\n".join(lines) + "\n"


metrics_store = MetricsStore()


class MetricsMiddleware:
    def __init__(self, app: object) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "unknown")
        metrics_store.increment_in_flight(method, path)
        start = perf_counter()
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = perf_counter() - start
            metrics_store.record_request(method, path, status_code, duration)


@router.get("", include_in_schema=False)
async def metrics() -> Response:
    payload = metrics_store.render()
    return Response(payload, media_type="text/plain; version=0.0.4")
