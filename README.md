# jobhunter

Lightweight job-matching feed server with configurable source filters and dashboard.

## Behavior
- FastAPI server serving filtered remote job feeds
- Configurable sources, keywords, locations, exclusions via `job_config.yaml`
- Curated dashboard script `curated_jobs_dashboard.py`
- CORS-enabled endpoints for frontend consumption

## Stack
- Python 3.11
- FastAPI
- httpx
- feedparser
- PyYAML

## Status
Functional stub

## Notes
- Not production-hardened
- Missing persistent storage and frontend scaffold
- Intended as Hermes job-matching prototype layer

## Author
Conrad CJ Wilson
