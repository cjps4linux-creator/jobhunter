# JobHunter

Lightweight job-matching feed server with configurable source filters and dashboard.

JobHunter is the Hermes job-matching prototype layer. It serves a filtered, configurable view of remote job feeds through a FastAPI backend, with a curated dashboard for quick triage. Designed for local deployment and constrained-host operation.

## Capabilities

- FastAPI server serving filtered remote job feeds
- Configurable sources, keywords, locations, and exclusions via `job_config.yaml`
- Curated dashboard script: `curated_jobs_dashboard.py`
- CORS-enabled endpoints for frontend consumption

## Stack

| Layer | Tooling |
|-------|----------|
| Language | Python 3.11 |
| API | FastAPI |
| Fetching | httpx, feedparser |
| Config | PyYAML |
| Observability | `/metrics`, structured logging, correlation IDs |
| Infra | Docker Compose, Kubernetes manifests under `k8s/` |

## Quick Start

```bash
pip install -r backend/requirements.txt
uvicorn server:app --reload
curl http://localhost:8000/health
```

## Repository Layout

| Path | Purpose |
|------|---------|
| `server.py` | FastAPI app and feed endpoints |
| `job_config.yaml` | Source/keyword/location filters |
| `curated_jobs_dashboard.py` | Local dashboard generator |
| `backend/` | API implementation and config |
| `tests/` | Load and contract fixtures |
| `security/` | Audit report and hardening notes |
| `k8s/` | Kubernetes manifests (probes, HPA, non-root) |
| `monitoring/` | Prometheus/Grafana scrape + dashboard config |
| `observability/` | Metrics and logging wiring |

## Current State

Core API and dashboard tooling are implemented. Persistence layer and dedicated frontend scaffold are planned for a subsequent release.

## Notes

- Intended as the Hermes job-matching prototype layer
- Designed for local deployment and constrained-host operation
- OAuth2 refresh-token rotation and `/metrics` are wired for production hardening

## Security

See `SECURITY.md`. Secret handling is fail-closed in non-development environments. Report issues privately to `conradcjwilson0@gmail.com`.

## License

MIT — use, modify, and ship freely.
**Author:** Conrad CJ Wilson
**GitHub:** https://github.com/cjps4linux-creator
**LinkedIn:** https://www.linkedin.com/in/conradcjwilson
