## Module B5: Production Observability, Hardening & CI Image Pipeline

### Work completed
- Added Prometheus-compatible metrics instrumentation with `MetricsMiddleware` and `/metrics`.
- Added local Prometheus + Grafana stack under `observability/`.
- Produced Grafana dashboard JSON and alert rule definitions.
- Added Python load baseline script and generated latency report.
- Added Kubernetes readiness/probes, service account, non-root security context, and secrets pattern.
- Added GitHub Actions image pipeline for GitHub Container Registry with optional SBOM/vuln summary.

### Artifacts
- `backend/app/metrics.py`
- `observability/docker-compose.yml`
- `observability/prometheus/prometheus.yml`
- `observability/prometheus/alerts/*.yml`
- `observability/grafana/provisioning/**`
- `artifacts/b5/grafana-dashboard.json`
- `artifacts/b5/alert-rules.yml`
- `artifacts/b5/baseline-latency-report.json`
- `k8s/sealed-secret-template.yaml`
- `k8s/deployment-events.yaml`
- `.github/workflows/image.yml`
- `tests/load/baseline_latency.py`
- `tests/test_metrics.py`

baseline-latency-report:
```json
{
  "requests": 50,
  "errors": 0,
  "min_ms": 2.417,
  "p50_ms": 4.293,
  "p95_ms": 32.879,
  "max_ms": 36.531,
  "service_url": "http://127.0.0.1:8000"
}
```

observability:
```text
http://localhost:9090
http://localhost:3000
# Use environment variables or a secrets manager for Grafana admin credentials.
# Do not commit default passwords or real credentials to the repository.
```

security:
- Kubernetes service account scoped to deployment namespace.
- Deployment enforces `runAsNonRoot: true`, `readOnlyRootFilesystem: true`.
- `seccompProfile.RuntimeDefault` applied to pod.
- Secrets example included for `SECRET_KEY`/`JWT_ALGORITHM`.
