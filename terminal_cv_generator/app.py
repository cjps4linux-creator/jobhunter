#!/usr/bin/env python3
"""
Terminal CV Generator — v3
Generates personalised job application documents (CV, cover letter,
motivational letter, proof of work) using Hermes agents.

Usage:
    python3 app.py [job_description_or_url]
"""

import os
import sys
import threading
from datetime import datetime

sys.path.insert(0, "/home/qba/.hermes/hermes-agent")

from run_agent import AIAgent
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ─── Configuration ────────────────────────────────────────────────────────────
WORKSPACE_PATH = "/home/qba/jobhunter/workspaces"
MODEL = "openrouter/owl-alpha"
PROVIDER = "openrouter"

# ─── CJ's Profile (embedded so the agent knows exactly who it's writing for) ──
CJ_PROFILE = """
CJ Wilson (Conrad Wilson) — Full-Stack & AI Engineer
Location: Durban, South Africa (SAST, GMT+2)
Email: cjtw0703@protonmail.com | Phone: 071 334 9568

PROFESSIONAL PROFILE:
Self-taught full-stack developer and AI engineer. Built JobHunter — a job search
aggregation platform that scraped 41 sources and matched 300+ jobs/day, running
entirely on constrained hardware (PS4, 3.8GB RAM). 8 years in technical sales (Makro,
Ittas) — strong communicator, understands business needs, delivers working code.

TECHNICAL SKILLS:
- Languages: Python (FastAPI), JavaScript/TypeScript (Next.js, React, Node.js)
- AI/ML: Agent design, prompt engineering, RAG, fine-tuning, inference optimization
- Databases: PostgreSQL, Redis, DuckDB
- DevOps: Docker Compose, Linux (CachyOS), systemd, nginx
- Tools: Git, uv, Celery, Playwright, BeautifulSoup, httpx

EXPERIENCE HIGHLIGHTS:
1. JobHunter Platform — Built end-to-end job search platform (Python/FastAPI + Next.js + PostgreSQL + Redis + Celery). 41 scrapers, 300+ jobs/day, 3-layer relevance filtering.
2. 43+ Production Web Scrapers — Deployed for e-commerce, job boards, real estate, competitive intelligence.
3. Technical Sales (Makro 2015–2023) — 8 years in B2B technical sales, consistently exceeded targets.
4. Ittas.co.za (Oct–Dec 2023) — Bitrix24 CRM implementation and lead generation.

EDUCATION:
- Diploma in Information Technology — Oval International Computer Education
- Microsoft Certifications: M365, Surface, Windows (2021–2023)
"""

# ─── Detailed Project Reference (for Proof of Work) ─────────────────────────
PROJECT_REFERENCE = """
# CJ Wilson — Detailed Project Reference

## 1. JobHunter Platform

**What it was:** A full-stack job search aggregation platform that scraped 41 job boards, matched listings against user profiles, and delivered personalised job alerts.

**Tech stack:** Python (FastAPI) + Next.js 14 + PostgreSQL + Redis + Celery + Docker Compose, deployed on PS4 (CachyOS, 3.8GB RAM).

**Key achievements:**
- 41 production web scrapers across job boards, e-commerce, real estate
- 300+ jobs/day throughput with 3-layer relevance filtering
- 30,000+ jobs in database, 75+ companies tracked
- Zero cloud infrastructure cost — ran entirely on consumer hardware
- Built matching algorithm, alert system, and full UI

**Why it matters:** Demonstrates ability to build production-grade systems under extreme constraints. Proves resourcefulness, systems thinking, and delivery capability.

---

## 2. 43+ Production Web Scrapers

**What they were:** Custom scrapers for e-commerce price monitoring, job board aggregation, real estate listings, and competitive intelligence across multiple industries.

**Tech stack:** Python, Scrapy, Playwright, BeautifulSoup, httpx, PostgreSQL.

**Key achievements:**
- Handled anti-bot bypass (rotating proxies, rate limiting, JS rendering)
- Concurrent data extraction pipelines with automated parsing
- Data cleaning, validation, and structured storage to PostgreSQL
- Monitored and maintained scraper fleet with error handling and retry logic

**Why it matters:** Shows deep understanding of web scraping at scale, data pipeline engineering, and production system maintenance.

---

## 3. Multi-Agent Orchestration System

**What it was:** A team of 7 AI agents (Athena, Bob, Clio, Narrator, Scout, Ledger, Sentinel) coordinating autonomous tasks — from job scraping to document generation to financial tracking.

**Tech stack:** Python, Hermes Agent framework, systemd, Docker, Telegram API.

**Key achievements:**
- Designed agent communication protocol with shared memory and task queues
- Implemented memory governor to prevent OOM on 3.8GB RAM
- Built cron-based scheduling for daily/weekly workflows
- Created cross-agent knowledge sharing (lessons learned propagate to all agents)

**Why it matters:** Demonstrates systems architecture, AI orchestration, and the ability to build intelligent multi-agent workflows.

---

## 4. Technical Sales — Makro (2015–2023)

**Role:** B2B Technical Sales Consultant

**Key achievements:**
- Consistently exceeded sales targets across 8-year tenure
- Advised enterprise clients on technology solutions
- Translated complex technical concepts into actionable business value
- Built strong client relationships through clear communication and reliable support

**Why it matters:** Proves business acumen, stakeholder communication, and ability to bridge technical and commercial domains.

---

## 5. CRM Implementation — Ittas.co.za (Oct–Dec 2023)

**What it was:** Ground-up Bitrix24 CRM implementation for a lead generation business.

**Key achievements:**
- Configured workflows, pipelines, and automation rules
- Integrated CRM with marketing channels
- Developed lead generation strategies to improve conversion rates

**Why it matters:** Shows ability to quickly learn new tools, implement systems, and drive measurable business outcomes.
"""

