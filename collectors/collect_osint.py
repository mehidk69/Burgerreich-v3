#!/usr/bin/env python3
"""
Supplementary OSINT feed collector.
Pulls from public defence/geopolitical RSS feeds outside the 5 COCOMs.
"""

from utils import fetch_rss, save_data, make_id, normalize_date, classify_tag, log

FEEDS: list[dict] = [
    {
        "url": "https://news.usni.org/feed",
        "source": "USNI News",
        "cocom": "osint",
    },
    {
        "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945",
        "source": "DoD News",
        "cocom": "osint",
    },
    {
        "url": "https://www.csis.org/analysis/feed",
        "source": "CSIS",
        "cocom": "osint",
    },
    {
        "url": "https://www.janes.com/feeds/news",
        "source": "Janes",
        "cocom": "osint",
    },
]


def collect() -> int:
    all_items: list[dict] = []

    for feed_cfg in FEEDS:
        url = feed_cfg["url"]
        source = feed_cfg["source"]
        cocom = feed_cfg["cocom"]

        log("info", "osint", f"Fetching {source}: {url}")
        entries = fetch_rss(url)

        for entry in entries:
            title = entry.get("title", "").strip()
            if not title:
                continue
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            published = entry.get("published", entry.get("updated", ""))

            all_items.append({
                "id": make_id(source, title),
                "title": title,
                "url": link,
                "date": normalize_date(published),
                "source": source,
                "cocom": cocom,
                "tag": classify_tag(title, summary),
                "summary": (summary[:300].strip()) if summary else "",
            })

    if not all_items:
        log("warn", "osint", "No OSINT items collected")
        return 0

    count = save_data("osint.json", all_items)
    log("info", "osint", f"OSINT collection complete — {count} items")
    return count


if __name__ == "__main__":
    collect()
