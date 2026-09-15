#!/usr/bin/env python3
"""
Overseas Cross-Platform Trending Search — main orchestrator
==============================
Searches X / TikTok / YouTube trending content for user-provided keywords
(any language, comma-separated for multiple), takes Top N per platform,
normalizes into a unified list (platform/title/author/views/likes/comments/date/link),
and outputs a grouped terminal table + CSV + interactive HTML report.

Usage:
    python3 digest.py "AI"
    python3 digest.py "artificial intelligence,AI agent" --days 3
    python3 digest.py "AI" --platforms tiktok --sort time
    python3 digest.py "AI" --sort views --top 5
    python3 digest.py "AI" --csv-only --no-open
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (DEFAULT_OUTPUT_DIR, get_api_key, make_session,
                    print_no_key_guide)
from sources import SOURCES
from sources.base import PlatformUnavailable

# ─── Terminal colors ──────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")

def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")

def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")

def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


def format_number(n):
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


# ─── Language detection & priority tiering ──────────────────────────────────────────
def detect_lang(text):
    """Lightweight language detection (no third-party deps):
    zh=has Han chars without kana (simplified/traditional Chinese), ja=has kana,
    ko=has Hangul, en=has Latin letters, other=everything else.
    Mixed text (e.g. "中文标题 with English") counts as zh."""
    has_han = has_kana = has_hangul = has_latin = False
    for ch in text or "":
        o = ord(ch)
        if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
            has_han = True
        elif 0x3040 <= o <= 0x30FF:
            has_kana = True
        elif 0xAC00 <= o <= 0xD7AF:
            has_hangul = True
        elif o < 0x80 and ch.isalpha():
            has_latin = True
    if has_han:
        return "ja" if has_kana else "zh"
    if has_kana:
        return "ja"
    if has_hangul:
        return "ko"
    if has_latin:
        return "en"
    return "other"


def keyword_pref_lang(keywords):
    """Infer the preferred language from keywords: Han chars→zh, pure Latin→en,
    Japanese/Korean likewise; unrecognizable→None (no tiering)."""
    lang = detect_lang(" ".join(keywords))
    return lang if lang in ("zh", "en", "ja", "ko") else None


def lang_tier(lang, pref):
    """Language tiers: 0=same language as keywords, 1=Chinese/English, 2=other languages.
    No tiering when pref is None."""
    if not pref or lang == pref:
        return 0
    if lang in ("zh", "en"):
        return 1
    return 2


# ─── Collection flow ────────────────────────────────────────────────────────────────────
def collect(session, keywords, platforms):
    """
    Platform × keyword collection loop.
    Returns (records, platform_status) — platform_status: {platform: "ok"/error message}
    """
    records = []
    seen = set()
    platform_status = {}

    for pf in platforms:
        source_cls = SOURCES.get(pf)
        if not source_cls:
            warn(f"Unknown platform \"{pf}\", skipped (options: {', '.join(SOURCES)})")
            continue
        source = source_cls()
        pf_ok = False

        for kw in keywords:
            step(f"[{source.display_name}] Searching \"{kw}\"...")
            try:
                items = source.search(session, kw)
            except PlatformUnavailable as e:
                warn(f"[{source.display_name}] unavailable, skipped: {e}")
                platform_status[pf] = str(e)
                break
            except Exception as e:
                warn(f"[{source.display_name}] search error for keyword \"{kw}\": {e}")
                continue

            added = 0
            for r in items:
                dedup_key = r.get("url") or f"{pf}:{r.get('work_id')}"
                if dedup_key and dedup_key not in seen:
                    seen.add(dedup_key)
                    r["lang"] = detect_lang(r.get("title") or "")
                    records.append(r)
                    added += 1
            step(f"  +{added} items (total {len(records)})")
            pf_ok = True
            time.sleep(0.3)

        if pf_ok:
            platform_status[pf] = "ok"

    return records, platform_status


def filter_by_days(records, days):
    """Filter by time window (records with missing publish_ts or outside the window are
    dropped, with per-platform statistics reported)"""
    if days <= 0:
        return records
    cutoff = (datetime.now() - timedelta(days=days)).timestamp()
    kept, dropped = [], []
    for r in records:
        ts = int(r.get("publish_ts") or 0)
        if ts and ts >= cutoff:
            kept.append(r)
        else:
            dropped.append(r)
    if dropped:
        drop_cnt, keep_cnt = {}, {}
        for r in dropped:
            pf = r.get("platform") or "?"
            drop_cnt[pf] = drop_cnt.get(pf, 0) + 1
        for r in kept:
            pf = r.get("platform") or "?"
            keep_cnt[pf] = keep_cnt.get(pf, 0) + 1

        def _name(pf):
            return SOURCES[pf].display_name if pf in SOURCES else pf

        detail = ", ".join(f"{_name(pf)} {n} items" for pf, n in drop_cnt.items())
        warn(f"{len(dropped)} items had a missing publish time or fell outside the last {days} day(s), excluded ({detail})")
        for pf, n in drop_cnt.items():
            if not keep_cnt.get(pf):
                warn(f"All {n} {_name(pf)} items are older trending content outside the window — add --days 0 to include them")
    return kept


SORT_LABELS = {"likes": "likes", "views": "views",
               "comments": "comments", "time": "publish time"}


def _sort_key(r, sort_by):
    """Sort key: primary metric descending, with views/publish time as tie-breakers.
    When a platform's primary metric is all zeros (e.g. YouTube without likes),
    automatically falls back to sorting by views."""
    views = int(r.get("views") or 0)
    likes = int(r.get("likes") or 0)
    comments = int(r.get("comments") or 0)
    ts = int(r.get("publish_ts") or 0)
    if sort_by == "time":
        return (ts, views, likes)
    if sort_by == "views":
        return (views, likes, ts)
    if sort_by == "comments":
        return (comments, views, likes, ts)
    return (likes, views, ts)  # likes


def sort_records(records, sort_by, pref_lang=None):
    """Sort by metric descending first, then stable-sort by language tier:
    keyword language > Chinese/English > other languages."""
    records.sort(key=lambda r: _sort_key(r, sort_by), reverse=True)
    if pref_lang:
        records.sort(key=lambda r: lang_tier(r.get("lang"), pref_lang))
    return records


def limit_per_platform(records, top, sort_by, pref_lang=None):
    """Group by platform → sort within group (language tier + metric desc) →
    take top N per group (0=unlimited) → merge in platform order"""
    groups, order = {}, []
    for r in records:
        pf = r.get("platform") or "?"
        if pf not in groups:
            groups[pf] = []
            order.append(pf)
        groups[pf].append(r)
    merged = []
    for pf in order:
        g = sort_records(groups[pf], sort_by, pref_lang)
        merged.extend(g if top <= 0 else g[:top])
    return merged


# ─── Terminal table ──────────────────────────────────────────────────────────────────────
def print_terminal_table(records, keywords, platform_status, sort_by, top, pref_lang=None):
    kw_label = " + ".join(keywords)
    sort_label = SORT_LABELS.get(sort_by, sort_by)
    top_label = f"Top {top} per platform" if top > 0 else "unlimited"
    lang_label = {"zh": "Chinese first", "en": "English first"}.get(pref_lang)
    lang_suffix = f" · {lang_label}" if lang_label else ""

    print(f"\n{BOLD}{'=' * 128}{RESET}")
    print(f"{BOLD}  Overseas Trending Search · \"{kw_label}\" · {len(records)} items · {top_label} · sorted by {sort_label} desc{lang_suffix}{RESET}")
    print(f"{BOLD}{'=' * 128}{RESET}")

    status_parts = []
    for pf, st in platform_status.items():
        name = SOURCES[pf].display_name if pf in SOURCES else pf
        status_parts.append(f"{name}: {'✓' if st == 'ok' else '✗ ' + st}")
    if status_parts:
        print(f"  {CYAN}Platform status: {' | '.join(status_parts)}{RESET}")

    if not records:
        print(f"  {YELLOW}No results. Try widening the time window (--days 0 = unlimited) or different keywords{RESET}\n")
        return

    # Group by platform for display (records are already grouped and sorted)
    groups, order = {}, []
    for r in records:
        pf = r.get("platform") or "?"
        if pf not in groups:
            groups[pf] = []
            order.append(pf)
        groups[pf].append(r)

    header = (f"  {'#':<4}{'Platform':<8}{'Title':<24}{'Author':<14}"
              f"{'Views':>7}{'Likes':>7}{'Comments':>7}  {'Published':<18}{'Link':<30}")
    idx = 0
    for pf in order:
        g = groups[pf]
        name = g[0].get("platform_name") or pf
        print(f"\n  {CYAN}{BOLD}▎{name} ({len(g)} items · by {sort_label}){RESET}")
        print(f"  {YELLOW}{'─' * 110}{RESET}")
        print(f"  {YELLOW}{header}{RESET}")
        print(f"  {YELLOW}{'─' * 110}{RESET}")
        for r in g:
            idx += 1
            pf_name = (r.get("platform_name") or r.get("platform") or "")[:6]
            title = r.get("title", "")
            title = (title[:20] + "…") if len(title) > 20 else title
            author = r.get("author", "")
            author = (author[:11] + "..") if len(author) > 13 else author
            views = format_number(r.get("views"))
            likes = format_number(r.get("likes")) if int(r.get("likes") or 0) else "-"
            comments = format_number(r.get("comments")) if int(r.get("comments") or 0) else "-"
            pub = (r.get("publish_time") or "")[:16]
            url = r.get("url", "")
            url = (url[:27] + "..") if len(url) > 29 else url
            print(f"  {idx:<4}{pf_name:<8}{title:<24}{author:<14}"
                  f"{views:>7}{likes:>7}{comments:>7}  {pub:<18}{url:<30}")
        print(f"  {YELLOW}{'─' * 110}{RESET}")
    print()


# ─── CSV export ──────────────────────────────────────────────────────────────────────
def export_csv(records, keyword, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = output_dir / f"overseas_trending_{keyword}_{date_str}.csv"

    fieldnames = ["Platform", "Title", "Author", "Views", "Likes", "Comments",
                  "Shares", "Publish Time", "Link", "Matched Keyword"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Platform": r.get("platform_name", ""),
                "Title": r.get("title", ""),
                "Author": r.get("author", ""),
                "Views": r.get("views", 0),
                "Likes": r.get("likes", 0),
                "Comments": r.get("comments", 0),
                "Shares": r.get("shares", 0),
                "Publish Time": r.get("publish_time", ""),
                "Link": r.get("url", ""),
                "Matched Keyword": r.get("keyword", ""),
            })
    return filepath


# ─── HTML report ────────────────────────────────────────────────────────────────────
def generate_html(records, keyword, platform_status):
    template_path = Path(__file__).parent.parent / "assets" / "report_template.html"
    template = template_path.read_text(encoding="utf-8")

    status_label = " | ".join(
        f"{SOURCES[pf].display_name if pf in SOURCES else pf}: "
        f"{'OK' if st == 'ok' else st}"
        for pf, st in platform_status.items()
    )
    html = template
    html = html.replace("{{KEYWORD}}", keyword)
    html = html.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
    html = html.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    html = html.replace("{{TOTAL_COUNT}}", str(len(records)))
    html = html.replace("{{PLATFORM_STATUS}}", status_label)
    html = html.replace("{{INITIAL_DATA}}", json.dumps(records, ensure_ascii=False))
    return html


# ─── Main flow ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Overseas cross-platform trending search — X / TikTok / YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 digest.py "AI"
  python3 digest.py "artificial intelligence,AI agent" --days 3
  python3 digest.py "AI" --platforms tiktok --sort time
  python3 digest.py "AI" --sort views --top 5
  python3 digest.py "AI" --csv-only --no-open
        """,
    )
    parser.add_argument("keywords", nargs="?", default="",
                        help="Search keywords in any language, comma-separated for multiple")
    parser.add_argument("--days", type=int, default=1,
                        help="Time window: last N days (default 1, 0=unlimited)")
    parser.add_argument("--platforms", default="x,tiktok,youtube",
                        help="Comma-separated platform list (default x,tiktok,youtube)")
    parser.add_argument("--sort", default="views",
                        choices=["likes", "views", "comments", "time"],
                        help="Sort by: views (default) / likes / comments / time")
    parser.add_argument("--top", type=int, default=5,
                        help="Max items per platform (default 5, 0=unlimited)")
    parser.add_argument("--output-dir", help="Output directory (default ~/Downloads/RedfoxOverseasTrending)")
    parser.add_argument("--api-key", help="RedFox API Key")
    parser.add_argument("--csv-only", action="store_true", help="Generate CSV only")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the browser")

    args = parser.parse_args()

    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════════════╗
  ║        Overseas Trending Search              ║
  ║        X / TikTok / YouTube · daily digest   ║
  ╚══════════════════════════════════════════════╝{RESET}
