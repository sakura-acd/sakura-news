#!/usr/bin/env python3
"""
Sample: Yahoo! JAPAN News RSS fetch ONLY (no translation, no API needed).

Yesले Yahoo News RSS feeds fetch garcha ra headlines print + JSON ma save garcha.
Testing/sample ko lagi ho - translation pachi thapinchha.

Run:
  python fetch_news_sample.py
"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import Request, urlopen

# ---- Config ----------------------------------------------------------------

FEEDS = {
    "top-picks": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
    "domestic": "https://news.yahoo.co.jp/rss/topics/domestic.xml",
    "world": "https://news.yahoo.co.jp/rss/topics/world.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml",
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
}

MAX_ITEMS_PER_FEED = 5
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "news_sample.json")
USER_AGENT = "Mozilla/5.0 (compatible; SakuraNewsBot/1.0; +https://learnwithsakura.com)"


# ---- RSS fetching -----------------------------------------------------------

def fetch_rss(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_items(xml_text: str, category: str, limit: int):
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  [!] XML parse error for {category}: {e}")
        return items

    channel = root.find("channel")
    if channel is None:
        return items

    for item in channel.findall("item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        items.append({
            "category": category,
            "title_ja": title,
            "link": link,
            "pub_date": pub_date,
        })
    return items


# ---- Main --------------------------------------------------------------------

def main():
    all_items = []

    for category, url in FEEDS.items():
        print(f"\nFetching [{category}] {url}")
        try:
            xml_text = fetch_rss(url)
        except Exception as e:
            print(f"  [!] Fetch failed: {e}")
            continue

        items = parse_items(xml_text, category, MAX_ITEMS_PER_FEED)
        print(f"  Found {len(items)} items:")
        for it in items:
            print(f"    - {it['title_ja']}")
        all_items.extend(items)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(all_items),
            "items": all_items,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(all_items)} total headlines saved to:\n  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
