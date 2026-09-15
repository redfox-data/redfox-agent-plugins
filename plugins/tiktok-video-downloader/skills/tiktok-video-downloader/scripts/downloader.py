#!/usr/bin/env python3
"""
TikTok Video Downloader - API version
Parse TikTok video links via the redfox.hk API and return watermark-free direct download URLs.
Supports single and batch link parsing with automatic TikTok link validation.

Usage:
    python3 downloader.py <url> [--api-key <key>]
    python3 downloader.py <url1> <url2> <url3> [--api-key <key>]
"""

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path
from urllib.parse import urlparse

import requests

# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# Ensure UTF-8 output for emoji and CJK characters on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API_URL = "https://redfox.hk/story/api/parseWork/videoDownload/tiktok"
CONFIG_DIR = Path.home() / ".redfox" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"

ENV_KEY = "REDFOX_API_KEY"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ── Redfox channel attribution ──
# Appends the running AI client to the API `source` field for per-platform stats.
# Priority: REDFOX_CHANNEL env var (documented in SKILL.md) > client env markers > "github".
SOURCE_BASE = "TikTok视频下载"


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


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")


def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")


def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


class ApiKeyError(Exception):
    """Raised when API key is missing or invalid, should stop batch processing."""
    pass


def get_api_key(cli_key=None):
    """Get API key with priority: CLI arg > env var > config file."""
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


def save_api_key(api_key):
    """Persist API key to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": api_key}, indent=2))
    os.chmod(CONFIG_FILE, 0o600)  # secure file permissions
    info(f"API Key saved to {CONFIG_FILE}")


def is_tiktok_link(url):
    """Check if the URL is a TikTok video link (web link or short link).

    Supports:
      - https://www.tiktok.com/@user/video/xxxxx
      - https://vm.tiktok.com/xxxxx/
      - https://vt.tiktok.com/xxxxx/
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return host.endswith("tiktok.com")
    except Exception:
        return False


def normalize_url(url):
    """Normalize a URL: strip quotes and ensure it has a scheme."""
    url = url.strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def extract_download_url(data):
    """Extract video download URL from API response data (tolerant of field naming)."""
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return None

    # Common field names that may carry the downloadable video link
    candidate_keys = [
        "videoUrl", "video_url", "downloadUrl", "download_url",
        "videoDownloadUrl", "video_download_url", "playUrl", "play_url",
        "url", "link",
    ]
    for key in candidate_keys:
        value = data.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value

    # Nested structures: data.video.url / data.media[0].url etc.
    for nested_key in ("video", "media", "result", "detail"):
        nested = data.get(nested_key)
        found = extract_download_url(nested) if isinstance(nested, (dict, list)) else None
        if found:
            return found

    if isinstance(data.get("videos"), list):
        for item in data["videos"]:
            found = extract_download_url(item)
            if found:
                return found

    return None


