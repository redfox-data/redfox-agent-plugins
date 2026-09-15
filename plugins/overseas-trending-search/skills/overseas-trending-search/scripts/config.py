#!/usr/bin/env python3
"""
overseas-trending-search — shared configuration & key loading
Key loading priority: --api-key argument > REDFOX_API_KEY env var > ~/.redfox/apis/redfox.json
"""

import json
import os
from pathlib import Path

# ─── RedFox gateway ──────────────────────────────────────────────────────────────────
BASE_URL = "https://redfox.hk/story/api"

X_SEARCH_API = f"{BASE_URL}/x/search"
X_DETAIL_API = f"{BASE_URL}/x/tweetDetail"
X_COMMENTS_API = f"{BASE_URL}/x/tweetComments"

TIKTOK_SEARCH_API = f"{BASE_URL}/tiktok/ability/searchVideo"
TIKTOK_DETAIL_API = f"{BASE_URL}/tiktok/ability/awemeDetail"
TIKTOK_USER_AWEME_API = f"{BASE_URL}/tiktok/ability/userAwemeList"

# YouTube endpoints (verified 2026-07): searchVideo list + videoDetail for likes/comments
YOUTUBE_SEARCH_API = f"{BASE_URL}/youtube/searchVideo"
YOUTUBE_DETAIL_API = f"{BASE_URL}/youtube/videoDetail"
YOUTUBE_COMMENTS_API = f"{BASE_URL}/youtube/videoComments"

# ─── Key & channel ────────────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".redfox" / "apis" / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"

# ── Redfox channel attribution ──
# Appends the running AI client to the API `source` field for per-platform stats.
# Priority: REDFOX_CHANNEL env var (documented in SKILL.md) > client env markers > "github".
SOURCE_BASE = "ChinaTrendingDigest"


def detect_channel():
    """Best-effort detection of the AI client that is running this skill."""
    ch = os.environ.get("REDFOX_CHANNEL", "").strip().lower()
    if ch:
        return ch
    markers = (
        ("claude", ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_PLUGIN_ROOT")),
        ("cursor", ("CURSOR_TRACE_ID", "CURSOR_AGENT", "CURSOR_PLUGIN_ROOT")),
        ("codex", ("CODEX_SANDBOX", "CODEX_PLUGIN_ROOT", "CODEX_HOME")),
        ("gemini", ("GEMINI_CLI", "GEMINI_PLUGIN_ROOT")),
    )
    for name, keys in markers:
        if any(os.environ.get(k) for k in keys):
            return name
    return "github"


def build_source():
    canonical = {"claude": "Claude", "codex": "Codex", "cursor": "Cursor", "gemini": "Gemini", "github": "GitHub"}
    ch = detect_channel()
    return f"{SOURCE_BASE}-{canonical.get(ch, ch.capitalize())}"


DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "RedfoxOverseasTrending"
SUCCESS_CODES = (200, 2000)


def get_api_key(cli_key=None):
    """Load the RedFox API key by priority; returns None if not found"""
    if cli_key:
        return cli_key
    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            key = data.get("api_key")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass
    return None


def make_session(api_key):
    """Build a requests.Session with auth headers (RedFox gateway uses X-API-KEY)"""
    import requests
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })
    return session


def print_no_key_guide():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  No API key configured. Set it in one of these ways: ║")
    print("║                                                      ║")
    print("║  export REDFOX_API_KEY=ak_your_key                   ║")
    print("║  python3 digest.py --api-key ak_your_key             ║")
    print("║  echo '{\"api_key\":\"ak_your_key\"}' > ~/.redfox/apis/redfox.json ║")
    print("║                                                      ║")
    print("║  Sign up for a key: https://redfox.hk/settings/api-keys ║")
    print("╚══════════════════════════════════════════════════════╝")
