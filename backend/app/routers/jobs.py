from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import httpx
import feedparser
import hashlib
import re
from datetime import datetime, timezone

router = APIRouter()

# ---- Models ----

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    posted_at: str  # ISO date string
    source: str
    job_type: str  # full-time, contract, etc.
    tags: List[str] = []

# ---- Keyword filter ----

KEYWORDS = [
    "software", "engineer", "developer", "frontend", "backend", "fullstack",
    "full-stack", "full stack", "python", "javascript", "typescript", "react",
    "node", "remote", "devops", "sre", "data", "product", "design", "ui",
    "ux", "mobile", "ios", "android", "swift", "kotlin", "java", "go",
    "golang", "rust", "c++", "csharp", ".net", "ruby", "rails", "php",
    "laravel", "django", "flask", "aws", "cloud", "sql", "nosql", "api",
    "machine learning", "ml", "ai", "artificial intelligence", "blockchain",
    "web3", "crypto", "security", "cybersecurity", "qa", "testing", "scrum",
    "agile", "manager", "lead", "senior", "junior", "intern", "mid",
]

def matches_keywords(job: Job) -> bool:
    """Return True if job title or tags match at least one keyword."""
    text = f"{job.title} {' '.join(job.tags)}".lower()
    return any(keyword in text for keyword in KEYWORDS)

# ---- Normalization helpers ----

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())

def make_id(url: str, source: str) -> str:
    return hashlib.md5(f"{source}:{url}".encode()).hexdigest()

