#!/usr/bin/env python3
"""Daily game industry news digest — RSS fetcher + email sender."""

import os
import re
import smtplib
import sys
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

import feedparser

# ── Config ──────────────────────────────────────────────────────────────────
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.sina.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "solidgouki@sina.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_TO = os.environ.get("MAIL_TO", "solidgouki@sina.com")
MAIL_FROM = os.environ.get("MAIL_FROM", "solidgouki@sina.com")
MAX_ENTRIES = int(os.environ.get("MAX_ENTRIES", "5"))

# ── RSS sources ─────────────────────────────────────────────────────────────
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
    """Fetch a single RSS feed, return up to MAX_ENTRIES clean entries."""
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"  [!] Failed to fetch {feed_name}: {e}", file=sys.stderr)
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
        summary = re.sub(r"<[^>]+>", " ", raw)  # strip HTML
        summary = re.sub(r"\s+", " ", summary).strip()[:250]

        entries.append({"title": title, "link": link, "summary": summary})
        if len(entries) >= MAX_ENTRIES:
            break
    return entries


def build_plain_text(entries_by_feed: list[tuple[str, list[dict]]], date_str: str) -> str:
    """Build a plain-text version of the email."""
    lines = [f"Game Industry Daily - {date_str}", "=" * 40, ""]
    for feed_name, entries in entries_by_feed:
        if not entries:
            continue
        lines.append(f"[{feed_name}]")
        lines.append("-" * len(feed_name) + "----")
        for e in entries:
            lines.append(f"* {e['title']}")
            lines.append(f"  {e['link']}")
            if e['summary']:
                lines.append(f"  {e['summary']}")
            lines.append("")
        lines.append("")
    lines.append("---")
    lines.append("Generated automatically from RSS feeds.")
    return "\n".join(lines)


def build_html(entries_by_feed: list[tuple[str, list[dict]]], date_str: str) -> str:
    """Build the HTML email body."""
    parts = [
        "<!DOCTYPE html>",
        '<html><head><meta charset="utf-8"></head>',
        '<body style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;'
        'max-width:680px;margin:0 auto;padding:20px;background:#f5f5f5;">',
        '<div style="background:#1a1a2e;color:#fff;padding:24px 30px;border-radius:8px 8px 0 0;">',
        f"<h1 style='margin:0;font-size:22px;'>Game Industry Daily</h1>",
        f"<p style='margin:6px 0 0;opacity:.8;font-size:13px;'>{date_str}</p></div>",
        '<div style="background:#fff;padding:20px 30px;border-radius:0 0 8px 8px;">',
    ]

    for feed_name, entries in entries_by_feed:
        if not entries:
            continue
        parts.append(
            f"<h2 style='color:#1a1a2e;border-bottom:2px solid #e94560;"
            f"padding-bottom:6px;margin-top:28px;'>{feed_name}</h2>"
        )
        for e in entries:
            parts.append(
                f"<div style='margin:14px 0;'>"
                f"<a href='{e['link']}' style='color:#1a1a2e;font-size:15px;"
                f"font-weight:600;text-decoration:none;'>{e['title']}</a>"
                f"<p style='color:#555;font-size:13px;margin:4px 0 0;line-height:1.5;'>{e['summary']}</p>"
                f"</div>"
            )

    parts.append(
        "<p style='color:#999;font-size:11px;margin-top:30px;"
        "border-top:1px solid #eee;padding-top:12px;'>"
        "Generated automatically from RSS feeds.</p></div></body></html>"
    )
    return "\n".join(parts)


def send_email(html_text: str, plain_text: str, date_str: str) -> None:
    """Send the email via SMTP with delivery verification."""
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((SMTP_USER, MAIL_FROM))
    msg["To"] = MAIL_TO
    msg["Subject"] = f"Game Industry Daily - {date_str}"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = f"<{uuid.uuid4().hex}@game-daily-news>"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_text, "html", "utf-8"))

    print(f"  Connecting to {SMTP_SERVER}:{SMTP_PORT} ...")
    if SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
    else:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()

    server.login(SMTP_USER, SMTP_PASS)
    print("  Authenticated")

    result = server.sendmail(MAIL_FROM, [MAIL_TO], msg.as_string())
    server.quit()

    if result:
        print(f"  Warning - delivery issues: {result}", file=sys.stderr)
    else:
        print("  Email sent successfully")
        print(f"  Check inbox at {MAIL_TO}")


def main() -> None:
    if not SMTP_PASS:
        print("ERROR: SMTP_PASS not set", file=sys.stderr)
        sys.exit(1)

    date_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    print(f"Game Industry Daily - {date_str}")
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

    print()
    plain = build_plain_text(all_entries, date_str)
    html = build_html(all_entries, date_str)
    send_email(html, plain, date_str)


if __name__ == "__main__":
    main()
