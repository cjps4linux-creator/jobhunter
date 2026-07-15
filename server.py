#!/usr/bin/env python3
# Lightweight standalone job dashboard server
# Runs: uvicorn server:app --host 0.0.0.0 --port 3000

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import feedparser
import hashlib
import re
import yaml
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

app = FastAPI(title="JobHunter Daily Feed")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config paths
CONFIG_PATH = Path(__file__).parent / "job_config.yaml"
FRONTEND_PATH = Path(__file__).parent / "index.html"

# --- Config loader ---

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

config = load_config()

KEYWORDS = [k.lower() for k in config.get("keywords", [])]
EXCLUDE = [k.lower() for k in config.get("exclude", [])]
LOCATIONS = [k.lower() for k in config.get("locations", [])]
EXCLUDE_SOURCES = [k.lower() for k in config.get("exclude_sources", [])]
INCLUDE_SOURCES = [k.lower() for k in config.get("include_sources", [])]
AUTO_REFRESH_HOURS = int(config.get("auto_refresh_client_hours", 3))
REFRESH_MS = AUTO_REFRESH_HOURS * 60 * 60 * 1000

def matches_keywords(job):
    text = f"{job.get('title','')} {' '.join(job.get('tags',[]))}".lower()
    if any(k in text for k in EXCLUDE):
        return False
    return any(k in text for k in KEYWORDS) if KEYWORDS else True

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())

def make_id(url: str, source: str) -> str:
    return hashlib.md5(f"{source}:{url}".encode()).hexdigest()

def parse_date(raw):
    if isinstance(raw, datetime):
        return raw.replace(tzinfo=timezone.utc) if raw.tzinfo is None else raw.astimezone(timezone.utc)
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
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None

# --- Fetchers ---

