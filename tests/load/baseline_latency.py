from __future__ import annotations

import json
import time
import urllib.request

from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
REQUESTS = 50
REPORT = Path(__file__).resolve().parents[2] / "artifacts" / "b5" / "baseline-latency-report.json"


def main() -> None:
    latencies = []
    errors = 0
    for _ in range(REQUESTS):
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as response:
                response.read()
                latencies.append((time.perf_counter() - start) * 1000)
        except Exception:
            errors += 1

    latencies.sort()
    count = len(latencies)
    summary = {
        "requests": count,
        "errors": errors,
        "min_ms": round(latencies[0], 3) if latencies else None,
        "p50_ms": round(latencies[int(count * 0.5)], 3) if latencies else None,
        "p95_ms": round(latencies[int(count * 0.95)], 3) if latencies else None,
        "max_ms": round(latencies[-1], 3) if latencies else None,
        "service_url": BASE_URL,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
