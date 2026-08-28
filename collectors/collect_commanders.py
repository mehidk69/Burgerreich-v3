#!/usr/bin/env python3
"""
COCOM commander data collector.
Scrapes official COCOM leadership pages for current commander names.
Output: commanders.json
"""

from utils import fetch_page, extract_text, log, DATA_DIR
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

COCOM_URLS = {
    "centcom":   "https://www.centcom.mil/ABOUT-US/LEADERSHIP/",
    "eucom":     "https://www.eucom.mil/about-us/leadership/combatant-commander",
    "indopacom": "https://www.pacom.mil/Leadership/Commander/",
    "northcom":  "https://www.northcom.mil/Leadership/Commander/",
    "southcom":  "https://www.southcom.mil/Leadership/Commander/",
    "africom":   "https://www.africom.mil/about-the-command/leadership/commander",
    "stratcom":  "https://www.stratcom.mil/Leadership/Commander/",
    "cybercom":  "https://www.cybercom.mil/About/Leadership/",
    "spacecom":  "https://www.spacecom.mil/About/Leadership/Commander/",
    "transcom":  "https://www.ustranscom.mil/cmd/commander.cfm",
    "socom":     "https://www.socom.mil/about/leadership",
}

RANK_PREFIXES = [
    "General", "Gen.", "Gen ",
    "Admiral", "Adm.", "Adm ",
    "Lt. Gen.", "Vice Adm.",
    "GEN ", "ADM ",
]

NAME_PATTERN = re.compile(
    r"(?:Gen(?:eral)?\.?|Adm(?:iral)?\.?|Lt\.?\s*Gen\.?|Vice\s*Adm\.?)\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    re.MULTILINE
)


def extract_commander(html: str, cocom: str) -> str:
    """Try to extract commander name from a leadership page."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    # Try common patterns: h1/h2/h3 with rank
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
        text = tag.get_text(strip=True)
        if any(prefix in text for prefix in RANK_PREFIXES):
            # Clean up
            name = text.strip()
            if len(name) < 80:
                return name

    # Fallback: regex on full page text
    text = soup.get_text(separator=" ", strip=True)
    match = NAME_PATTERN.search(text)
    if match:
        # Return the full match including rank
        start = max(0, match.start() - 15)
        snippet = text[start:match.end()]
        # Find the rank prefix
        for prefix in RANK_PREFIXES:
            idx = snippet.find(prefix)
            if idx >= 0:
                return snippet[idx:].strip()
        return match.group(0).strip()

    return ""


def collect():
    log("info", "commanders", "Starting commander data collection")

    commanders = {}

    for cocom, url in COCOM_URLS.items():
        log("info", "commanders", f"Fetching {cocom}: {url}")
        html = fetch_page(url)
        name = extract_commander(html, cocom)
        if name:
            commanders[cocom] = {"name": name, "url": url}
            log("info", "commanders", f"  {cocom}: {name}")
        else:
            log("warn", "commanders", f"  {cocom}: could not extract name")
            commanders[cocom] = {"name": "check manually", "url": url}

    data = {
        "commanders": commanders,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "commanders.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "commanders", f"Saved {len(commanders)} commander entries")
    return len(commanders)


if __name__ == "__main__":
    collect()
