"""
Burgerreich Watch v3 — Shared collector utilities.
Provides RSS fetching, dedup, classification, date normalization, and data persistence.
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UA = "BurgerreichWatch/3.0 (OSINT collector; +https://github.com/mehidk69/Burgerreich-v3)"
DATA_DIR = Path(__file__).resolve().parent.parent / "site" / "data"
MAX_ITEMS_PER_FEED = 60
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each retry
REQUEST_TIMEOUT = 30  # seconds

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def log(level: str, source: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [{level.upper():5}] [{source}] {msg}", file=sys.stderr)

# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def make_id(*parts: str) -> str:
    """Deterministic 12-char hex ID from any number of string parts."""
    blob = "|".join(str(p) for p in parts if p)
    return hashlib.md5(blob.encode()).hexdigest()[:12]

# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------

_DATE_FMTS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%b %d, %Y",
    "%d %b %Y",
]

def normalize_date(raw: str) -> str:
    """Parse various date formats to ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)."""
    if not raw:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = raw.strip()
    for fmt in _DATE_FMTS:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    # feedparser struct_time fallback
    try:
        import calendar
        tp = feedparser._parse_date(raw)
        if tp:
            ts = calendar.timegm(tp)
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# HTTP helpers with retry
# ---------------------------------------------------------------------------

_session = requests.Session()
_session.headers.update({"User-Agent": UA})

def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response | None:
    """HTTP request with exponential-backoff retry."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    delay = RETRY_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = _session.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                log("error", "http", f"Failed after {MAX_RETRIES} attempts: {url} — {exc}")
                return None
            log("warn", "http", f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {exc}")
            time.sleep(delay)
            delay *= 2
    return None

def fetch_rss(url: str) -> list[dict]:
    """Fetch and parse an RSS/Atom feed, returning list of entry dicts."""
    log("info", "rss", f"Fetching {url}")
    resp = _request_with_retry("GET", url)
    if not resp:
        return []
    feed = feedparser.parse(resp.text)
    if feed.bozo and not feed.entries:
        log("warn", "rss", f"Feed parse warning for {url}: {feed.bozo_exception}")
        return []
    log("info", "rss", f"Got {len(feed.entries)} entries from {url}")
    return [dict(e) for e in feed.entries]

def fetch_page(url: str) -> str:
    """Fetch raw HTML page content."""
    resp = _request_with_retry("GET", url)
    return resp.text if resp else ""

def fetch_json(url: str) -> dict | list | None:
    """Fetch and parse JSON from a URL."""
    resp = _request_with_retry("GET", url)
    if not resp:
        return None
    try:
        return resp.json()
    except ValueError:
        log("error", "json", f"Invalid JSON from {url}")
        return None

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

_TAG_RULES: list[tuple[str, list[str]]] = [
    ("alert",    ["strike", "strikes", "attack", "missile", "intercept", "shoot",
                  "destroy", "neutralize", "killed", "casualt", "wounded", "raid"]),
    ("naval",    ["carrier", "cvn", "ship", "fleet", "navy", "destroyer", "cruiser",
                  "submarine", "frigate", "amphibious", "uss ", "maritime", "patrol"]),
    ("air",      ["aircraft", "bomber", "fighter", "f-35", "f-16", "b-52", "b-2",
                  "drone", "mq-9", "sortie", "airborne", "airlift", "kc-135",
                  "tanker", "awacs", "e-3", "uav", "rpa", "aerial"]),
    ("exercise", ["exercise", "drill", "training", "wargame", "readiness",
                  "bilateral", "multilateral", "joint exercise"]),
    ("posture",  ["deploy", "reposition", "reinforce", "rotation", "forward",
                  "permanent", "station", "base", "posture", "presence"]),
    ("ground",   ["troop", "soldier", "infantry", "brigade", "division", "battalion",
                  "armor", "artillery", "army", "marine corps", "regiment"]),
]

def classify_tag(title: str, summary: str = "") -> str:
    """Auto-classify an item into a category based on keyword matching."""
    text = f"{title} {summary}".lower()
    scores: dict[str, int] = {}
    for tag, keywords in _TAG_RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[tag] = score
    if not scores:
        return "general"
    return max(scores, key=scores.get)

# ---------------------------------------------------------------------------
# Data persistence
# ---------------------------------------------------------------------------

def load_existing(filename: str) -> list[dict]:
    """Load existing JSON data from the data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        log("warn", "data", f"Could not load {path}: {exc}")
        return []

def save_data(filename: str, new_items: list[dict]) -> int:
    """
    Merge new items with existing, deduplicate by ID, keep newest MAX_ITEMS_PER_FEED.
    Returns count of items saved.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_existing(filename)

    seen_ids: set[str] = set()
    merged: list[dict] = []
    for item in new_items + existing:
        item_id = item.get("id", "")
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            merged.append(item)

    # Sort by date descending
    merged.sort(key=lambda x: x.get("date", ""), reverse=True)
    merged = merged[:MAX_ITEMS_PER_FEED]

    path = DATA_DIR / filename
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "data", f"Saved {len(merged)} items to {path.name} ({len(new_items)} new)")
    return len(merged)

# ---------------------------------------------------------------------------
# HTML scraping helpers
# ---------------------------------------------------------------------------

def extract_text(html: str, selector: str = "body") -> str:
    """Extract clean text from HTML using a CSS selector."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    el = soup.select_one(selector)
    return el.get_text(separator=" ", strip=True) if el else ""

def extract_links(html: str, selector: str = "a[href]", base_url: str = "") -> list[dict]:
    """Extract links from HTML matching a CSS selector."""
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    results = []
    for a in soup.select(selector):
        href = a.get("href", "")
        if href and not href.startswith(("#", "javascript:")):
            if base_url and href.startswith("/"):
                href = base_url.rstrip("/") + href
            results.append({"text": a.get_text(strip=True), "url": href})
    return results