"""
    print(banner)

    try:
        import requests  # noqa: F401
    except ImportError:
        error("Missing the requests library. Install with: pip3 install requests")
        sys.exit(1)

    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        print_no_key_guide()
        sys.exit(1)

    if not args.keywords:
        try:
            args.keywords = input(f"{CYAN}Enter keywords (comma-separated for multiple): {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        error("Keywords cannot be empty")
        sys.exit(1)

    platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    output_dir = os.path.expanduser(args.output_dir or str(DEFAULT_OUTPUT_DIR))

    session = make_session(api_key)

    # ── Collect ──
    records, platform_status = collect(session, keywords, platforms)

    # ── Language priority tiering (Chinese keywords→Chinese first, English→English first, others as fallback) ──
    pref_lang = keyword_pref_lang(keywords)

    # ── Time filter + Top N per platform ──
    records = filter_by_days(records, args.days)
    records = limit_per_platform(records, args.top, args.sort, pref_lang)

    # ── Terminal table ──
    print_terminal_table(records, keywords, platform_status, args.sort, args.top, pref_lang)

    if not records:
        sys.exit(0)

    # ── Statistics ──
    total_likes = sum(int(r.get("likes") or 0) for r in records)
    pf_counter = {}
    for r in records:
        pf_counter[r.get("platform_name", "?")] = pf_counter.get(r.get("platform_name", "?"), 0) + 1
    pf_dist = " | ".join(f"{k} {v}" for k, v in pf_counter.items())
    print(f"  {BOLD}Stats:{RESET} {len(records)} items | {pf_dist} | total likes {format_number(total_likes)}")

    # ── CSV ──
    main_kw = keywords[0]
    csv_path = export_csv(records, main_kw, output_dir)
    info(f"CSV saved: {csv_path}")

    # ── HTML ──
    if not args.csv_only:
        step("Generating HTML report ...")
        html_content = generate_html(records, " + ".join(keywords), platform_status)
        html_path = Path(output_dir) / f"overseas_trending_{main_kw}_{datetime.now().strftime('%Y-%m-%d')}.html"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding="utf-8")
        info(f"HTML report saved: {html_path}")

        if not args.no_open:
            step("Opening browser...")
            try:
                subprocess.run(["open", str(html_path)], check=True)
            except Exception:
                print(f"  Open manually: {html_path}")

    print(f"\n{GREEN}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║  ✓ Trending search complete!                     ║{RESET}")
    print(f"{GREEN}╚══════════════════════════════════════════════════╝{RESET}\n")


if __name__ == "__main__":
    main()
