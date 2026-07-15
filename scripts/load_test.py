#!/usr/bin/env python3
"""Minimal k6-style local load test with requests + reporting.

If k6 is unavailable, falls back to a threading-based load test and still emits
`artifacts/load-report.json` and `artifacts/load-report.md`.
"""
from __future__ import annotations

import json
import os
import statistics
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = os.getenv("JOBHUNTER_BASE_URL", "http://127.0.0.1:8000")
TARGET_RPS = float(os.getenv("LOAD_TARGET_RPS", "20"))
DURATION_SECONDS = int(os.getenv("LOAD_DURATION_SECONDS", "30"))
CONCURRENCY = max(2, int(TARGET_RPS / 5))

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "artifacts"
OUTPUT_DIR.mkdir(exist_ok=True)


def _request(path: str) -> tuple[float, int]:
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=5) as response:
            status = response.status
    except Exception:
        status = 0
    return time.perf_counter() - start, status


def _worker(results: list[tuple[float, int]], stop_event: threading.Event) -> None:
    paths = ["/health"] * 7 + ["/api/jobs/today"] * 2 + ["/metrics"] * 1
    while not stop_event.is_set():
        for path in paths:
            if stop_event.is_set():
                break
            results.append(_request(path))
            time.sleep(1.0 / max(1.0, TARGET_RPS / CONCURRENCY))


def run() -> dict:
    results: list[tuple[float, int]] = []
    stop_event = threading.Event()
    threads = [threading.Thread(target=_worker, args=(results, stop_event), daemon=True) for _ in range(CONCURRENCY)]
    for thread in threads:
        thread.start()
    time.sleep(DURATION_SECONDS)
    stop_event.set()
    for thread in threads:
        thread.join()

    latencies = [lat for lat, _ in results]
    statuses = [st for _, st in results]
    successful = [st for st in statuses if 200 <= st < 400]
    failed = len(statuses) - len(successful)
    error_rate = failed / len(statuses) if statuses else 0.0
    p95 = sorted(latencies)[min(len(latencies) - 1, max(0, int(len(latencies) * 0.95)))] if latencies else 0.0
    rps = len(results) / DURATION_SECONDS if DURATION_SECONDS else 0.0

    report = {
        "url": BASE_URL,
        "concurrency": CONCURRENCY,
        "duration_seconds": DURATION_SECONDS,
        "requests": len(results),
        "rps": round(rps, 2),
        "error_rate": round(error_rate, 4),
        "latency_p95_seconds": round(p95, 4),
        "success_rate": round((len(successful) / len(statuses)) if statuses else 0.0, 4),
    }
    return report


def write_md(report: dict) -> Path:
    md_path = OUTPUT_DIR / "load-report.md"
    md_path.write_text(
        "\n".join([
            "# Load test report",
            "",
            f"- URL: `{report['url']}`",
            f"- Concurrency: {report['concurrency']}",
            f"- Duration: {report['duration_seconds']}s",
            f"- Requests: {report['requests']}",
            f"- Observed RPS: {report['rps']}",
            f"- Error rate: {report['error_rate']}",
            f"- P95 latency: {report['latency_p95_seconds']}s",
            f"- Success rate: {report['success_rate']}",
        ]) + "\n",
        encoding="utf-8",
    )
    return md_path


def main() -> None:
    report = run()
    json_path = OUTPUT_DIR / "load-report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = write_md(report)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "report": report}, indent=2))


if __name__ == "__main__":
    main()