def get_audio_url(res):
    """Extract audio URL from a resource dict (tolerant of field naming)."""
    if not isinstance(res, dict):
        return None
    for key in ("audioUrl", "audio_url", "audioDownloadUrl", "audio_download_url",
                "musicUrl", "music_url", "soundUrl", "sound_url"):
        value = res.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def process_single_video(url, api_key, json_mode=False):
    """Process a single TikTok video URL: validate, call API, print results.

    Returns True on success, False on failure.
    Raises ApiKeyError if the API key is missing/invalid (fatal for batch mode).
    Terminates the process (sys.exit) if the URL is not a TikTok link.
    """
    # ── Validate TikTok link ──
    if not is_tiktok_link(url):
        error(f"Not a TikTok video link — please provide a valid TikTok video link: {url}")
        print(f"  Valid link format examples:")
        print(f"  https://www.tiktok.com/@user/video/xxxxx")
        print(f"  https://vm.tiktok.com/xxxxx/")
        sys.exit(1)

    step(f"URL: {url}")

    # ── Call API ──
    step("Calling redfox.hk API...")

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    try:
        resp = session.post(API_URL, json={"url": url, "source": build_source()}, timeout=30)
        result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"API request failed: {e}")
        return False
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        return False

    code = result.get("code")
    msg = result.get("msg", "")

    # Success codes start with 2 (e.g. 200, 2000); anything else is an error
    if not str(code).startswith("2"):
        if code == 3106:
            error("Missing API Key")
            raise ApiKeyError()
        elif code == 3107:
            error("API Key is invalid or expired, please check it")
            print("  Configure: export REDFOX_API_KEY=ark_your_key")
            raise ApiKeyError()
        elif code == 400:
            error(f"Invalid request parameters: {msg}")
        else:
            error(f"API error (code {code}): {msg}")
        return False

    data = result.get("data")
    if not data:
        error("API returned empty data")
        return False

    # ── Parse result ──
    if json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))

    desc = data.get("desc") if isinstance(data, dict) else None
    cover = data.get("cover") if isinstance(data, dict) else None
    resources = data.get("resources") if isinstance(data, dict) else None

    print(f"\n{GREEN}{BOLD}✓ Parsed successfully!{RESET}")

    # Content description (full original text, never truncated)
    if desc:
        print(f"\n{CYAN}{BOLD}📝 Description:{RESET}")
        for line in str(desc).splitlines():
            print(f"  {line}")

    # Resource list: type / duration / download URL / cover / audio URL
    if isinstance(resources, list) and resources:
        print(f"\n{CYAN}{BOLD}🎬 Resources ({len(resources)} total):{RESET}")
        for i, res in enumerate(resources, 1):
            if not isinstance(res, dict):
                continue
            rtype = res.get("type") or "unknown"
            dl = res.get("downloadUrl") or "-"
            cu = res.get("coverUrl") or cover or "-"
            dur = res.get("durationSeconds")
            dur_str = f"{dur}s" if isinstance(dur, (int, float)) and dur else "unknown"
            audio = get_audio_url(res)
            print(f"\n  {BOLD}[Resource {i}]{RESET}")
            print(f"    Type: {rtype}")
            print(f"    Duration: {dur_str}")
            print(f"    Download URL: {dl}")
            print(f"    Cover: {cu}")
            if audio:
                print(f"    Audio URL: {audio}")
    else:
        # Fallback: extract from top-level fields when there is no resources array
        download_url = extract_download_url(data)
        if not download_url:
            error("Could not extract a download URL from the API response. Raw response:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return False
        print(f"\n{CYAN}{BOLD}🎬 Resource:{RESET}")
        print(f"    Download URL: {download_url}")
        if cover:
            print(f"    Cover: {cover}")
        audio = get_audio_url(data) if isinstance(data, dict) else None
        if audio:
            print(f"    Audio URL: {audio}")

    print(f"\n{CYAN}Copy the link into a browser or download manager to save the file.{RESET}")
    print(f"\n{YELLOW}⚠️ Download links expire in about 5 minutes — copy and open/download right away!{RESET}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="TikTok Video Downloader - parse videos via the redfox.hk API and return direct download links, batch supported",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single link
  python3 downloader.py https://www.tiktok.com/@user/video/xxxxx
  python3 downloader.py https://www.tiktok.com/@user/video/xxxxx --api-key ark_xxxxx

  # Batch links (space separated)
  python3 downloader.py https://www.tiktok.com/@user/video/111 https://www.tiktok.com/@user/video/222

You can also provide the key via the REDFOX_API_KEY environment variable:
  export REDFOX_API_KEY=ark_xxxxx
  python3 downloader.py <url> [<url> ...]
        """,
    )
    parser.add_argument("urls", nargs="+", help="TikTok video link(s), e.g. https://www.tiktok.com/@user/video/xxxxx (multiple allowed, space separated)")
    parser.add_argument("--api-key", help="API key (format ark_xxx; falls back to env var or config file)")
    parser.add_argument(
        "--save-key",
        action="store_true",
        help="Save the provided API key to the config file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full API response as JSON",
    )

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║   TikTok Video Downloader            ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── API Key ──
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        error("API Key not found. Set the REDFOX_API_KEY environment variable or pass --api-key")
        print(f"  Get a key: https://redfox.hk/settings/api-keys?source=github")
        sys.exit(1)

    # Save key if requested
    if args.save_key:
        save_api_key(api_key)

    # ── Process URLs ──
    total = len(args.urls)
    if total > 1:
        print(f"{CYAN}{BOLD}📋 Batch mode: {total} links{RESET}\n")

    success_count = 0
    fail_count = 0

    for idx, raw_url in enumerate(args.urls, 1):
        if total > 1:
            print(f"\n{CYAN}{BOLD}{'='*50}{RESET}")
            print(f"{CYAN}{BOLD}📋 Link {idx}/{total}{RESET}")
            print(f"{CYAN}{BOLD}{'='*50}{RESET}")

        url = normalize_url(raw_url)

        try:
            ok = process_single_video(url, api_key, json_mode=args.json)
        except ApiKeyError:
            # Invalid API key — remaining links would fail too, exit now
            if fail_count > 0 or success_count > 0:
                print(f"\n{RED}API Key invalid, batch parsing aborted.{RESET}")
            sys.exit(1)

        if ok:
            success_count += 1
        else:
            fail_count += 1

    # ── Summary ──
    if total > 1:
        print(f"\n{CYAN}{BOLD}{'='*50}{RESET}")
        print(f"{CYAN}{BOLD}📋 Batch parsing complete{RESET}")
        print(f"  {GREEN}✓ Success: {success_count}{RESET}")
        print(f"  {RED}✗ Failed: {fail_count}{RESET}")

    print(f"\n{CYAN}Copy the link into a browser or download manager to save the file.{RESET}")
    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
