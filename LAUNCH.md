# JobHunter — Launch Documentation

## Launch Readiness Snapshot

| Field | Value |
| --- | --- |
| Repo | `jobhunter` |
| Default branch | `master` |
| License | MIT |
| Commercial baseline | CI, `CONTRIBUTING.md`, `SECURITY.md`, `LAUNCH.md`, `VERIFICATION.md` |
| Purpose | Job-matching feed server and curated dashboard |

## Verified
- `README.md` present.
- No tracked `.env` files.
- `SECURITY.md` present with contact path and hardening notes.
- `.github/workflows/ci.yml` and `image.yml` present.
- `security/audit-report.md` present and references fail-closed secret handling.
- `tests/` present with load and contract fixtures.

## Launch Gates
- [ ] CI workflow green on `master` before release tag
- [ ] Branch protection and required status checks enabled on `master`
- [ ] GitHub secret scanning and vulnerability alerts enabled
- [ ] Dashboard and feed filters reviewed for customer use before distribution

## Release Workflow
1. Validate `server.py` startup and `/health` against a local run.
2. Cherry-pick approved wording and config updates into a release branch.
3. Tag a release with semver and attach runbook artifacts.
4. Rotate or revoke any shared example credentials if included in release assets.

## Support
- Support contact: `conradcjwilson0@gmail.com`
