# JobHunter

Lightweight job-matching feed server with configurable source filters and dashboard.

## Capabilities
- FastAPI server serving filtered remote job feeds
- Configurable sources, keywords, locations, and exclusions via `job_config.yaml`
- Curated dashboard script: `curated_jobs_dashboard.py`
- CORS-enabled endpoints for frontend consumption

## Stack
- Python 3.11
- FastAPI
- httpx
- feedparser
- PyYAML

## Current State
Core API and dashboard tooling are implemented. Persistence layer and dedicated frontend scaffold are planned for a subsequent release.

## Notes
- Intended as the Hermes job-matching prototype layer
- Designed for local deployment and constrained-host operation

## Author
Conrad CJ Wilson
