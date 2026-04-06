#!/usr/bin/env python3
"""
EUCOM news collector.
Source: https://www.eucom.mil/media-hub/news
"""

from collector_base import collect_cocom

FEED_URL = "https://www.eucom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=105&max=25"
ALT_URL  = "https://www.eucom.mil/media-hub/news"

if __name__ == "__main__":
    collect_cocom(
        feed_url=FEED_URL,
        alt_url=ALT_URL,
        cocom="eucom",
        source="EUCOM",
        output="eucom.json",
    )