def parse_date(raw) -> Optional[datetime]:
    """Try to parse a date string into a timezone-aware UTC datetime."""
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        except Exception:
            return None
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(str(raw), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None

# ---- Source fetchers ----

async def fetch_remoteok(client: httpx.AsyncClient) -> List[Job]:
    jobs: List[Job] = []
    try:
        resp = await client.get(
            "https://remoteok.com/api",
            headers={"User-Agent": "JobHunter/1.0"},
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("link") or item.get("id")
            if not url:
                continue
            title = item.get("position") or item.get("title") or "Untitled"
            company = item.get("company") or "Unknown"
            location = item.get("location") or "Remote"
            date_raw = item.get("date") or item.get("created_at") or item.get("epoch")
            posted = parse_date(date_raw)
            if posted is None:
                posted = datetime.now(timezone.utc)
            tags = [t.lower() for t in item.get("tags", []) if isinstance(t, str)]
            jobs.append(
                Job(
                    id=make_id(str(url), "remoteok"),
                    title=title,
                    company=company,
                    location=location,
                    url=str(url),
                    posted_at=posted.isoformat(),
                    source="RemoteOK",
                    job_type=item.get("job_type") or "Full-time",
                    tags=tags,
                )
            )
    except Exception:
        # Log in production; silent here to keep MVP simple
        pass
    return jobs



async def fetch_remotive(client: httpx.AsyncClient) -> List[Job]:
    jobs: List[Job] = []
    try:
        resp = await client.get(
            "https://remotive.com/api/remote-jobs",
            headers={"User-Agent": "JobHunter/1.0"},
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobs", []):
            url = item.get("url") or item.get("link")
            if not url:
                continue
            title = item.get("title") or "Untitled"
            company = item.get("company_name") or item.get("company") or "Unknown"
            location = item.get("candidate_required_location") or "Remote"
            date_raw = item.get("publication_date") or item.get("date")
            posted = parse_date(date_raw)
            if posted is None:
                posted = datetime.now(timezone.utc)
            tags = [
                t.lower()
                for t in item.get("tags", [])
                if isinstance(t, str)
            ]
            jobs.append(
                Job(
                    id=make_id(str(url), "remotive"),
                    title=title,
                    company=company,
                    location=location,
                    url=str(url),
                    posted_at=posted.isoformat(),
                    source="Remotive",
                    job_type=item.get("job_type") or "Full-time",
                    tags=tags,
                )
            )
    except Exception:
        pass
    return jobs


async def fetch_wwr(client: httpx.AsyncClient) -> List[Job]:
    jobs: List[Job] = []
    try:
        resp = await client.get(
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            headers={"User-Agent": "JobHunter/1.0"},
            timeout=20.0,
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            url = entry.get("link")
            if not url:
                continue
            title = entry.get("title") or "Untitled"
            # WWR titles often include company at the end
            company = "Unknown"
            location = "Remote"
            if " — " in title:
                parts = title.split(" — ")
                if len(parts) >= 2:
                    company = parts[-1].strip()
                    title = " — ".join(parts[:-1]).strip()
            date_raw = entry.get("published_parsed") or entry.get("published")
            posted = parse_date(date_raw)
            if posted is None:
                posted = datetime.now(timezone.utc)
            jobs.append(
                Job(
                    id=make_id(str(url), "wwr"),
                    title=title,
                    company=company,
                    location=location,
                    url=str(url),
                    posted_at=posted.isoformat(),
                    source="We Work Remotely",
                    job_type="Full-time",
                    tags=[],
                )
            )
    except Exception:
        pass
    return jobs


async def fetch_himalayas(client: httpx.AsyncClient) -> List[Job]:
    jobs: List[Job] = []
    # Try JSON API first, fall back to RSS
    urls_to_try = [
        "https://himalayas.app/jobs/api/jobs",
        "https://himalayas.app/jobs.rss",
    ]
    for url in urls_to_try:
        try:
            resp = await client.get(
                url,
                headers={"User-Agent": "JobHunter/1.0"},
                timeout=20.0,
            )
            resp.raise_for_status()
            if "application/json" in resp.headers.get("content-type", "") or url.endswith(".json"):
                data = resp.json()
                items = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    job_url = item.get("url") or item.get("link") or item.get("slug")
                    if not job_url:
                        continue
                    if not str(job_url).startswith("http"):
                        job_url = f"https://himalayas.app{job_url}"
                    title = item.get("title") or "Untitled"
                    company = item.get("company_name") or item.get("company") or "Himalayas"
                    location = item.get("location") or "Remote"
                    date_raw = item.get("published_at") or item.get("date") or item.get("created_at")
                    posted = parse_date(date_raw)
                    if posted is None:
                        posted = datetime.now(timezone.utc)
                    tags = [
                        t.lower()
                        for t in item.get("tags", [])
                        if isinstance(t, str)
                    ]
                    jobs.append(
                        Job(
                            id=make_id(str(job_url), "himalayas"),
                            title=title,
                            company=company,
                            location=location,
                            url=str(job_url),
                            posted_at=posted.isoformat(),
                            source="Himalayas",
                            job_type=item.get("job_type") or "Full-time",
                            tags=tags,
                        )
                    )
            else:
                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    url = entry.get("link")
                    if not url:
                        continue
                    title = entry.get("title") or "Untitled"
                    company = "Himalayas"
                    date_raw = entry.get("published_parsed") or entry.get("published")
                    posted = parse_date(date_raw)
                    if posted is None:
                        posted = datetime.now(timezone.utc)
                    jobs.append(
                        Job(
                            id=make_id(str(url), "himalayas"),
                            title=title,
                            company=company,
                            location="Remote",
                            url=str(url),
                            posted_at=posted.isoformat(),
                            source="Himalayas",
                            job_type="Full-time",
                            tags=[],
                        )
                    )
            # If we got here successfully, break
            break
        except Exception:
            continue
    return jobs

# ---- Main endpoint ----

@router.get("/jobs/today", response_model=List[Job])
async def get_jobs_today():
    async with httpx.AsyncClient() as client:
        remoteok_jobs, remotive_jobs, wwr_jobs, himalayas_jobs = await asyncio.gather(
            fetch_remoteok(client),
            fetch_remotive(client),
            fetch_wwr(client),
            fetch_himalayas(client),
        )
    all_jobs = remoteok_jobs + remotive_jobs + wwr_jobs + himalayas_jobs

    # Filter by keywords
    filtered = [job for job in all_jobs if matches_keywords(job)]

    # Deduplicate by normalized title + company + source
    seen = set()
    deduped: List[Job] = []
    for job in filtered:
        key = (normalize(job.title), normalize(job.company), job.source)
        if key not in seen:
            seen.add(key)
            deduped.append(job)

    # Sort by posted_at descending
    deduped.sort(key=lambda j: j.posted_at, reverse=True)
    return deduped
