#!/usr/bin/env python3
"""
Fleet position collector.
Scrapes USNI News Fleet Tracker for current CSG/ARG positions.
Falls back to DoD press releases for fleet movement data.
Output: fleet.json
"""

from utils import fetch_page, fetch_rss, extract_text, save_data, log, DATA_DIR, normalize_date
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

USNI_FLEET_URL = "https://news.usni.org/category/fleet-tracker"
USNI_RSS = "https://news.usni.org/category/fleet-tracker/feed"

# Hull numbers to match against
CARRIER_HULLS = [
    "CVN-68", "CVN-69", "CVN-70", "CVN-71", "CVN-72",
    "CVN-73", "CVN-74", "CVN-75", "CVN-76", "CVN-77", "CVN-78"
]

ARG_HULLS = [
    "LHD-1", "LHD-2", "LHD-3", "LHD-4", "LHD-5",
    "LHA-6", "LHA-7", "LHD-8"
]

STATUS_KEYWORDS = {
    "deployed": ["deployed", "operating", "underway", "on station", "patrol"],
    "transit": ["transit", "en route", "transiting", "heading"],
    "homeport": ["homeport", "home port", "returned", "in port"],
    "maintenance": ["maintenance", "overhaul", "rcoh", "dry dock", "repair"],
}


def classify_status(text: str) -> str:
    text_lower = text.lower()
    for status, keywords in STATUS_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return status
    return "deployed"


def extract_fleet_from_article(html: str) -> dict:
    """Parse a USNI fleet tracker article for carrier/ARG data."""
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one(".entry-content") or soup.select_one("article") or soup
    text = content.get_text(separator="\n", strip=True)

    carriers = []
    args = []

    # Look for hull numbers and surrounding context
    for hull in CARRIER_HULLS:
        pattern = re.compile(rf"(.{{0,200}}{re.escape(hull)}.{{0,200}})", re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(text)
        for match in matches:
            carriers.append({
                "hull": hull,
                "status": classify_status(match),
                "location": match.strip()[:150],
            })

    for hull in ARG_HULLS:
        pattern = re.compile(rf"(.{{0,200}}{re.escape(hull)}.{{0,200}})", re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(text)
        for match in matches:
            args.append({
                "hull": hull,
                "status": classify_status(match),
                "location": match.strip()[:150],
            })

    return {"carriers": carriers, "args": args}


def collect():
    log("info", "fleet", "Starting fleet position collection")

    # Try RSS first for latest fleet tracker article
    entries = fetch_rss(USNI_RSS)
    fleet_data = {"carriers": [], "args": [], "updated": ""}

    for entry in entries[:3]:  # Check up to 3 most recent articles
        link = entry.get("link", "")
        if not link:
            continue
        log("info", "fleet", f"Checking article: {link}")
        html = fetch_page(link)
        if not html:
            continue
        result = extract_fleet_from_article(html)
        if result["carriers"] or result["args"]:
            fleet_data["carriers"] = result["carriers"]
            fleet_data["args"] = result["args"]
            fleet_data["updated"] = normalize_date(entry.get("published", ""))
            break

    # Deduplicate by hull
    seen = set()
    unique_carriers = []
    for c in fleet_data["carriers"]:
        if c["hull"] not in seen:
            seen.add(c["hull"])
            unique_carriers.append(c)
    fleet_data["carriers"] = unique_carriers

    seen = set()
    unique_args = []
    for a in fleet_data["args"]:
        if a["hull"] not in seen:
            seen.add(a["hull"])
            unique_args.append(a)
    fleet_data["args"] = unique_args

    if not fleet_data["updated"]:
        fleet_data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Write fleet.json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "fleet.json"
    out.write_text(json.dumps(fleet_data, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "fleet", f"Saved {len(fleet_data['carriers'])} carriers, {len(fleet_data['args'])} ARGs to fleet.json")
    return len(fleet_data["carriers"])


if __name__ == "__main__":
    collect()
