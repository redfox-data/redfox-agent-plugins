#!/usr/bin/env python3
"""
TikTok platform adapter
Endpoints verified (2026-07):
  searchVideo  POST {"keyword": "..."}  → 20 items/call, each with likes/comments/views/publish time
  awemeDetail  POST {"awemeId": "..."}  → single-item detail (not needed for daily digests)
  userAwemeList POST {"secUserId": "..."} → author's video list (reserved)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TIKTOK_SEARCH_API, build_source, SUCCESS_CODES
from .base import BaseSource, PlatformUnavailable


class TikTokSource(BaseSource):
    platform = "tiktok"
    display_name = "TikTok"

    def search(self, session, keyword):
        result = self.post_json(session, TIKTOK_SEARCH_API,
                                {"keyword": keyword, "source": build_source()})
        if result is None:
            raise PlatformUnavailable("TikTok search request failed (network error)")

        code = result.get("code")
        if code not in SUCCESS_CODES:
            msg = result.get("msg", "")
            if code == 3203:
                raise PlatformUnavailable(f"TikTok upstream capability failure: {msg}")
            raise PlatformUnavailable(f"TikTok search endpoint error (code {code}): {msg}")

        data = result.get("data") or []
        if not isinstance(data, list):
            return []

        records = []
        for item in data:
            stats = item.get("statsData") or {}
            author = item.get("authorData") or {}
            record = self.make_record(
                title=item.get("content") or "",
                url=item.get("shareLink") or "",
                author=author.get("userName") or author.get("userHandle") or "",
                likes=stats.get("likeCount"),
                comments=stats.get("commentTotal"),
                views=stats.get("viewCount"),
                publish_ts=self._parse_ts(item.get("publishTime")),
                keyword=keyword,
                extra={
                    "shares": self._to_int(stats.get("shareTotal")),
                    "work_id": str(item.get("workId") or ""),
                    "area": item.get("area") or "",
                    "cover": (item.get("videoData") or {}).get("coverImage") or "",
                },
            )
            records.append(record)
        return records
