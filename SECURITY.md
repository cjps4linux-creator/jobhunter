# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| master  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security issue in this repository, please open a private security advisory via GitHub or contact `conradcjwilson0@gmail.com` directly.

Please do not open public issues for active vulnerabilities.

## Hardening Requirements

- Do not commit `.env` or files containing secrets.
- Use `SECRET_KEY` from a secrets manager or environment variable in non-development deployments.
- Enable GitHub secret scanning and vulnerability alerts in repository settings.
- Require CI/status checks before merge when the repository is public-facing.
