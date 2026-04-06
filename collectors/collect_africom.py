#!/usr/bin/env python3
"""
AFRICOM press-release collector.
Source: https://www.africom.mil/pressrelease
"""

from collector_base import collect_cocom

FEED_URL = "https://www.africom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=106&max=25"
ALT_URL  = "https://www.africom.mil/pressrelease"

if __name__ == "__main__":
    collect_cocom(
        feed_url=FEED_URL,
        alt_url=ALT_URL,
        cocom="africom",
        source="AFRICOM",
        output="africom.json",
    )
