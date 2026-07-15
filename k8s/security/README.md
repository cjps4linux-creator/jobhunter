# Kubernetes hardening notes

## Secret management
- Production secrets should not be stored as plain Kubernetes Secrets.
- Options to evaluate:
  - Sealed Secrets
  - external-secrets + secret store backend
  - HashiCorp Vault or cloud secret manager

## Pod security
- Prefer restricted policy:
  - `runAsNonRoot: true`
  - `readOnlyRootFilesystem: true`
  - drop `ALL` Linux capabilities
  - writable volumes limited to `/tmp` and application caches only

## Environment separation
- Do not reuse a single secret across environments.
- Rotate `SECRET_KEY` on promotion to production.
- Inject secrets via envFrom or CSI volume rather than inline base64 only.

## Evidence for reviewers
- `k8s/security/secure-pod-template.yaml` is a hardened template for manual review.
- Include `kubectl diff` or policy report output in PR evidence when adopting.
