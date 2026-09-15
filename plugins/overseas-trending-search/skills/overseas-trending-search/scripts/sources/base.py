#!/usr/bin/env python3
"""
Abstract base class for platform adapters — every platform implements the same
interface so the main flow stays platform-agnostic.
Adding a platform (e.g. YouTube) only requires subclassing BaseSource and
implementing search() — zero changes to the main flow.
"""

import re
import time
from datetime import datetime, timedelta


class PlatformUnavailable(Exception):
    """Upstream platform capability unavailable (e.g. RedFox 3203 failure) — the main flow should degrade gracefully and skip"""
    pass


class BaseSource:
    """Platform adapter base class"""

    #: platform identifier (x / tiktok / youtube)
    platform = ""
    #: platform display name
    display_name = ""

    def search(self, session, keyword):
        """
        Search by keyword and return a list of normalized records (make_record output).
        Raise PlatformUnavailable on upstream failure so the main flow can degrade.
        """
        raise NotImplementedError

    # ─── Normalization ─────────────────────────────────────────────────────────────────
    def make_record(self, title, url, author, likes, comments, views,
                    publish_ts, keyword, extra=None):
        """Build the unified record schema — the main flow only knows this structure"""
        record = {
            "platform": self.platform,
            "platform_name": self.display_name,
            "title": (title or "").strip() or "(untitled)",
            "url": url or "",
            "author": author or "(unknown author)",
            "likes": self._to_int(likes),
            "comments": self._to_int(comments),
            "views": self._to_int(views),
            "publish_ts": publish_ts or 0,
            "publish_time": self._fmt_ts(publish_ts),
            "keyword": keyword or "",
        }
        if extra:
            record.update(extra)
        return record

    # ─── Utilities ───────────────────────────────────────────────────────────────────
    @staticmethod
    def _to_int(v):
        try:
            return int(v or 0)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _fmt_ts(ts):
        try:
            ts = int(ts)
            if ts > 10**12:  # millisecond timestamp compatibility
                ts = ts // 1000
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OSError):
            return ""

    @staticmethod
    def _parse_ts(value):
        """Accepts second/millisecond timestamps, ISO time strings and relative times
        (e.g. "1 day ago"); returns seconds as int"""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            ts = int(value)
            return ts // 1000 if ts > 10**12 else ts
        s = str(value).strip()
        if s.isdigit():
            ts = int(s)
            return ts // 1000 if ts > 10**12 else ts
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%a %b %d %H:%M:%S %z %Y"):
            try:
                return int(datetime.strptime(s.replace("Z", "+0000"), fmt).timestamp())
            except (ValueError, TypeError):
                continue
        return BaseSource._parse_relative_ts(s)

    #: relative-time unit → seconds (month/year are approximations, good enough for digests)
    _REL_UNITS = {
        "second": 1, "minute": 60, "hour": 3600, "day": 86400,
        "week": 604800, "month": 2592000, "year": 31536000,
    }
    #: Chinese relative-time units — parsing logic, upstream APIs may return them
    _REL_UNITS_ZH = {
        "秒": 1, "分钟": 60, "小时": 3600, "天": 86400,
        "周": 604800, "个月": 2592000, "月": 2592000, "年": 31536000,
    }

    @staticmethod
    def _parse_relative_ts(s):
        """Parse relative times: "3 hours ago" / "Streamed 1 day ago" / "2 天前" etc."""
        m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago", s, re.I)
        if m:
            secs = int(m.group(1)) * BaseSource._REL_UNITS[m.group(2).lower()]
            return int((datetime.now() - timedelta(seconds=secs)).timestamp())
        m = re.search(r"(\d+)\s*(个月|分钟|小时|秒|天|周|月|年)前", s)
        if m:
            secs = int(m.group(1)) * BaseSource._REL_UNITS_ZH[m.group(2)]
            return int((datetime.now() - timedelta(seconds=secs)).timestamp())
        return 0

    # ─── Robust requests (retry with incremental backoff) ─────────────────────────────
    def post_json(self, session, url, payload, max_retries=3, timeout=30):
        """
        POST JSON with incremental-backoff retries on failure (network error / non-JSON).
        Returns the parsed dict; None if all attempts fail.
        """
        for attempt in range(max_retries):
            try:
                resp = session.post(url, json=payload, timeout=timeout)
                return resp.json()
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
        return None
