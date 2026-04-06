#!/usr/bin/env python3
"""
INDOPACOM news collector.
Source: https://www.pacom.mil/Media/News/
"""

from collector_base import collect_cocom

FEED_URL = "https://www.pacom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=108&max=25"
ALT_URL  = "https://www.pacom.mil/Media/News/"

if __name__ == "__main__":
    collect_cocom(
        feed_url=FEED_URL,
        alt_url=ALT_URL,
        cocom="indopacom",
        source="INDOPACOM",
        output="indopacom.json",
    )
