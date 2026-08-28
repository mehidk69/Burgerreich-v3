#!/usr/bin/env python3
"""
Equipment losses collector.
Scrapes news feeds for reports of US military equipment losses/damage.
Output: losses.json

The dashboard hydration code:
1. Updates qty on seed items that match by equipment type prefix
2. Appends entirely new items to a "LIVE REPORTS" category
"""

from utils import fetch_rss, fetch_page, log, DATA_DIR, normalize_date, make_id
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

FEED_SOURCES = [
    ("https://www.centcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=104&max=25", "CENTCOM"),
    ("https://news.usni.org/feed", "USNI News"),
    ("https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945", "DoD News"),
    ("https://www.csis.org/analysis/feed", "CSIS"),
]

LOSS_KEYWORDS = [
    "destroyed", "shot down", "crashed", "lost", "downed", "wreck",
    "damage", "damaged", "struck", "hit by", "fire on", "fire aboard",
    "wreckage", "debris", "intercept", "shoot down", "shootdown",
    "went down", "crash land", "emergency land", "ditched",
    "ballistic missile", "drone strike", "attack on",
]

EQUIPMENT_TYPES = [
    ("MQ-9",    "MQ-9 Reaper"),
    ("MQ-1",    "MQ-1 Predator"),
    ("RQ-4",    "RQ-4 Global Hawk"),
    ("RQ-7",    "RQ-7 Shadow"),
    ("F-35",    "F-35 Lightning II"),
    ("F-15",    "F-15E Strike Eagle"),
    ("F-16",    "F-16 Fighting Falcon"),
    ("F/A-18",  "F/A-18 Hornet"),
    ("B-52",    "B-52H Stratofortress"),
    ("B-2",     "B-2 Spirit"),
    ("B-1",     "B-1B Lancer"),
    ("KC-135",  "KC-135 Stratotanker"),
    ("KC-46",   "KC-46 Pegasus"),
    ("C-17",    "C-17 Globemaster III"),
    ("C-130",   "C-130 Hercules"),
    ("E-3",     "E-3 Sentry AWACS"),
    ("E-6",     "E-6B Mercury"),
    ("E-7",     "E-7 Wedgetail"),
    ("P-8",     "P-8A Poseidon"),
    ("V-22",    "V-22 Osprey"),
    ("THAAD",   "THAAD"),
    ("Patriot",  "Patriot"),
    ("CVN",     "Aircraft Carrier"),
    ("DDG",     "Destroyer"),
    ("LHD",     "Amphibious Assault Ship"),
    ("LCS",     "Littoral Combat Ship"),
    ("SATCOM",  "SATCOM Terminal"),
    ("Humvee",  "HMMWV"),
    ("MRAP",    "MRAP"),
    ("Abrams",  "M1 Abrams"),
    ("Bradley", "M2 Bradley"),
    ("Stryker", "Stryker"),
]


def extract_loss_context(text: str, equipment_prefix: str) -> str:
    """Extract surrounding context for an equipment mention."""
    idx = text.lower().find(equipment_prefix.lower())
    if idx < 0:
        return ""
    start = max(0, idx - 100)
    end = min(len(text), idx + 150)
    return text[start:end].strip()


def collect():
    log("info", "losses", "Starting equipment loss collection")

    items = []

    for feed_url, source_name in FEED_SOURCES:
        entries = fetch_rss(feed_url)
        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}"
            text_lower = text.lower()

            # Must mention a loss keyword
            if not any(kw in text_lower for kw in LOSS_KEYWORDS):
                continue

            # Check for equipment type mentions
            for prefix, full_name in EQUIPMENT_TYPES:
                if prefix.lower() in text_lower:
                    # Try to extract quantity
                    qty_match = re.search(
                        rf"(\d+)\s*(?:x\s*)?{re.escape(prefix)}",
                        text, re.IGNORECASE
                    )
                    qty = int(qty_match.group(1)) if qty_match else 1

                    context = extract_loss_context(text, prefix)

                    items.append({
                        "id": make_id(source_name, title, full_name),
                        "type": full_name,
                        "qty": qty,
                        "source": source_name,
                        "date": normalize_date(entry.get("published", "")),
                        "headline": title.strip(),
                        "context": context[:200] if context else "",
                        "url": entry.get("link", ""),
                    })

    # Deduplicate by id, keeping highest qty per type
    by_id = {}
    for item in items:
        existing = by_id.get(item["id"])
        if not existing or item["qty"] > existing["qty"]:
            by_id[item["id"]] = item
    unique = list(by_id.values())

    # Sort by date descending
    unique.sort(key=lambda x: x.get("date", ""), reverse=True)

    losses = {
        "items": unique,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "losses.json"

    # Merge with existing data (keep items from previous runs)
    existing_items = []
    if (DATA_DIR / "losses.json").exists():
        try:
            existing = json.loads((DATA_DIR / "losses.json").read_text(encoding="utf-8"))
            existing_items = existing.get("items", [])
        except (json.JSONDecodeError, OSError):
            pass

    # Merge: new items take priority, keep old items not in new set
    merged_ids = {i["id"] for i in unique}
    for old_item in existing_items:
        if old_item.get("id") and old_item["id"] not in merged_ids:
            unique.append(old_item)
            merged_ids.add(old_item["id"])

    unique.sort(key=lambda x: x.get("date", ""), reverse=True)
    unique = unique[:100]  # Cap at 100

    losses["items"] = unique
    out.write_text(json.dumps(losses, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "losses", f"Saved {len(unique)} loss items to losses.json")
    return len(unique)


if __name__ == "__main__":
    collect()
