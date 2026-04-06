#!/usr/bin/env python3
"""
Equipment losses collector.
Scrapes news feeds for reports of US military equipment losses.
Output: losses.json
"""

from utils import fetch_rss, log, DATA_DIR, normalize_date, make_id
import json
import re
from datetime import datetime, timezone

SOURCES = [
    ("https://www.centcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=104&max=25", "CENTCOM"),
    ("https://news.usni.org/feed", "USNI News"),
    ("https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945", "DoD News"),
]

LOSS_KEYWORDS = [
    "destroyed", "shot down", "crashed", "lost", "downed",
    "damage", "damaged", "struck", "hit", "fire",
    "wreckage", "debris", "intercepted",
]

EQUIPMENT_TYPES = [
    ("MQ-9", "MQ-9 Reaper"),
    ("MQ-1", "MQ-1 Predator"),
    ("RQ-4", "RQ-4 Global Hawk"),
    ("F-35", "F-35"),
    ("F-15", "F-15"),
    ("F-16", "F-16"),
    ("F/A-18", "F/A-18"),
    ("B-52", "B-52H Stratofortress"),
    ("B-2", "B-2 Spirit"),
    ("KC-135", "KC-135 Stratotanker"),
    ("KC-46", "KC-46 Pegasus"),
    ("C-17", "C-17 Globemaster"),
    ("E-3", "E-3 Sentry AWACS"),
    ("E-6", "E-6B Mercury"),
    ("P-8", "P-8A Poseidon"),
    ("THAAD", "THAAD"),
    ("Patriot", "Patriot"),
    ("CVN", "Aircraft Carrier"),
    ("DDG", "Destroyer"),
    ("LHD", "Amphibious Assault Ship"),
]

QTY_PATTERN = re.compile(r"(\d+)\s+(?:" + "|".join(re.escape(t[0]) for t in EQUIPMENT_TYPES) + ")", re.IGNORECASE)


def collect():
    log("info", "losses", "Starting equipment loss collection")

    items = []

    for feed_url, source_name in SOURCES:
        entries = fetch_rss(feed_url)
        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}".lower()

            # Must mention a loss keyword
            if not any(kw in text for kw in LOSS_KEYWORDS):
                continue

            # Check for equipment type mentions
            for prefix, full_name in EQUIPMENT_TYPES:
                if prefix.lower() in text:
                    # Try to extract quantity
                    qty_match = re.search(rf"(\d+)\s*{re.escape(prefix)}", text, re.IGNORECASE)
                    qty = int(qty_match.group(1)) if qty_match else 1

                    items.append({
                        "id": make_id(source_name, title, full_name),
                        "type": full_name,
                        "qty": qty,
                        "source": source_name,
                        "date": normalize_date(entry.get("published", "")),
                        "headline": title.strip(),
                    })

    # Deduplicate by id
    seen = set()
    unique = []
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    losses = {
        "items": unique,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "losses.json"
    out.write_text(json.dumps(losses, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "losses", f"Saved {len(unique)} loss items to losses.json")
    return len(unique)


if __name__ == "__main__":
    collect()
