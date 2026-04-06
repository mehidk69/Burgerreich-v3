#!/usr/bin/env python3
"""
Force posture collector.
Scrapes DoD and CENTCOM releases for troop deployment numbers.
Output: posture.json
"""

from utils import fetch_rss, fetch_page, log, DATA_DIR, normalize_date
import json
import re
from datetime import datetime, timezone

SOURCES = [
    "https://www.centcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=104&max=25",
    "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945",
    "https://www.eucom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=105&max=25",
    "https://www.pacom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=108&max=25",
]

# Patterns for troop numbers in Middle East
ME_PATTERNS = [
    re.compile(r"(\d[\d,]+)\s*(?:US\s+)?(?:troops?|service\s*members?|personnel|soldiers?)\s*(?:in|across|throughout|deployed\s+to)\s*(?:the\s+)?(?:middle\s*east|centcom|region)", re.IGNORECASE),
    re.compile(r"(?:middle\s*east|centcom|region).*?(\d[\d,]+)\s*(?:troops?|service\s*members?|personnel)", re.IGNORECASE),
]


def collect():
    log("info", "posture", "Starting force posture collection")

    best_me_total = None
    source = ""
    updated = ""

    for feed_url in SOURCES:
        entries = fetch_rss(feed_url)
        for entry in entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}"

            for pattern in ME_PATTERNS:
                match = pattern.search(text)
                if match:
                    num_str = match.group(1).replace(",", "")
                    try:
                        num = int(num_str)
                        if num >= 10000:  # Sanity check — ME deployments are 40k+
                            if best_me_total is None or num > best_me_total:
                                best_me_total = num
                                source = entry.get("title", "")[:100]
                                updated = normalize_date(entry.get("published", ""))
                    except ValueError:
                        pass

    posture = {
        "total_middle_east": f"{best_me_total:,}" if best_me_total else None,
        "source": source,
        "updated": updated or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "posture.json"
    out.write_text(json.dumps(posture, indent=2, ensure_ascii=False), encoding="utf-8")
    log("info", "posture", f"Saved posture: Middle East total = {posture['total_middle_east']}")
    return 1


if __name__ == "__main__":
    collect()
