# Security Audit — JobHunter + Local Workstation

Date: 2026-07-15
Auditor: ATHENA X / Conrad CJ Wilson
Scope: local Windows 11 Pro host, jobhunter repository, GitHub account posture
Severity: LOW / MEDIUM / HIGH

---

## Executive Summary

- No active compromise indicators found.
- Repo-local secrets hygiene is mostly healthy.
- One code-path finding was fixed in this audit: hardcoded `dev-secret-key` default in `app/config.py`.
- Three GitHub-level controls are best-practice missing and require manual enablement.

---

## 1. Local System

### Verified
- Windows Defender: real-time protection enabled, signatures current
- Firewall: enabled for Domain/Private/Public
- Windows Update: last successful install/search on 2026-07-15
- Active local user accounts: `user` only, plus disabled built-in accounts
- Listening local services include expected localhost ports:
  - 127.0.0.1:8000 FastAPI
  - 127.0.0.1:9090 Prometheus
  - 127.0.0.1:3000 Grafana
  - 127.0.0.1:12434 Docker/GUI
  - plus standard Windows services

### Finding
- Severity: LOW
- Observation: Docker Desktop/WSL2 backend was unavailable until BIOS virtualization was enabled; this is expected remediation, not a finding.

---

## 2. Repo-Local Secrets Hygiene

### Verified
- No tracked `.env` files in git
- `.gitignore` covers `.env` and `.env.*`
- Workflow uses GitHub Actions `secrets.GITHUB_TOKEN` ref, not a literal token
- No raw long-lived tokens detected in repo text: no `ghp_*`, `github_pat_*`, `AKIA*`, `sk_live_*`, `sk_test_*`, or PEM blocks

### Fixed in this audit
- Severity: MEDIUM
- File: `backend/app/config.py`
- Finding: `secret_key: str = "dev-secret-key"`
- Fix: changed to fail-closed in non-development environments; development fallback emits an explicit security warning
- Verification: `python -m pytest` focused suite passes

### Finding
- Severity: LOW
- File: `artifacts/b5/summary.md`
- Finding: previously contained placeholder Grafana credentials in plain text
- Fix: replaced with secrets-management guidance
- Verification: `git diff` confirms replacement

---

## 3. GitHub Posture

### Verified
- Account: `cjps4linux-creator`
- Token scopes: `gist`, `read:org`, `repo`, `workflow`
- Repositories are private: jobhunter, constrained-ai-stack, hermes-agent-template, hermes-ai-os, hermes-ai-os-public, hermes-0os-public, architect-agent, architect-agent-mobile, nousstream
- Default branch protection object exists; additional hardening can be reviewed per repo

### Requires manual remediation
- Severity: MEDIUM
- Enable secret scanning in GitHub Settings → Code security and analysis
- Enable vulnerability alerts in GitHub Settings → Code security and analysis
- Add `SECURITY.md` to each repository for public vulnerability-reporting contact path
- Consider enabling branch protection rules requiring status checks before merge

---

## 4. Infrastructure Security

### Verified
- Kubernetes manifests include:
  - `runAsNonRoot: true`
  - `readOnlyRootFilesystem: true`
  - `seccompProfile.RuntimeDefault`
- Observability stack runs on localhost-bound ports with Docker network isolation
- Secrets pattern documented in `k8s/sealed-secret-template.yaml`

### Requires improvement
- Severity: LOW
- Add network-policy definitions when exposing externally
- Rotate API keys/tokens on a defined cadence
- Ensure database credentials are injected via sealed secret or external secret store in non-local environments

---

## 5. Windows Defender / Endpoint Findings

### Verified
- Active protection enabled
- Firewall enabled
- Updates current

### Requires improvement
- Last full scan age is very old; run an on-demand full scan
- Standardize local account lockout policy and screen lock behavior

---

## 6. Remediation Evidence

- Code fix committed and pushed: `backend/app/config.py`
- Documentation added: `SECURITY.md`
- Findings documented: `security/audit-report.md`
- Skills documented: `security-audit`

---

## 7. CV Accreditation Language

- Secured repository by removing placeholder credentials from public-facing documentation and enforcing fail-closed secret handling in application configuration.
- Validated endpoint, container, and localhost-scoped service posture with live health checks and port audit.

---

## 8. Local Stale Image Inventory

### Verified
- `docker images` review performed on local Docker Desktop cache.

### Finding
- Severity: LOW
- Image: `tensorflow/tensorflow:latest` (ID: `f325279f01a3`, Created: 2026-03-07)
- Status: **Stale/unreferenced** — not referenced in any active Dockerfile or compose file in the vault
- Risk: Medium-High if executed; low risk while simply present in cache
- Action: Left in cache per user decision. Documented here for traceability.

### Recommendation
- Delete when ready: `docker rmi tensorflow/tensorflow:latest`
- If TensorFlow is needed again, use a pinned slim/cpu-only variant in an explicit project Dockerfile with CI scanning
- Monitor Docker Desktop image cache regularly for unused large ML images
