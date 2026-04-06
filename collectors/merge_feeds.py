#!/usr/bin/env python3
"""
Merge all COCOM + OSINT collector outputs into a single unified feed.
Output: site/data/feed.json
"""

import json
from pathlib import Path

from utils import DATA_DIR, log

SOURCES = [
    "centcom.json",
    "eucom.json",
    "indopacom.json",
    "africom.json",
    "stratcom.json",
    "osint.json",
]

MAX_MERGED = 150


def merge() -> int:
    all_items: list[dict] = []
    stats: dict[str, int] = {}

    for filename in SOURCES:
        path = DATA_DIR / filename
        if not path.exists():
            log("warn", "merge", f"Missing: {filename}")
            stats[filename] = 0
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                log("warn", "merge", f"Invalid format in {filename}")
                stats[filename] = 0
                continue
            stats[filename] = len(data)
            all_items.extend(data)
        except (json.JSONDecodeError, OSError) as exc:
            log("error", "merge", f"Failed to read {filename}: {exc}")
            stats[filename] = 0

    # Deduplicate by ID
    seen: set[str] = set()
    unique: list[dict] = []
    for item in all_items:
        item_id = item.get("id", "")
        if item_id and item_id not in seen:
            seen.add(item_id)
            unique.append(item)

    # Sort by date descending, cap at MAX_MERGED
    unique.sort(key=lambda x: x.get("date", ""), reverse=True)
    unique = unique[:MAX_MERGED]

    # Write merged feed
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "feed.json"
    out_path.write_text(json.dumps(unique, indent=2, ensure_ascii=False), encoding="utf-8")

    # Report
    log("info", "merge", "--- Merge Stats ---")
    for name, count in stats.items():
        log("info", "merge", f"  {name}: {count} items")
    log("info", "merge", f"  Merged (deduped): {len(unique)} items → feed.json")

    return len(unique)


if __name__ == "__main__":
    merge()
