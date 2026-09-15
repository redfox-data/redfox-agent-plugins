#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf-image-text-extractor/scripts/record.py

PDF & Image Text Extractor — usage permission request script
Purpose: must be called before every use of this skill to request usage
permission from the server and complete the auth check.

Permission endpoint: https://redfox.hk/story/api/skill/record/save
Auth: reads the REDFOX_API_KEY environment variable, sent via the X-API-Key header
Failure policy: exits non-zero when no API key is present or the request fails;
the caller is responsible for informing the user.

Usage:
  python3 scripts/record.py
"""

import sys
import os

try:
    import requests
except ImportError:
    print("❌ Missing dependency: requests. Run: pip install requests")
    sys.exit(1)

RECORD_URL = "https://redfox.hk/story/api/skill/record/save"
SKILL_NAME = "PDF和图片文字提取"
REGISTER_URL = "https://redfox.hk/settings/api-keys?source=github"

# ── Redfox channel attribution ──
# Appends the running AI client to the API `source` field for per-platform stats.
# Priority: REDFOX_CHANNEL env var (documented in SKILL.md) > client env markers > "github".
SOURCE_BASE = "PDF和图片文字提取"


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


def _get_api_key() -> str:
    """Read the API key from the REDFOX_API_KEY environment variable; exit if missing."""
    key = os.getenv("REDFOX_API_KEY", "").strip()
    if not key:
        print("❌ REDFOX_API_KEY is not configured — this skill cannot run without it")
        print(f"Sign up for free at {REGISTER_URL} to get an API key (no credits deducted)")
        print("Then configure it in either way:")
        print('  Option 1 (env var): export REDFOX_API_KEY="ak_xxxx..."')
        print('  Option 2 (config file): add to ~/.openclaw/openclaw.json')
        print('    { "env": { "REDFOX_API_KEY": "ak_xxxx..." } }')
        sys.exit(1)
    return key


def save_record() -> None:
    """Call the permission endpoint to request usage rights. Exits non-zero on failure."""
    api_key = _get_api_key()
    payload = {"skillName": SKILL_NAME, "source": build_source()}
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-API-Key": api_key,
    }

    try:
        resp = requests.post(RECORD_URL, json=payload, headers=headers, verify=True, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach the auth server: {e}")
        print(f"Check your network and retry, or visit {REGISTER_URL} to confirm the API key is valid")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"❌ Auth endpoint returned HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()
    code = data.get("code")

    if code in (200, 2000):
        print("✅ Auth passed — usage permission granted")
        return

    if code in (3106, 3107):
        print("❌ API key is invalid or expired")
        print(f"Get a new free API key at {REGISTER_URL}")
        print('Then run: export REDFOX_API_KEY="ak_xxxx..."')
        sys.exit(1)

    print(f"❌ Unexpected auth response: {data}")
    sys.exit(1)


if __name__ == "__main__":
    save_record()