# ─── Document Prompts (each emphasises DIFFERENT aspects to avoid redundancy) ─
DOC_TYPES = [
    (
        "cv",
        "ATS-Optimised CV",
        """You are a professional CV writer. Using the candidate profile and job description below, create a concise, ATS-friendly CV in Markdown.

FORMAT (strict — follow this exactly):
# Curriculum Vitae — CJ Wilson
---
## Professional Summary
[3-4 sentences: who they are, what they bring, relevant to the job. Mention the PS4/JobHunter story ONCE here as proof of resourcefulness.]
## Technical Skills
[Bullet points, grouped by category: Languages, AI/ML, Web, DevOps, Tools]
## Professional Experience
[Reverse chronological. For each role: Title | Company | Dates, then 3-4 bullet points of achievements]
## Education & Certifications
[Education, then certifications]
## Key Projects
[1-2 paragraphs on most relevant projects — mention JobHunter briefly. Do NOT repeat the full PS4 story here (it's in Summary).]

TARGET LENGTH: ~400-500 words total. Be concise. Use action verbs. Tailor every section to match keywords from the job description.
IMPORTANT: Do NOT mention PlayStation 4 or PS4 more than once (only in Professional Summary). Focus on skills, outcomes, and relevance to the job.

CJ's profile:
{profile}

Job Description:
{job}

Write the complete CV in Markdown. Do not use any tools.""",
    ),
    (
        "cover_letter",
        "Cover Letter",
        """You are a professional cover letter writer. Using the candidate profile and job description below, create a compelling cover letter in Markdown.

FORMAT (strict):
# Cover Letter — Application for [Role Name at Company]
---
[Salutation: Dear Hiring Team / Dear [Name] if known]

## Opening
[1 paragraph: Express interest, mention the specific role, 1 sentence on why CJ is a strong fit. Focus on PROBLEM-SOLVING and DELIVERY, not the PS4 story.]

## Why I Can Deliver
[1 paragraph: Reference 2-3 SPECIFIC requirements from the job description and map them to CJ's actual experience. Use concrete examples. Emphasise technical depth and results.]

## Why I Want This
[1 paragraph: Show cultural fit and genuine interest. Mention something specific about the company/mission. Focus on what CJ wants to BUILD at this company.]

## Closing
[1 short paragraph: Availability, enthusiasm, call to action. Include CJ's contact details.]

TARGET LENGTH: ~200-250 words. Be specific — never generic. Mirror language from the job description.
IMPORTANT: Do NOT mention PlayStation 4 or PS4 at all. Focus on skills, experience, and what CJ can do for THIS company.

CJ's profile:
{profile}

Job Description:
{job}

Write the complete cover letter in Markdown. Do not use any tools.""",
    ),
    (
        "motivational_letter",
        "Motivational Letter",
        """You are a professional motivational letter writer. Using the candidate profile and job description below, create a motivational letter in Markdown.

FORMAT (strict):
# Motivational Letter — [Company Name]
---
## Why I'm Applying
[1 paragraph: What draws CJ to this role specifically — avoid clichés. Focus on the WORK and the IMPACT, not the PS4 origin story.]

## What I Bring
[1 paragraph: CJ's unique strengths, told through the lens of this role. Emphasise adaptability, self-directed learning, and delivery. Reference the multi-agent system or sales experience — NOT the PS4.]

## How I'll Contribute
[1 paragraph: Concrete things CJ could do in the first 30/60/90 days. Show proactive thinking.]

TARGET LENGTH: ~150-200 words. Be enthusiastic but grounded in facts.
IMPORTANT: Do NOT mention PlayStation 4 or PS4 at all. Focus on professional strengths, growth mindset, and what CJ will deliver.

CJ's profile:
{profile}

Job Description:
{job}

Write the complete motivational letter in Markdown. Do not use any tools.""",
    ),
    (
        "proof_of_work",
        "Proof of Work & Project Reference",
        """You are a technical writer. Create a detailed Proof of Work document that showcases CJ's projects with depth and evidence.

FORMAT (strict):
# Proof of Work — CJ Wilson
---

[For each of the 4 projects below, write a detailed section using this structure:]

## [Project Name]
**What it was:** [2-3 sentences describing the project and its purpose]
**Tech stack:** [List of technologies used]
**Key achievements:**
- [Bullet point with specific numbers/metrics]
- [Bullet point on technical challenge overcome]
- [Bullet point on business impact or user outcome]
**Why it matters:** [1 sentence on what this proves about CJ's capability]

---

## Contact
📧 cjtw0703@protonmail.com | 📱 071 334 9568 | 📍 Durban, South Africa (SAST, GMT+2)

RULES:
- Use ALL 4 projects provided below
- Include specific numbers (41 scrapers, 300+ jobs/day, 8 years, etc.)
- Explain technical challenges and how CJ solved them
- Each project section should be 6-10 lines (detailed but not bloated)
- Tailor emphasis to match the job description (highlight relevant projects first)
- This is a STANDALONE document — it can be attached separately for verification

CJ's detailed project reference:
{projects}

Job Description (for tailoring emphasis):
{job}

Write the complete Proof of Work in Markdown. Do not use any tools.""",
    ),
]