async def fetch_remoteok(client: httpx.AsyncClient):
    jobs = []
    try:
        r = await client.get("https://remoteok.com/api", headers={"User-Agent": "JobHunter/1.0"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        for item in data:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("link") or item.get("id")
            if not url:
                continue
            job = {
                "id": make_id(str(url), "remoteok"),
                "title": item.get("position") or item.get("title") or "Untitled",
                "company": item.get("company") or "Unknown",
                "location": item.get("location") or "Remote",
                "url": str(url),
                "posted_at": (parse_date(item.get("date") or item.get("created_at") or item.get("epoch")) or datetime.now(timezone.utc)).isoformat(),
                "source": "RemoteOK",
                "job_type": item.get("job_type") or "Full-time",
                "tags": [t.lower() for t in item.get("tags", []) if isinstance(t, str)],
            }
            jobs.append(job)
    except Exception:
        pass
    return jobs


async def fetch_remotive(client: httpx.AsyncClient):
    jobs = []
    try:
        r = await client.get("https://remotive.com/api/remote-jobs", headers={"User-Agent": "JobHunter/1.0"}, timeout=20)
        r.raise_for_status()
        data = r.json()
        for item in data.get("jobs", []):
            url = item.get("url") or item.get("link")
            if not url:
                continue
            job = {
                "id": make_id(str(url), "remotive"),
                "title": item.get("title") or "Untitled",
                "company": item.get("company_name") or item.get("company") or "Unknown",
                "location": item.get("candidate_required_location") or "Remote",
                "url": str(url),
                "posted_at": (parse_date(item.get("publication_date") or item.get("date")) or datetime.now(timezone.utc)).isoformat(),
                "source": "Remotive",
                "job_type": item.get("job_type") or "Full-time",
                "tags": [t.lower() for t in item.get("tags", []) if isinstance(t, str)],
            }
            jobs.append(job)
    except Exception:
        pass
    return jobs


async def fetch_wwr(client: httpx.AsyncClient):
    jobs = []
    try:
        r = await client.get("https://weworkremotely.com/categories/remote-programming-jobs.rss", headers={"User-Agent": "JobHunter/1.0"}, timeout=20)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
        for entry in feed.entries:
            url = entry.get("link")
            if not url:
                continue
            title = entry.get("title") or "Untitled"
            company = "Unknown"
            if " — " in title:
                parts = title.split(" — ")
                if len(parts) >= 2:
                    company = parts[-1].strip()
                    title = " — ".join(parts[:-1]).strip()
            job = {
                "id": make_id(str(url), "wwr"),
                "title": title,
                "company": company,
                "location": "Remote",
                "url": str(url),
                "posted_at": (parse_date(entry.get("published_parsed") or entry.get("published")) or datetime.now(timezone.utc)).isoformat(),
                "source": "We Work Remotely",
                "job_type": "Full-time",
                "tags": [],
            }
            jobs.append(job)
    except Exception:
        pass
    return jobs


async def fetch_himalayas(client: httpx.AsyncClient):
    jobs = []
    urls_to_try = [
        "https://himalayas.app/jobs/api/jobs",
        "https://himalayas.app/jobs.rss",
    ]
    for url in urls_to_try:
        try:
            r = await client.get(url, headers={"User-Agent": "JobHunter/1.0"}, timeout=20)
            r.raise_for_status()
            ct = r.headers.get("content-type", "")
            if "application/json" in ct or url.endswith(".json"):
                data = r.json()
                items = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    job_url = item.get("url") or item.get("link") or item.get("slug")
                    if not job_url:
                        continue
                    if not str(job_url).startswith("http"):
                        job_url = f"https://himalayas.app{job_url}"
                    job = {
                        "id": make_id(str(job_url), "himalayas"),
                        "title": item.get("title") or "Untitled",
                        "company": item.get("company_name") or item.get("company") or "Himalayas",
                        "location": item.get("location") or "Remote",
                        "url": str(job_url),
                        "posted_at": (parse_date(item.get("published_at") or item.get("date") or item.get("created_at")) or datetime.now(timezone.utc)).isoformat(),
                        "source": "Himalayas",
                        "job_type": item.get("job_type") or "Full-time",
                        "tags": [t.lower() for t in item.get("tags", []) if isinstance(t, str)],
                    }
                    jobs.append(job)
            else:
                feed = feedparser.parse(r.content)
                for entry in feed.entries:
                    url = entry.get("link")
                    if not url:
                        continue
                    job = {
                        "id": make_id(str(url), "himalayas"),
                        "title": entry.get("title") or "Untitled",
                        "company": "Himalayas",
                        "location": "Remote",
                        "url": str(url),
                        "posted_at": (parse_date(entry.get("published_parsed") or entry.get("published")) or datetime.now(timezone.utc)).isoformat(),
                        "source": "Himalayas",
                        "job_type": "Full-time",
                        "tags": [],
                    }
                    jobs.append(job)
            break
        except Exception:
            continue
    return jobs


# --- Playwright browser pool (SA sources) ---
_playwright = None
_browser = None


async def _get_browser():
    global _playwright, _browser
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
    return _browser


async def _close_browser():
    global _playwright, _browser
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def _scrape_pnet(client: httpx.AsyncClient):
    jobs = []
    page = None
    try:
        browser = await _get_browser()
        page = await browser.new_page()
        query = "+".join(KEYWORDS[:2]) if KEYWORDS else "junior"
        url = f"https://www.pnet.co.za/jobs?keywords={query}&location=South+Africa"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        cards = await page.query_selector_all("[data-testid='job-card'], [class*='job-card'], article")
        for card in cards[:20]:
            try:
                title_el = await card.query_selector("h2, h3, [class*='title']")
                company_el = await card.query_selector("[class*='company'], [class*='employer']")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else "Pnet"
                if not title or len(title) < 5:
                    continue
                link_el = await card.query_selector("a[href*='/job/'], a[href*='job?id']")
                href = await link_el.get_attribute("href") if link_el else url
                if href and not str(href).startswith("http"):
                    href = f"https://www.pnet.co.za{href}"
                jobs.append({
                    "id": make_id(href or url, "pnet"),
                    "title": title[:120],
                    "company": company[:80] or "Pnet",
                    "location": "South Africa",
                    "url": href or url,
                    "posted_at": datetime.now(timezone.utc).isoformat(),
                    "source": "Pnet",
                    "job_type": "Full-time",
                    "tags": [],
                })
            except Exception:
                continue
    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
    return jobs


async def _scrape_simplyhired(client: httpx.AsyncClient):
    jobs = []
    page = None
    try:
        browser = await _get_browser()
        page = await browser.new_page()
        query = "+".join(KEYWORDS[:2]) if KEYWORDS else "junior"
        url = f"https://www.simplyhired.co.za/search?q={query}&l=South+Africa"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        cards = await page.query_selector_all("[data-testid='job-card'], [class*='job-card'], article")
        for card in cards[:20]:
            try:
                title_el = await card.query_selector("h2, h3, [class*='title']")
                company_el = await card.query_selector("[class*='company'], [class*='employer']")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else "Simply Hired"
                if not title or len(title) < 5:
                    continue
                link_el = await card.query_selector("a[href*='job'], a[href*='view']")
                href = await link_el.get_attribute("href") if link_el else url
                if href and not str(href).startswith("http"):
                    href = f"https://www.simplyhired.co.za{href}"
                jobs.append({
                    "id": make_id(href or url, "simplyhired"),
                    "title": title[:120],
                    "company": company[:80] or "Simply Hired",
                    "location": "South Africa",
                    "url": href or url,
                    "posted_at": datetime.now(timezone.utc).isoformat(),
                    "source": "Simply Hired",
                    "job_type": "Full-time",
                    "tags": [],
                })
            except Exception:
                continue
    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
    return jobs


async def _scrape_indeed(client: httpx.AsyncClient):
    jobs = []
    page = None
    try:
        browser = await _get_browser()
        page = await browser.new_page()
        query = "+".join(KEYWORDS[:2]) if KEYWORDS else "junior"
        url = f"https://za.indeed.com/jobs?q={query}&l=South+Africa"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        cards = await page.query_selector_all("[data-jk], [class*='jobsearch-Result'], [class*='jobCard']")
        for card in cards[:20]:
            try:
                title_el = await card.query_selector("h2, h3, [class*='title'] a")
                company_el = await card.query_selector("[class*='company'], [data-company]")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else "Indeed"
                if not title or len(title) < 5:
                    continue
                link_el = await card.query_selector("a[href*='/rc/clk'], a[href*='/viewjob']")
                href = await link_el.get_attribute("href") if link_el else url
                if href and not str(href).startswith("http"):
                    href = f"https://za.indeed.com{href}"
                jobs.append({
                    "id": make_id(href or url, "indeed"),
                    "title": title[:120],
                    "company": company[:80] or "Indeed",
                    "location": "South Africa",
                    "url": href or url,
                    "posted_at": datetime.now(timezone.utc).isoformat(),
                    "source": "Indeed",
                    "job_type": "Full-time",
                    "tags": [],
                })
            except Exception:
                continue
    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
    return jobs


async def _scrape_talent(client: httpx.AsyncClient):
    jobs = []
    page = None
    try:
        browser = await _get_browser()
        page = await browser.new_page()
        query = "+".join(KEYWORDS[:2]) if KEYWORDS else "junior"
        url = f"https://za.talent.com/jobs?q={query}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        # talent.com exposes job URLs in JSON-LD ItemList
        links = await page.eval_on_selector_all(
            'script[type="application/ld+json"]',
            "els => els.map(e => e.textContent).join('\\n')"
        )
        import json
        hrefs = []
        for blob in links:
            try:
                data = json.loads(blob)
                graph = data.get("@graph", []) if isinstance(data, dict) else []
                for item in graph:
                    if isinstance(item, dict) and item.get("@type") == "ItemList":
                        for el in item.get("itemListElement", []):
                            u = el.get("item", {}).get("url")
                            if u:
                                hrefs.append(u)
            except Exception:
                continue
        for href in hrefs[:20]:
            jobs.append({
                "id": make_id(href, "talent"),
                "title": "",
                "company": "talent.com",
                "location": "South Africa",
                "url": href,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "source": "talent.com",
                "job_type": "Full-time",
                "tags": [],
            })
    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
    return jobs


async def _scrape_careers24(client: httpx.AsyncClient):
    jobs = []
    page = None
    try:
        browser = await _get_browser()
        page = await browser.new_page()
        query = "+".join(KEYWORDS[:2]) if KEYWORDS else "junior"
        url = f"https://www.careers24.com/jobs/search?q={query}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        cards = await page.query_selector_all("[class*='job-card'], article, [data-testid='job-card']")
        for card in cards[:20]:
            try:
                title_el = await card.query_selector("h2, h3, [class*='title']")
                company_el = await card.query_selector("[class*='company'], [class*='employer']")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else "Careers24"
                if not title or len(title) < 5:
                    continue
                link_el = await card.query_selector("a[href*='job'], a[href*='view']")
                href = await link_el.get_attribute("href") if link_el else url
                if href and not str(href).startswith("http"):
                    href = f"https://www.careers24.com{href}"
                jobs.append({
                    "id": make_id(href or url, "careers24"),
                    "title": title[:120],
                    "company": company[:80] or "Careers24",
                    "location": "South Africa",
                    "url": href or url,
                    "posted_at": datetime.now(timezone.utc).isoformat(),
                    "source": "Careers24",
                    "job_type": "Full-time",
                    "tags": [],
                })
            except Exception:
                continue
    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
    return jobs


# --- Route ---

@app.get("/api/jobs/today")
async def get_jobs_today():
    async with httpx.AsyncClient() as client:
        remoteok_jobs, remotive_jobs, wwr_jobs, himalayas_jobs = await asyncio.gather(
            fetch_remoteok(client),
            fetch_remotive(client),
            fetch_wwr(client),
            fetch_himalayas(client),
        )
    all_jobs = remoteok_jobs + remotive_jobs + wwr_jobs + himalayas_jobs
    # Optional Playwright SA sources
    if INCLUDE_SOURCES:
        sa_tasks = []
        if "pnet" in INCLUDE_SOURCES:
            sa_tasks.append(_scrape_pnet(client))
        if "simply hired" in INCLUDE_SOURCES or "simplyhired" in INCLUDE_SOURCES:
            sa_tasks.append(_scrape_simplyhired(client))
        if "indeed" in INCLUDE_SOURCES:
            sa_tasks.append(_scrape_indeed(client))
        if "talent.com" in INCLUDE_SOURCES:
            sa_tasks.append(_scrape_talent(client))
        if "careers24" in INCLUDE_SOURCES:
            sa_tasks.append(_scrape_careers24(client))
        if sa_tasks:
            sa_results = await asyncio.gather(*sa_tasks, return_exceptions=True)
            for r in sa_results:
                if isinstance(r, list):
                    all_jobs.extend(r)
    filtered = [j for j in all_jobs if matches_keywords(j)]
    seen = set()
    deduped = []
    for j in filtered:
        key = (normalize(j["title"]), normalize(j["company"]), j["source"])
        if key not in seen:
            seen.add(key)
            deduped.append(j)
    deduped.sort(key=lambda j: j["posted_at"], reverse=True)
    return JSONResponse(content=deduped)

@app.get("/health")
async def health():
    return {"status": "ok"}

# --- Frontend stub (Google Jobs-style) ---
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JobHunter — Daily Feed</title>
<style>
  :root {
    --bg: #0f1115;
    --panel: #161b22;
    --panel-2: #1c2129;
    --border: #262c36;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #4f8cff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text);
  }
  header {
    position: sticky; top: 0; z-index: 10;
    background: rgba(22,27,34,.82);
    backdrop-filter: saturate(140%) blur(10px);
    border-bottom: 1px solid var(--border);
  }
  .bar {
    max-width: 860px; margin: 0 auto; padding: 14px 16px;
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
  }
  .bar h1 { font-size: 18px; margin: 0; font-weight: 700; letter-spacing: .2px; }
  .pill {
    border-radius: 999px; background: var(--panel-2); border: 1px solid var(--border);
    color: var(--text); padding: 6px 10px; font-size: 13px;
  }
  .accent { color: var(--accent); }
  main { max-width: 860px; margin: 0 auto; padding: 14px 16px 80px; }
  .card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 16px; padding: 14px; margin-bottom: 12px;
    transition: transform .12s ease, box-shadow .12s ease;
  }
  .card:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,.25); }
  .row { display: flex; gap: 12px; align-items: flex-start; }
  .logo {
    width: 44px; height: 44px; border-radius: 12px;
    display: grid; place-items: center; font-weight: 800; font-size: 14px; color: white;
    background: linear-gradient(135deg,#6366f1,#8b5cf6);
    flex-shrink: 0;
  }
  .title { font-weight: 700; font-size: 15px; line-height: 1.3; margin: 0 0 4px; }
  .meta { color: var(--muted); font-size: 13px; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .tag {
    background: var(--panel-2); border: 1px solid var(--border);
    padding: 4px 8px; border-radius: 999px; font-size: 12px; color: var(--muted);
  }
  .actions { display: flex; gap: 8px; margin-top: 12px; }
  a.btn {
    text-decoration: none; padding: 8px 12px; border-radius: 10px; font-size: 13px; font-weight: 600;
    background: var(--accent); color: white;
  }
  .muted { color: var(--muted); font-size: 12px; margin-top: 8px; }
  .empty { text-align: center; padding: 40px 10px; color: var(--muted); }
</style>
</head>
<body>
<header>
  <div class="bar">
    <h1>Jobs</h1>
    <div class="pill" id="clock">Updated just now</div>
  </div>
</header>
<main>
  <div id="jobs"></div>
  <div id="empty" class="empty" style="display:none">No jobs found. Check back later.</div>
</main>
<script>
const elJobs = document.getElementById('jobs');
const elEmpty = document.getElementById('empty');
const elClock = document.getElementById('clock');
async function load() {
  try {
    const res = await fetch('/api/jobs/today', {cache:'no-store'});
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const jobs = await res.json();
    render(jobs);
  } catch (e) {
    elJobs.innerHTML = '<div class="empty">Failed to load jobs.</div>';
  }
}
function timeAgo(iso) {
  const now = new Date();
  const then = new Date(iso);
  const seconds = Math.floor((now - then)/1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds/60);
  if (minutes < 60) return minutes + 'm ago';
  const hours = Math.floor(minutes/60);
  if (hours < 24) return hours + 'h ago';
  return Math.floor(hours/24) + 'd ago';
}
function initials(name) {
  return (name || '?').split(/[^a-zA-Z0-9]+/).filter(Boolean).map(w => w[0]).slice(0,2).join('').toUpperCase();
}
function render(jobs) {
  if (!jobs.length) { elJobs.innerHTML = ''; elEmpty.style.display = 'block'; return; }
  elEmpty.style.display = 'none';
  elJobs.innerHTML = jobs.map(j => {
    const tags = (j.tags || []).slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('');
    return `
    <article class="card">
      <div class="row">
        <div class="logo">${initials(j.company)}</div>
        <div style="min-width:0;flex:1">
          <h2 class="title">${j.title}</h2>
          <div class="meta">${j.company} · ${j.location}</div>
          <div class="tags">${tags}</div>
          <div class="actions">
            <a class="btn" href="${j.url}" target="_blank" rel="noreferrer">Apply ↗</a>
          </div>
          <div class="muted">${j.source} · ${timeAgo(j.posted_at)} · ${j.job_type}</div>
        </div>
      </div>
    </article>`;
  }).join('');
}
load();
setInterval(load, {{REFRESH_MS}});
setTimeout(() => { elClock.textContent = 'Updated just now'; }, 1000);
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML.replace("{{REFRESH_MS}}", str(REFRESH_MS))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="warning")
