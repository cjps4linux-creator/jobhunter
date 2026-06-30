Based on the context I have — JobHunter platform, multi-agent systems, embedded development on PS4, full-stack work — here's a concise proof of work section:

---

# Proof of Work

## **JobHunter Platform** — Full-Stack Job Intelligence System
*Personal project — architect, developer, operations*

Built a job scraping and matching platform running entirely on a PlayStation 4 (3.8GB RAM, zero cloud budget). The system aggregates listings from 8+ global sources (Remotive, WWR, Himalayas, Pnet SA), deduplicates results via fuzzy matching, and serves them through a Next.js frontend with FastAPI backend — all in Docker Compose on CachyOS.

**Skills demonstrated:** Full-stack engineering, distributed scraping, resource-constrained architecture, API design.

## **Hermes Multi-Agent Framework** — Autonomous AI Coordination Layer
*System architect — ongoing*

Designed and maintain a 7-agent autonomous coordination system running on embedded hardware. Implemented FIFO-based inter-agent messaging, a memory governance layer (DuckDB-backed), OOM protection for sub-1GB workloads, and Playwright integration for JavaScript-heavy target sites. All services operate under 3.8GB RAM with deterministic task scheduling.

**Skills demonstrated:** Systems design, inter-process communication, constraint-aware architecture, security hardening.

## **PS4-to-Productivity Pipeline** — Embedded Linux Dev Environment
*DevOps / infrastructure*

Repurposed a PlayStation 4 as a continuous-delivery development node: automated builds targeting Jaguar APU (`-march=btver2`), CI-equivalent pipelines via go-task, vulnerability scanning with Trivy, and real-time monitoring through systemd cgroups. Hardware-targeted compilation for a non-x86 production environment.

**Skills demonstrated:** Embedded Linux, hardware-specific optimization, CI/CD without cloud dependencies, monitoring at the kernel level.

---

Each project reflects a consistent pattern: **solve real problems under real constraints, ship working systems, iterate.**

---