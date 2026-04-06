"""
Shared COCOM collector logic.
Each command-specific script just provides URLs and metadata;
this module does the actual collection, parsing, and persistence.
"""

from utils import fetch_rss, fetch_page, extract_links, save_data, make_id, normalize_date, classify_tag, log


def _parse_rss_entries(entries: list[dict], source: str, cocom: str) -> list[dict]:
    """Convert raw RSS/feedparser entries into normalised item dicts."""
    items: list[dict] = []
    for entry in entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        published = entry.get("published", entry.get("updated", ""))

        items.append({
            "id": make_id(cocom, title),
            "title": title,
            "url": link,
            "date": normalize_date(published),
            "source": source,
            "cocom": cocom,
            "tag": classify_tag(title, summary),
            "summary": (summary[:300].strip()) if summary else "",
        })
    return items


def _scrape_fallback(url: str, source: str, cocom: str) -> list[dict]:
    """HTML-scrape fallback when RSS is unavailable."""
    log("info", cocom, f"Trying HTML fallback: {url}")
    html = fetch_page(url)
    if not html:
        return []
    links = extract_links(html, selector="a[href]", base_url=url.split("/", 3)[0] + "//" + url.split("/")[2])
    items: list[dict] = []
    for link in links:
        title = link["text"].strip()
        if len(title) < 15:  # skip nav links
            continue
        items.append({
            "id": make_id(cocom, title),
            "title": title,
            "url": link["url"],
            "date": normalize_date(""),
            "source": source,
            "cocom": cocom,
            "tag": classify_tag(title),
            "summary": "",
        })
    return items[:25]


def collect_cocom(
    feed_url: str,
    alt_url: str,
    cocom: str,
    source: str,
    output: str,
) -> int:
    """
    Main collection entry-point for a COCOM.
    1. Try RSS feed
    2. Fallback to HTML scrape if RSS fails
    3. Deduplicate + persist
    Returns number of items saved.
    """
    log("info", cocom, f"Starting collection for {source}")

    entries = fetch_rss(feed_url)
    items = _parse_rss_entries(entries, source, cocom)

    if not items and alt_url:
        items = _scrape_fallback(alt_url, source, cocom)

    if not items:
        log("warn", cocom, "No items collected")
        return 0

    count = save_data(output, items)
    log("info", cocom, f"Collection complete — {count} items in {output}")
    return count
