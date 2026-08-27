# JobHunter

Lightweight job-matching feed server with configurable source filters and a curated dashboard for quick triage.

JobHunter serves a filtered, configurable view of remote job feeds through a FastAPI backend. It is designed for local deployment and constrained-host operation, with production-hardened observability and security patterns.

Built by Conrad CJ Wilson.

## What It Demonstrates

| Capability | Implementation |
|---|---|
| Feed ingestion | Configurable remote job feed parsing with source filters |
| Keyword and location filtering | Exclusion rules, inclusion rules, and location-based filtering via `job_config.yaml` |
| Curated dashboard | Local dashboard generator for quick job triage |
| CORS-enabled API | Frontend consumption with explicit CORS configuration |
| Observability | `/metrics` endpoint, structured logging, correlation IDs |
| Security hardening | OAuth2 refresh-token rotation, rate limiting, fail-closed secret handling |
| Infrastructure as code | Docker Compose, Kubernetes manifests with probes and HPA |
| Monitoring | Prometheus + Grafana scrape configuration and dashboard |

## Stack

| Layer | Tooling |
|---|---|
| Language | Python 3.11 |
| API | FastAPI + uvicorn |
| Fetching | httpx, feedparser |
| Config | PyYAML |
| Observability | Prometheus `/metrics`, structured JSON logs, correlation IDs |
| Infrastructure | Docker Compose, Kubernetes (probes, HPA, non-root) |
| Monitoring | Prometheus + Grafana |
| Testing | pytest with load and contract fixtures |

## Architecture

```
Job Feed Sources (RSS, APIs)
    │
    ▼
Feed Fetcher (httpx + feedparser)
    │
    ▼
Filter Pipeline
    ├── Source filters
    ├── Keyword inclusion / exclusion
    └── Location filters
    │
    ▼
FastAPI Server
    ├── /jobs — filtered feed endpoints
    ├── /metrics — Prometheus metrics
    ├── /health — service health
    └── CORS-enabled for frontend
    │
    ▼
Curated Dashboard (local script)
```

## Quick Start

```bash
git clone https://github.com/cjps4linux-creator/jobhunter.git
cd jobhunter

python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate   # Linux/macOS

pip install -r backend/requirements.txt
uvicorn server:app --reload

curl http://localhost:8000/health
```

## Configuration

Edit `job_config.yaml` to configure:

| Setting | Purpose |
|---|---|
| `sources` | Feed URLs or API endpoints to monitor |
| `keywords.include` | Terms that must appear in the job title or description |
| `keywords.exclude` | Terms that filter out matching jobs |
| `locations` | Geographic filters (city, country, remote) |
| `refresh_interval` | How often feeds are polled |

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/metrics` | Prometheus metrics (feed counts, filter rates, latency) |
| GET | `/jobs` | Filtered job listings |
| GET | `/jobs/sources` | Available feed sources and their status |

## Repository Layout

| Path | Purpose |
|---|---|
| `server.py` | FastAPI app and feed endpoints |
| `job_config.yaml` | Source, keyword, and location filters |
| `curated_jobs_dashboard.py` | Local dashboard generator |
| `backend/` | API implementation and configuration |
| `tests/` | Load and contract test fixtures |
| `security/` | Audit report and hardening notes |
| `k8s/` | Kubernetes manifests (probes, HPA, non-root) |
| `monitoring/` | Prometheus/Grafana scrape and dashboard config |
| `observability/` | Metrics and logging wiring |

## Architecture Decision Records

### ADR-001: FastAPI Over Flask

FastAPI was selected for its async support, automatic OpenAPI documentation, and built-in Pydantic validation. The async capability is important for the I/O-bound feed fetching pattern, and the automatic API documentation reduces maintenance overhead.

### ADR-002: PyYAML for Configuration

Job filters are defined in YAML rather than hardcoded. This allows non-developers to adjust sources, keywords, and locations without modifying Python code, and supports version-controlled configuration changes.

### ADR-003: Kubernetes Manifests Over Helm Charts

Raw Kubernetes manifests were chosen over Helm charts to keep the deployment transparent and auditable. The manifests include readiness and liveness probes, HPA for autoscaling, and non-root security contexts.

## Honest Limitations

- Feed freshness depends on the polling interval configured in `job_config.yaml`. Real-time job boards typically require webhook or streaming APIs, which are not implemented in this version.
- The curated dashboard is a local script, not a hosted web interface. A production deployment would replace this with a proper frontend or integrate with an existing dashboard framework.
- Persistence layer is not implemented; job state is held in memory. A production system would add PostgreSQL or Redis for feed state persistence and deduplication.
- No authentication on the API endpoints. Deploy behind a reverse proxy or API gateway for production access control.

## Current State

Core API, feed filtering, dashboard tooling, observability, and Kubernetes manifests are implemented. Persistence layer and dedicated frontend are planned for a subsequent release.

## License

MIT — use, modify, and ship freely.

**Author:** Conrad CJ Wilson
**GitHub:** https://github.com/cjps4linux-creator
**LinkedIn:** https://www.linkedin.com/in/conradcjwilson
