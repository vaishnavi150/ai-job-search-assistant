"""Live job search over free, keyless public job boards, ranked against the
user's resume.

Sources:
- Remotive (remote jobs worldwide) - https://remotive.com/api/remote-jobs
- Arbeitnow (mostly Europe, many remote) - https://www.arbeitnow.com/api/job-board-api

Both ask API users not to hammer them (Remotive suggests a few calls a
day), so each board's full feed is fetched at most once per
JOB_CACHE_MINUTES and searched locally. Listings link back to the original
post, as both boards require.
"""
import html
import logging
import re
import threading
import time
from dataclasses import dataclass, field

import numpy as np
import requests

from app.config import settings

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_html(raw: str | None) -> str:
    text = _TAG_RE.sub(" ", raw or "")
    return _WS_RE.sub(" ", html.unescape(text)).strip()


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    tags: list[str]
    description: str
    job_type: str | None = None
    salary: str | None = None
    posted_at: str | None = None
    search_text: str = field(default="", repr=False)

    def __post_init__(self):
        self.search_text = " ".join(
            [self.title, self.company, self.location, " ".join(self.tags), self.description[:3000]]
        ).lower()


def _fetch_remotive() -> list[Job]:
    resp = requests.get("https://remotive.com/api/remote-jobs", timeout=30)
    resp.raise_for_status()
    jobs = []
    for item in resp.json().get("jobs", []):
        if not item.get("url") or not item.get("title"):
            continue
        jobs.append(Job(
            id=f"remotive-{item.get('id')}",
            title=item["title"].strip(),
            company=(item.get("company_name") or "Unknown company").strip(),
            location=f"Remote - {item.get('candidate_required_location') or 'Worldwide'}",
            url=item["url"],
            source="Remotive",
            tags=[t for t in (item.get("tags") or []) if isinstance(t, str)][:12],
            description=_clean_html(item.get("description")),
            job_type=(item.get("job_type") or "").replace("_", " ") or None,
            salary=item.get("salary") or None,
            posted_at=(item.get("publication_date") or "")[:10] or None,
        ))
    return jobs


def _fetch_arbeitnow(pages: int = 3) -> list[Job]:
    jobs = []
    for page in range(1, pages + 1):
        resp = requests.get("https://www.arbeitnow.com/api/job-board-api", params={"page": page}, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        for item in data:
            if not item.get("url") or not item.get("title"):
                continue
            created = item.get("created_at")
            jobs.append(Job(
                id=f"arbeitnow-{item.get('slug')}",
                title=item["title"].strip(),
                company=(item.get("company_name") or "Unknown company").strip(),
                location=("Remote" + (f" / {item['location']}" if item.get("location") else ""))
                if item.get("remote") else (item.get("location") or "Not specified"),
                url=item["url"],
                source="Arbeitnow",
                tags=[t for t in (item.get("tags") or []) if isinstance(t, str)][:12],
                description=_clean_html(item.get("description")),
                job_type=", ".join(item.get("job_types") or []) or None,
                posted_at=time.strftime("%Y-%m-%d", time.gmtime(created)) if isinstance(created, int) else None,
            ))
        if not data:
            break
    return jobs


_SOURCES = {"Remotive": _fetch_remotive, "Arbeitnow": _fetch_arbeitnow}
_cache: dict[str, tuple[float, list[Job]]] = {}
# One lock per source, so a slow board doesn't hold up searches of the other.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()
# After a failed fetch with nothing cached, don't retry for a while: otherwise
# every search during an outage waits out the full request timeout again.
FAILURE_BACKOFF_SECONDS = 120
_failed_at: dict[str, float] = {}


class SourceUnavailableError(RuntimeError):
    pass


def _get_source(name: str) -> list[Job]:
    """Returns the cached feed, refreshing it if stale. On fetch failure a
    stale copy is reused if there is one; otherwise the error propagates."""
    ttl = settings.job_cache_minutes * 60
    with _locks_guard:
        lock = _locks.setdefault(name, threading.Lock())
    with lock:
        cached = _cache.get(name)
        now = time.time()
        if cached and now - cached[0] < ttl:
            return cached[1]
        if not cached and now - _failed_at.get(name, 0) < FAILURE_BACKOFF_SECONDS:
            raise SourceUnavailableError(f"{name} failed recently; not retrying yet")
        try:
            jobs = _SOURCES[name]()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Job source %s unavailable: %s", name, type(exc).__name__)
            if cached:
                return cached[1]
            _failed_at[name] = now
            raise
        _cache[name] = (time.time(), jobs)
        _failed_at.pop(name, None)
        logger.info("Fetched %d jobs from %s", len(jobs), name)
        return jobs


def _keyword_score(job: Job, terms: list[str]) -> float:
    if not terms:
        return 1.0
    title = job.title.lower()
    tags = " ".join(job.tags).lower()
    score = 0.0
    for term in terms:
        if term in title:
            score += 3
        elif term in tags:
            score += 2
        elif term in job.search_text:
            score += 1
        else:
            return 0.0  # every search word must appear somewhere
    return score


def _matches_location(job: Job, location: str, remote_only: bool) -> bool:
    loc = job.location.lower()
    if remote_only and "remote" not in loc:
        return False
    if location:
        wanted = location.lower()
        # "Worldwide"/"Anywhere" remote roles are open to every location.
        return wanted in loc or "worldwide" in loc or "anywhere" in loc
    return True


def search_jobs(query: str, location: str = "", remote_only: bool = False,
                resume_chunk_vectors: np.ndarray | None = None, limit: int = 20) -> dict:
    terms = [t for t in re.split(r"[\s,]+", query.lower().strip()) if len(t) > 1][:8]
    available, unavailable, pool = [], [], []
    for name in _SOURCES:
        try:
            pool.extend(_get_source(name))
            available.append(name)
        except Exception:
            unavailable.append(name)

    candidates = []
    seen = set()
    for job in pool:
        key = (job.title.lower(), job.company.lower())
        if key in seen or not _matches_location(job, location.strip(), remote_only):
            continue
        kw = _keyword_score(job, terms)
        if kw > 0:
            seen.add(key)
            candidates.append((kw, job))
    candidates.sort(key=lambda c: c[0], reverse=True)
    candidates = candidates[:60]

    relevance: dict[str, float] = {}
    ranked = False
    if resume_chunk_vectors is not None and len(resume_chunk_vectors) and candidates:
        from app.services.embeddings import embed_texts
        texts = [f"{j.title}. {' '.join(j.tags)}. {j.description[:600]}" for _, j in candidates]
        job_vecs = embed_texts(texts)
        sims = job_vecs @ resume_chunk_vectors.T  # (jobs, resume chunks)
        top = np.sort(sims, axis=1)[:, -3:].mean(axis=1)
        for (_, job), s in zip(candidates, top):
            relevance[job.id] = float(np.clip((s - 0.15) / 0.45, 0, 1))
        max_kw = max(c[0] for c in candidates)
        candidates.sort(key=lambda c: 0.65 * relevance[c[1].id] + 0.35 * (c[0] / max_kw), reverse=True)
        ranked = True

    results = []
    for _, job in candidates[:limit]:
        results.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "source": job.source,
            "tags": job.tags,
            "job_type": job.job_type,
            "salary": job.salary,
            "posted_at": job.posted_at,
            "snippet": job.description[:280] + ("…" if len(job.description) > 280 else ""),
            "description": job.description[:8000],
            "relevance": round(relevance[job.id], 3) if job.id in relevance else None,
        })
    return {"jobs": results, "ranked_by_resume": ranked, "sources": available, "unavailable_sources": unavailable}
