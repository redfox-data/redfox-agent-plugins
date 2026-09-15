#!/usr/bin/env python3
"""
YouTube Video Downloader - API version
Parse YouTube video links via the redfox.hk API and return watermark-free direct download URLs.

Usage:
    python3 downloader.py <url> [--api-key <key>]
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import requests

# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

API_URL = "https://redfox.hk/story/api/parseWork/videoDownload/youtube"
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
SOURCE_BASE = "youtube视频下载"


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


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Video Downloader - parse videos via the redfox.hk API and return direct download links",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 downloader.py https://www.youtube.com/watch?v=xxxxx
  python3 downloader.py https://youtu.be/xxxxx
  python3 downloader.py https://www.youtube.com/watch?v=xxxxx --api-key ark_xxxxx

You can also provide the key via the REDFOX_API_KEY environment variable:
  export REDFOX_API_KEY=ark_xxxxx
  python3 downloader.py <url>
        """,
    )
    parser.add_argument("url", help="YouTube video link, e.g. https://www.youtube.com/watch?v=xxxxx or https://youtu.be/xxxxx")
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
  ║   YouTube Video Downloader                ║
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

    # ── URL ──
    url = args.url.strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

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
        sys.exit(1)
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        sys.exit(1)

    code = result.get("code")
    msg = result.get("msg", "")

    # Success codes start with 2 (e.g. 200, 2000); anything else is an error
    if not str(code).startswith("2"):
        if code == 3106:
            error("Missing API Key")
        elif code == 3107:
            error("API Key is invalid or expired, please check it")
            print("  Configure: export REDFOX_API_KEY=ark_your_key")
        elif code == 400:
            error(f"Invalid request parameters: {msg}")
        else:
            error(f"API error (code {code}): {msg}")
        sys.exit(1)

    data = result.get("data")
    if not data:
        error("API returned empty data")
        sys.exit(1)

    # ── Parse result ──
    if args.json:
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

    # Resource list: type / duration / download URL / cover URL
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
            print(f"\n  {BOLD}[Resource {i}]{RESET}")
            print(f"    Type: {rtype}")
            print(f"    Duration: {dur_str}")
            print(f"    Download URL: `{dl}`")
            print(f"    Cover URL: `{cu}`")
    else:
        # Fallback: extract from top-level fields when there is no resources array
        download_url = extract_download_url(data)
        if not download_url:
            error("Could not extract a download URL from the API response. Raw response:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            sys.exit(1)
        print(f"\n{CYAN}{BOLD}🎬 Resource:{RESET}")
        print(f"    Download URL: `{download_url}`")
        if cover:
            print(f"    Cover URL: `{cover}`")

    print(f"\n{CYAN}Copy the link into a browser or download manager to save the file.{RESET}")
    sys.exit(0)


if __name__ == "__main__":
    main()
