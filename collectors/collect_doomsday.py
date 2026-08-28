#!/usr/bin/env python3
"""
Doomsday Clock collector.
Scrapes the Bulletin of the Atomic Scientists for the current clock setting.
Output: doomsday.json
"""

from utils import fetch_page, log, DATA_DIR
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

BAS_URL = "https://thebulletin.org/doomsday-clock/"


def collect():
    log("info", "doomsday", "Fetching Doomsday Clock data")

    html = fetch_page(BAS_URL)
    seconds = None
    description = ""

    if html:
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator=" ", strip=True)

        # Look for "X seconds to midnight" pattern
        patterns = [
            re.compile(r"(\d+)\s*seconds?\s*to\s*midnight", re.IGNORECASE),
            re.compile(r"(\d+)\s*seconds?\s*before\s*midnight", re.IGNORECASE),
            re.compile(r"clock.*?(\d+)\s*seconds?", re.IGNORECASE),
        ]

        for pattern in patterns:
            match = pattern.search(text)
            if match:
                seconds = int(match.group(1))
                break

        # Try to get description
        desc_match = re.search(r"(It is now.*?midnight\.)", text)
        if desc_match:
            description = desc_match.group(1)

    data = {
        "seconds_to_midnight": seconds,
        "description": description,
        "source": "Bulletin of the Atomic Scientists",
        "url": BAS_URL,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "doomsday.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "doomsday", f"Doomsday Clock: {seconds}s to midnight")
    return 1


if __name__ == "__main__":
    collect()
