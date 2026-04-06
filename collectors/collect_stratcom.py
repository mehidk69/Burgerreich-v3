#!/usr/bin/env python3
"""
STRATCOM news collector.
Source: https://www.stratcom.mil/Media/News/
"""

from collector_base import collect_cocom

FEED_URL = "https://www.stratcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=107&max=25"
ALT_URL  = "https://www.stratcom.mil/Media/News/"

if __name__ == "__main__":
    collect_cocom(
        feed_url=FEED_URL,
        alt_url=ALT_URL,
        cocom="stratcom",
        source="STRATCOM",
        output="stratcom.json",
    )
