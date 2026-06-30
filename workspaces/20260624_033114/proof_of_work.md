# Proof of Work

Building production-grade AI and full-stack systems on constrained infrastructure — turning a PlayStation 4 into a development platform and shipping real products on zero cloud budget.

---

## 1. JobHunter — Full-Stack Job Intelligence Platform

Architected and deployed a job scraping and matching platform running on CachyOS (PS4, 3.8GB RAM). Multi-source ingestion pipeline pulling from RemoteOK, Remotive, WWR, Himalayas, and Playwright-powered scrapers for JS-heavy sites (SA, Indeed, talent.com). Stack: **Next.js 14 + FastAPI + PostgreSQL + Redis + Celery**, orchestrated via Docker Compose. Built a stateless, RSS/JSON-feed dashboard (Google Jobs-style mobile UI), no auth layer, three-hour refresh cycle, YAML-configurable keywords/locations.

**Outcome:** 5 global sources stable, South African sources returning real listings, end-to-end pipeline from scrape to dashboard on commodity hardware.

---

## 2. Hermes Multi-Agent System — Autonomous Development Team

Designed and coordinate a 6-agent AI system (Bob, Clio, Narrator, Scout, Ledger, Sentinel) with specialized roles in architecture, analytics, documentation, research, finance, and security. All agents report through a single coordination layer. Managed task routing, resource governance on 3.8GB RAM, and knowledge persistence across sessions.

**Outcome:** Multi-agent workflows executing in parallel — architectural planning, automated analytics, financial tracking, and documentation generation running on local infrastructure with zero cloud spend.

---

## 3. Terminal CV Generator — Productivity Tooling

Built a Markdown-to-PDF/DOCX CV generator optimized for ATS parsing. Clean semantic structure, machine-readable formatting, single-command output.

**Outcome:** Repeatable, professional-grade application documents generated in seconds.

---

*Tech stack: Python, FastAPI, Next.js, PostgreSQL, Redis, Docker, Linux systems programming, multi-agent orchestration.*