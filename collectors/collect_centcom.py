#!/usr/bin/env python3
"""
CENTCOM press-release collector.
Source: https://www.centcom.mil/MEDIA/PRESS-RELEASES/
"""

from collector_base import collect_cocom

FEED_URL = "https://www.centcom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=104&max=25"
ALT_URL  = "https://www.centcom.mil/MEDIA/PRESS-RELEASES/"

if __name__ == "__main__":
    collect_cocom(
        feed_url=FEED_URL,
        alt_url=ALT_URL,
        cocom="centcom",
        source="CENTCOM",
        output="centcom.json",
    )
