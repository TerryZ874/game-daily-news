#!/usr/bin/env python3
"""Daily game industry news digest — fetch RSS and write markdown."""

import os
import re
import sys
from datetime import datetime, timezone

import feedparser

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "news")
MAX_ENTRIES = int(os.environ.get("MAX_ENTRIES", "5"))

# Keywords to watch for and pin at the top
WATCH_KEYWORDS = ["恋与深空", "Love and Deepspace", "love and deepspace"]

RSS_FEEDS = [
    # English game dev / industry
    ("Game Developer",        "https://www.gamedeveloper.com/rss.xml"),
    ("PC Gamer",              "https://www.pcgamer.com/rss/"),
    ("Rock Paper Shotgun",    "https://www.rockpapershotgun.com/feed/"),
    ("Eurogamer",             "https://www.eurogamer.net/feed"),
    ("IndieGames",            "https://indiegames.com/feed/"),
    ("Engadget Gaming",       "https://www.engadget.com/rss/gaming/"),
    ("Reddit r/gamedev",      "https://www.reddit.com/r/gamedev/.rss"),
    # Chinese game portal
    ("机核",                  "https://www.gcores.com/rss"),
    # Keyword search (works from GitHub US runners)
    ("恋与深空 动态",         "https://news.google.com/rss/search?q=%E6%81%8B%E4%B8%8E%E6%B7%B1%E7%A9%BA+%E6%B8%B8%E6%88%8F&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
]


def _match_watch(text: str) -> bool:
    """Check if text contains any watched keyword."""
    if not text:
        return False
    lower = text.lower()
    return any(kw.lower() in lower for kw in WATCH_KEYWORDS)


def fetch_entries(feed_name: str, url: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"  [!] Failed: {feed_name} - {e}", file=sys.stderr)
        return []

    entries = []
    for entry in feed.entries:
        link = entry.get("link", "")
        title = (entry.get("title") or "Untitled").strip()

        raw = ""
        for field in ("summary", "description", "content"):
            val = entry.get(field)
            if val is None:
                continue
            if isinstance(val, list):
                raw = val[0].get("value", "") if isinstance(val[0], dict) else str(val[0])
            else:
                raw = str(val)
            break
        summary = re.sub(r"<[^>]+>", " ", raw)
        summary = re.sub(r"\s+", " ", summary).strip()[:250]

        entries.append({"title": title, "link": link, "summary": summary, "source": feed_name})
        if len(entries) >= MAX_ENTRIES:
            break
    return entries


def build_markdown(all_entries: list[tuple[str, list[dict]]], date_str: str) -> str:
    """Build markdown, with watched keywords pinned at top."""
    lines = [f"# Game Industry Daily — {date_str}", ""]

    # Collect all entries and split into watched vs regular
    watched: list[dict] = []
    regular: list[tuple[str, list[dict]]] = []

    for feed_name, entries in all_entries:
        watched_from_feed = [e for e in entries if _match_watch(e["title"]) or _match_watch(e["summary"])]
        other_entries = [e for e in entries if e not in watched_from_feed]

        if watched_from_feed:
            watched.extend(watched_from_feed)
        if other_entries:
            regular.append((feed_name, other_entries))

    # Watched / pinned section
    if watched:
        lines.append("## 🔥 恋与深空")
        lines.append("")
        for e in watched:
            tag = f" [{e['source']}]" if e.get("source") else ""
            lines.append(f"### [{e['title']}]({e['link']}){tag}")
            if e["summary"]:
                lines.append("")
                lines.append(e["summary"])
            lines.append("")

    # Regular feeds
    for feed_name, entries in regular:
        if not entries:
            continue
        lines.append(f"## {feed_name}")
        lines.append("")
        for e in entries:
            lines.append(f"### [{e['title']}]({e['link']})")
            if e["summary"]:
                lines.append("")
                lines.append(e["summary"])
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    date_obj = datetime.now(timezone.utc)
    date_str = date_obj.strftime("%A, %B %d, %Y")
    file_date = date_obj.strftime("%Y-%m-%d")

    print(f"Game Industry Daily — {date_str}")
    print("-" * 40)

    all_entries: list[tuple[str, list[dict]]] = []
    for name, url in RSS_FEEDS:
        print(f"Fetching {name} ...")
        entries = fetch_entries(name, url)
        print(f"  -> {len(entries)} entries")
        if entries:
            all_entries.append((name, entries))

    if not all_entries:
        print("ERROR: no entries fetched", file=sys.stderr)
        sys.exit(1)

    md = build_markdown(all_entries, date_str)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{file_date}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nWritten to {filepath}")


if __name__ == "__main__":
    main()
