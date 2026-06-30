# Proof of Work — CJ Wilson

*Full-Stack Engineer & AI Systems Builder — Durban, South Africa*

---

## 1. Multi-Agent AI Orchestration System (Hermes)

**What it was:** A team of 7 autonomous AI agents — Athena (coordinator), Bob (full-stack lead), Clio (analytics), Narrator (documentation), Scout (research), Ledger (financial tracking), and Sentinel (security) — coordinating daily tasks across job sourcing, document generation, market analysis, and system governance without human intervention.

**Tech stack:** Python, Hermes Agent framework (Nous Research), systemd, Docker Compose, Telegram Bot API, PostgreSQL, shared memory architecture, cron-based scheduling.

**Key achievements:**
- Designed inter-agent communication protocol with shared workspace, task queues, and cross-agent knowledge propagation — lessons learned by one agent benefit all others
- Implemented a memory governor enforcing RAM sanity checks to prevent OOM on a 3.8GB RAM PS4 running CachyOS (AMD Jaguar APU)
- Built automated daily workflows: Scout delivers 8-12 curated jobs/week, Narrator pre-drafts cover letter outlines, Clio runs market analysis — all triggered via cron with zero manual oversight
- Created role-based branch governance (e.g., `scout/intel/*`, `bob/design/*`) and decision logging to `shared/docs/decisions/` for full auditability
- Operated entirely on consumer hardware with zero cloud infrastructure cost

**Why it matters:** This project demonstrates production-grade AI orchestration — designing multi-agent workflows that are reliable, resource-conscious, and self-documenting, directly applicable to building LLM agent systems at startup scale.

---

## 2. JobHunter Platform

**What it was:** A full-stack job search aggregation platform that scraped 41 job boards in real-time, matched listings against user profiles using a custom relevance algorithm, and delivered personalised job alerts through a web dashboard.

**Tech stack:** Python (FastAPI) + Next.js 14 + PostgreSQL + Redis + Celery + Docker Compose, deployed on PS4 (CachyOS, 3.8GB RAM, zero cloud budget).

**Key achievements:**
- 41 production web scrapers covering job boards, e-commerce, and real estate — with anti-bot handling (rate limiting, rotating proxies, JS rendering)
- 300+ jobs/day throughput pipeline with 3-layer relevance filtering (keyword match → semantic scoring → user preference weighting)
- 30,000+ jobs stored in PostgreSQL, 75+ companies tracked in the database
- Built complete matching algorithm, alert system, and responsive frontend UI — fully functional end-to-end product
- Ran entirely on consumer hardware (PS4) with zero cloud infrastructure cost, proving ability to deliver under extreme resource constraints

**Why it matters:** Demonstrates full-stack production capability with Python, FastAPI, and React — the exact stack required for this role — plus the resourcefulness to build serious systems on minimal infrastructure.

---

## 3. 43+ Production Web Scrapers

**What they were:** A fleet of custom scrapers built for e-commerce price monitoring, job board aggregation, real estate listings, and competitive intelligence across multiple industries — each with its own parsing, validation, and storage pipeline.

**Tech stack:** Python, Scrapy, Playwright, BeautifulSoup, httpx, PostgreSQL, lynx/w3m for lightweight fetching.

**Key achievements:**
- Handled anti-bot bypass techniques including rotating proxy pools, request throttling, and headless browser rendering (Playwright) for JS-heavy sites
- Built concurrent data extraction pipelines with automated parsing, cleaning, and structured storage to PostgreSQL
- Implemented error handling, retry logic, and health monitoring across the scraper fleet — maintaining uptime on a 24/7 schedule
- Scaled to 43+ active scrapers running concurrently within a 3.8GB RAM environment, using chunked processing (50K row max) to stay within memory limits

**Why it matters:** Shows deep practical expertise in data pipeline engineering at scale — concurrent extraction, resilience patterns, and production maintenance — skills directly transferable to building reliable AI-powered data systems.

---

## 4. Technical Sales — Makro (2015–2023) & CRM Implementation — Ittas (2023)

**What it was:** 8 years of B2B technical sales at Makro (South Africa's largest wholesale retailer), followed by a ground-up Bitrix24 CRM implementation for a lead generation business at Ittas.co.za.

**Tech stack:** Bitrix24, workflow automation, pipeline management, lead tracking systems, CRM-marketing integrations.

**Key achievements:**
- Consistently exceeded sales targets across 8-year tenure at Makro — advising enterprise clients on technology solutions and translating complex technical concepts into actionable business value
- At Ittas (Oct–Dec 2023): configured Bitrix24 workflows, pipelines, and automation rules from scratch; integrated CRM with marketing channels; developed lead generation strategies to improve conversion rates
- Bridged the gap between technical teams and business stakeholders — a skill critical for an AI engineer who must translate product requirements into working LLM agent systems

**Why it matters:** Proves business acumen, stakeholder communication, and the ability to bridge technical execution with commercial outcomes — rare combination for an engineer, and valuable in a startup environment where understanding the "why" behind the build matters as much as the "how."

---

## Contact

📧 cjtw0703@protonmail.com | 📱 071 334 9568 | 📍 Durban, South Africa (SAST, GMT+2)

---

*Document prepared for verification of work history and technical capability. All projects are demonstrable and available for technical discussion.*