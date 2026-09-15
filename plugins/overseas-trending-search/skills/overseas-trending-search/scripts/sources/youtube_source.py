#!/usr/bin/env python3
"""
YouTube platform adapter
Endpoints verified (2026-07):
  searchVideo   POST {"searchQuery": "..."}
      → data.videos[] (20/call): title / videoId / author / channelId /
        viewCount (raw integer) / duration / publishedTime (relative, e.g. "1 day ago") / thumbnails[]
  videoDetail   POST {"videoId": "..."}
      → likeCount / commentCount (localized display strings, e.g. "1928万", "244万"),
        date (localized date string, e.g. "2026年7月24日"), videoUrl / channelHandle / description
  videoComments POST {"videoId": "..."}
      → data.comments[] + continuationToken (reserved for comment-analysis scenarios)
Note: searchVideo lacks like/comment counts, so videoDetail is called per candidate;
      to control credit consumption, only the top detail_top items by viewCount get
      detail enrichment — the rest fall back to 0.
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import YOUTUBE_SEARCH_API, YOUTUBE_DETAIL_API, build_source, SUCCESS_CODES
from .base import BaseSource, PlatformUnavailable


class YouTubeSource(BaseSource):
    platform = "youtube"
    display_name = "YouTube"
    #: Enrich the top N items by viewCount with detail (likes/comments only come from the detail API).
    #: searchVideo returns 20 items per call — 20 means full coverage; trending posts sort by likes,
    #: and skipping detail fetches would keep high-like videos from ranking up.
    detail_top = 20

    def search(self, session, keyword):
        result = self.post_json(session, YOUTUBE_SEARCH_API,
                                {"searchQuery": keyword, "source": build_source()})
        if result is None:
            raise PlatformUnavailable("YouTube search request failed (network error)")

        code = result.get("code")
        if code not in SUCCESS_CODES:
            msg = result.get("msg", "")
            if code == 3203:
                raise PlatformUnavailable(f"YouTube upstream capability failure: {msg}")
            raise PlatformUnavailable(f"YouTube search endpoint error (code {code}): {msg}")

        data = result.get("data") or {}
        videos = data.get("videos") if isinstance(data, dict) else None
        if not isinstance(videos, list):
            return []

        # Sort by views and only fetch detail for the top N (likes/comments come from the detail API)
        videos = [v for v in videos if isinstance(v, dict)]
        videos.sort(key=lambda v: self._to_int(v.get("viewCount")), reverse=True)
        details = {}
        for v in videos[:self.detail_top]:
            vid = str(v.get("videoId") or "")
            if not vid:
                continue
            detail = self._fetch_detail(session, vid)
            if detail:
                details[vid] = detail
            time.sleep(0.2)

        return [self._normalize_item(v, keyword, details.get(str(v.get("videoId") or "")))
                for v in videos]

    def _fetch_detail(self, session, video_id):
        result = self.post_json(session, YOUTUBE_DETAIL_API, {"videoId": video_id})
        if result and result.get("code") in SUCCESS_CODES:
            data = result.get("data")
            if isinstance(data, dict) and data:
                return data
        return None

    def _normalize_item(self, item, keyword, detail=None):
        detail = detail or {}
        vid = str(item.get("videoId") or "")
        cover = ""
        thumbs = item.get("thumbnails")
        if isinstance(thumbs, list) and thumbs:
            best = max(thumbs,
                       key=lambda t: int(t.get("width") or 0) * int(t.get("height") or 0))
            cover = best.get("url") or ""

        # Publish time: prefer the detail's exact date ("2026年7月24日"), fall back to the list's relative time ("1 day ago")
        publish_ts = (self._parse_cn_date(detail.get("date"))
                      or self._parse_ts(item.get("publishedTime")))

        return self.make_record(
            title=item.get("title") or detail.get("title") or "",
            url=detail.get("videoUrl") or (f"https://www.youtube.com/watch?v={vid}" if vid else ""),
            author=item.get("author") or detail.get("author") or "",
            likes=self._parse_display_count(detail.get("likeCount")),
            comments=self._parse_display_count(detail.get("commentCount")),
            views=self._to_int(item.get("viewCount")) or self._parse_display_count(detail.get("viewCount")),
            publish_ts=publish_ts,
            keyword=keyword,
            extra={
                "shares": 0,
                "work_id": vid,
                "cover": cover,
                "duration": item.get("duration") or "",
                "channel_id": item.get("channelId") or "",
                "channel_handle": detail.get("channelHandle") or "",
            },
        )

    # ─── Localized display-string parsing ────────────────────────────────────────────────
    @staticmethod
    def _parse_display_count(value):
        """
        Parse YouTube localized count strings → int.
        Handles: "1928万" / "1,797,749,387次观看" / "244万" / "1.9M" / "24K" / raw integers.
        (Chinese numerals appear because the upstream API returns zh-localized strings.)
        """
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip().replace(",", "").replace(" ", "")
        m = re.match(r"^([\d.]+)(.*)$", text)
        if not m:
            return 0
        try:
            num = float(m.group(1))
        except ValueError:
            return 0
        suffix = m.group(2).upper()
        if "亿" in suffix:
            mult = 100_000_000
        elif "万" in suffix:
            mult = 10_000
        elif "千" in suffix:
            mult = 1_000
        elif suffix.startswith("B"):
            mult = 1_000_000_000
        elif suffix.startswith("M"):
            mult = 1_000_000
        elif suffix.startswith("K"):
            mult = 1_000
        else:
            mult = 1
        return int(num * mult)

    @staticmethod
    def _parse_cn_date(value):
        """Parse the upstream's Chinese date string "2026年7月24日" → second-level timestamp"""
        if not value:
            return 0
        m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$", str(value).strip())
        if not m:
            return 0
        try:
            return int(datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).timestamp())
        except ValueError:
            return 0
