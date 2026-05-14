#!/usr/bin/env python3
"""Daily game industry news digest — fetch RSS and write markdown."""

import os
import re
import sys
from datetime import datetime, timezone

import feedparser

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "news")
MAX_ENTRIES = int(os.environ.get("MAX_ENTRIES", "5"))

RSS_FEEDS = [
    ("Game Developer",        "https://www.gamedeveloper.com/rss.xml"),
    ("PC Gamer",              "https://www.pcgamer.com/rss/"),
    ("Rock Paper Shotgun",    "https://www.rockpapershotgun.com/feed/"),
    ("Eurogamer",             "https://www.eurogamer.net/feed"),
    ("IndieGames",            "https://indiegames.com/feed/"),
    ("Engadget Gaming",       "https://www.engadget.com/rss/gaming/"),
    ("Reddit r/gamedev",      "https://www.reddit.com/r/gamedev/.rss"),
]


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

        entries.append({"title": title, "link": link, "summary": summary})
        if len(entries) >= MAX_ENTRIES:
            break
    return entries


def build_markdown(entries_by_feed: list[tuple[str, list[dict]]], date_str: str) -> str:
    lines = [f"# Game Industry Daily — {date_str}", ""]
    for feed_name, entries in entries_by_feed:
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
