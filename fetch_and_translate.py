#!/usr/bin/env python3
"""
Sakura Academy - Yahoo! JAPAN News -> English (Google Translate API)

Flow:
  1. Fetch Yahoo!ニュース RSS feeds (Japanese headlines).
  2. Translate each new headline to English using the Google Cloud
     Translation API (v2, simple REST + API key).
  3. Save both Japanese (original) + English (translated) to
     output/news.json, in a shape similar to your existing
     grammar/vocab JSON content files.

Run:
  GOOGLE_TRANSLATE_API_KEY=xxx python fetch_and_translate.py

Env vars:
  GOOGLE_TRANSLATE_API_KEY   - required (Google Cloud Translation API key)
  MAX_ITEMS_PER_FEED         - optional, default 10
"""

import os
import json
import time
import hashlib
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ---- Config ----------------------------------------------------------------

FEEDS = {
    "top-picks": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
    "domestic": "https://news.yahoo.co.jp/rss/topics/domestic.xml",
    "world": "https://news.yahoo.co.jp/rss/topics/world.xml",
    "business": "https://news.yahoo.co.jp/rss/topics/business.xml",
    "it": "https://news.yahoo.co.jp/rss/topics/it.xml",
}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "news.json")
MAX_ITEMS_PER_FEED = int(os.environ.get("MAX_ITEMS_PER_FEED", "10"))
GOOGLE_API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
USER_AGENT = "Mozilla/5.0 (compatible; SakuraNewsBot/1.0; +https://learnwithsakura.com)"
TRANSLATE_ENDPOINT = "https://translation.googleapis.com/language/translate/v2"


# ---- RSS fetching -----------------------------------------------------------

def fetch_rss(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_rss_items(xml_text: str, category: str, limit: int):
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
        if not title or not link:
            continue
        item_id = hashlib.sha256(link.encode("utf-8")).hexdigest()[:16]
        items.append({
            "id": item_id,
            "category": category,
            "title_ja": title,
            "link": link,
            "pub_date": pub_date,
        })
    return items


# ---- Google Translate API ----------------------------------------------------

def translate_to_english(text_ja: str) -> str:
    """Translate a single Japanese string to English via Google Translate API v2."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_TRANSLATE_API_KEY is not set")

    params = urllib.parse.urlencode({
        "key": GOOGLE_API_KEY,
        "q": text_ja,
        "source": "ja",
        "target": "en",
        "format": "text",
    })
    url = f"{TRANSLATE_ENDPOINT}?{params}"

    last_err = None
    for attempt in range(3):
        try:
            req = Request(url, method="POST")
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["data"]["translations"][0]["translatedText"]
        except (HTTPError, URLError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Google Translate API failed after retries: {last_err}")


# ---- Main --------------------------------------------------------------------

def load_existing():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {item["id"]: item for item in data.get("items", [])}
            except (json.JSONDecodeError, KeyError):
                return {}
    return {}


def main():
    existing = load_existing()
    print(f"Loaded {len(existing)} existing items from {OUTPUT_PATH}")

    new_count = 0
    for category, url in FEEDS.items():
        print(f"Fetching [{category}] {url}")
        try:
            xml_text = fetch_rss(url)
        except Exception as e:
            print(f"  [!] Fetch failed: {e}")
            continue

        items = parse_rss_items(xml_text, category, MAX_ITEMS_PER_FEED)
        print(f"  Found {len(items)} items")

        for item in items:
            if item["id"] in existing:
                continue  # already translated, skip (saves API calls)
            print(f"  -> Translating: {item['title_ja'][:40]}")
            try:
                title_en = translate_to_english(item["title_ja"])
            except Exception as e:
                print(f"     [!] Translation failed: {e}")
                continue
            item["title_en"] = title_en
            item["fetched_at"] = datetime.now(timezone.utc).isoformat()
            existing[item["id"]] = item
            new_count += 1
            time.sleep(0.3)  # gentle rate limiting

    all_items = sorted(existing.values(), key=lambda x: x.get("pub_date", ""), reverse=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(all_items),
            "items": all_items,
        }, f, ensure_ascii=False, indent=2)

    print(f"Done. {new_count} new items translated. Total in file: {len(all_items)}")


if __name__ == "__main__":
    main()
