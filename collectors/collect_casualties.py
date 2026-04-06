#!/usr/bin/env python3
"""
Casualty data collector.
Scrapes CENTCOM press releases and DoD casualty feeds for current figures.
Output: casualties.json
"""

from utils import fetch_rss, fetch_page, log, DATA_DIR, normalize_date
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

CENTCOM_RSS = "https://www.centcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=104&max=25"
DOD_RELEASES = "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945"

KIA_PATTERN = re.compile(r"(\d+)\s*(?:US\s+)?(?:service\s*members?|troops?|soldiers?|personnel)?\s*(?:were\s+)?killed", re.IGNORECASE)
WIA_PATTERN = re.compile(r"(\d+)\s*(?:US\s+)?(?:service\s*members?|troops?|soldiers?|personnel)?\s*(?:were\s+)?(?:wounded|injured)", re.IGNORECASE)
KIA_SIMPLE = re.compile(r"(\d+)\s*KIA", re.IGNORECASE)
WIA_SIMPLE = re.compile(r"(\d+)\s*WIA", re.IGNORECASE)


def extract_casualty_numbers(text: str) -> dict:
    """Extract KIA/WIA numbers from text."""
    kia = 0
    wia = 0

    for pattern in [KIA_SIMPLE, KIA_PATTERN]:
        matches = pattern.findall(text)
        for m in matches:
            val = int(m)
            if val > kia:
                kia = val

    for pattern in [WIA_SIMPLE, WIA_PATTERN]:
        matches = pattern.findall(text)
        for m in matches:
            val = int(m)
            if val > wia:
                wia = val

    return {"kia": kia, "wia": wia}


def collect():
    log("info", "casualties", "Starting casualty data collection")

    best_kia = 0
    best_wia = 0
    source = ""
    updated = ""

    # Scan CENTCOM press releases for casualty updates
    entries = fetch_rss(CENTCOM_RSS)
    for entry in entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        text = f"{title} {summary}"

        # Look for casualty-related entries
        if any(kw in text.lower() for kw in ["casualt", "killed", "wounded", "kia", "wia", "fatali"]):
            nums = extract_casualty_numbers(text)
            if nums["kia"] > best_kia:
                best_kia = nums["kia"]
                source = "CENTCOM"
                updated = normalize_date(entry.get("published", ""))
            if nums["wia"] > best_wia:
                best_wia = nums["wia"]

    # Also scan DoD news
    entries = fetch_rss(DOD_RELEASES)
    for entry in entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        text = f"{title} {summary}"

        if any(kw in text.lower() for kw in ["casualt", "killed", "wounded", "kia", "wia", "fatali"]):
            nums = extract_casualty_numbers(text)
            if nums["kia"] > best_kia:
                best_kia = nums["kia"]
                source = "DoD"
                updated = normalize_date(entry.get("published", ""))
            if nums["wia"] > best_wia:
                best_wia = nums["wia"]

    casualties = {
        "us_kia_confirmed": best_kia if best_kia > 0 else None,
        "us_wia_confirmed": best_wia if best_wia > 0 else None,
        "source": source,
        "updated": updated or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "casualties.json"
    out.write_text(json.dumps(casualties, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "casualties", f"Saved casualties: KIA={casualties['us_kia_confirmed']}, WIA={casualties['us_wia_confirmed']}")
    return 1


if __name__ == "__main__":
    collect()