# ─── UI Helpers ──────────────────────────────────────────────────────────────

def render_header():
    title = Text()
    title.append("╔══════════════════════════════════════════╗\n", style="bold cyan")
    title.append("║    🖥️  Terminal CV Generator v3           ║\n", style="bold white")
    title.append("║    Personalised docs for CJ Wilson       ║\n", style="dim")
    title.append("╚══════════════════════════════════════════╝", style="bold cyan")
    console.print(Panel(title, border_style="cyan"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("label", style="bold yellow", width=16)
    table.add_column("value", style="white")
    table.add_row("Model:", f"{MODEL} ({PROVIDER})")
    table.add_row("Output:", WORKSPACE_PATH)
    table.add_row("Date:", datetime.now().strftime("%Y-%m-%d %H:%M"))
    console.print(table)
    console.print()


def render_doc_plan():
    table = Table(title="[bold white]📋 Generation Plan[/bold white]", border_style="blue")
    table.add_column("#", style="bold cyan", width=4, justify="center")
    table.add_column("Document", style="bold white", width=24)
    table.add_column("Focus", style="dim", width=40)
    table.add_column("Status", style="yellow", width=10, justify="center")

    focuses = [
        "Skills, experience, ATS keywords",
        "Problem-solving & cultural fit",
        "Growth mindset & contribution",
        "Detailed project deep-dives",
    ]
    for i, (key, label, _) in enumerate(DOC_TYPES):
        table.add_row(str(i + 1), label, focuses[i], "⏳ Pending")

    console.print(table)
    console.print()


def render_summary(files):
    console.print()
    table = Table(title="[bold green]✅ Generation Complete[/bold green]", border_style="green")
    table.add_column("#", style="bold cyan", width=4, justify="center")
    table.add_column("Document", style="bold white", width=24)
    table.add_column("File", style="dim", width=30)
    table.add_column("Status", style="green", width=10, justify="center")

    for i, (key, label, _) in enumerate(DOC_TYPES):
        filepath = files.get(key)
        if filepath:
            filename = os.path.basename(filepath)
            table.add_row(str(i + 1), label, filename, "✅ Done")
        else:
            table.add_row(str(i + 1), label, "—", "❌ Failed")

    console.print(table)

    all_paths = [v for v in files.values() if v]
    if all_paths:
        folder = os.path.dirname(all_paths[0])
        console.print(f"\n[bold cyan]📂 Files saved to:[/bold cyan] {folder}")
        console.print(f"[dim]   Open any .md file to view your tailored document.[/dim]")


# ─── Core Generation (with real progress bar) ────────────────────────────────

def make_agent():
    return AIAgent(
        model=MODEL,
        provider=PROVIDER,
        load_soul_identity=True,
        enabled_toolsets=[],
        quiet_mode=True,
    )


def generate_one(key, label, template, job_description, job_folder):
    """Generate a single document into the shared job_folder with real progress."""
    if key == "proof_of_work":
        prompt = template.format(projects=PROJECT_REFERENCE, job=job_description)
    else:
        prompt = template.format(profile=CJ_PROFILE, job=job_description)

    agent = make_agent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Generating {label}...", total=100)

        # Run API call in a thread so we can advance the bar while waiting
        result = {"value": None, "done": False}

        def call_agent():
            try:
                result["value"] = agent.chat(prompt)
            except Exception as e:
                result["value"] = f"ERROR: {e}"
            result["done"] = True

        thread = threading.Thread(target=call_agent)
        thread.start()

        # Advance progress bar while the API call runs in background
        while not result["done"]:
            progress.update(task, advance=1)
            # Rich Progress handles timing internally; we just tick
            import time
            time.sleep(0.08)

        # Ensure bar shows 100% when done
        remaining = 100 - progress.tasks[0].completed
        if remaining > 0:
            progress.update(task, advance=remaining)
            import time
            time.sleep(0.1)

        thread.join(timeout=5)

        # Check result
        if result["value"] and not result["value"].startswith("ERROR:"):
            text = result["value"].strip()
        else:
            error_msg = result["value"] if result["value"] else "Empty response"
            progress.update(task, description=f"❌ {label} failed: {str(error_msg)[:50]}")
            return None

        if not text:
            progress.update(task, description=f"❌ {label} — empty output")
            return None

        # Clean code fences
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()

        # Write file
        filepath = os.path.join(job_folder, f"{key}.md")
        with open(filepath, "w") as f:
            f.write(text)

        progress.update(task, description=f"✅ {label} generated!")
        return filepath


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        job_description = " ".join(sys.argv[1:])
    else:
        render_header()
        console.print("\n[bold yellow]📌 Enter the job description or paste a job URL:[/bold yellow]")
        console.print("[dim]   (Leave blank for default: 'AI Engineer, remote')[/dim]\n")
        try:
            job_description = input("> ").strip()
        except EOFError:
            job_description = "AI Engineer, remote"
        if not job_description:
            job_description = "AI Engineer, remote"

    render_header()
    console.print(f"\n[bold cyan]🎯 Target:[/bold cyan] {job_description[:80]}{'...' if len(job_description) > 80 else ''}\n")
    render_doc_plan()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_folder = os.path.join(WORKSPACE_PATH, timestamp)
    os.makedirs(job_folder, exist_ok=True)

    # Copy detailed project reference into the job folder for attachment
    import shutil
    ref_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workspaces", "PROJECT_REFERENCE.md")
    ref_dst = os.path.join(job_folder, "project_reference.md")
    if os.path.exists(ref_src):
        shutil.copy2(ref_src, ref_dst)

    files = {}
    for key, label, template in DOC_TYPES:
        files[key] = generate_one(key, label, template, job_description, job_folder)
        console.print()

    render_summary(files)

    if sys.stdin.isatty():
        console.print("\n[dim]Press Enter to exit...[/dim]")
        try:
            input()
        except EOFError:
            pass


if __name__ == "__main__":
    main()
