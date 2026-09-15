#!/usr/bin/env python3
"""
Redfox AI Video Generator - video generation tool based on Seedance 2.0
Submits video generation tasks via the redfox.hk API and downloads the results

Usage:
    python3 videogen.py "prompt" [options]
    python3 videogen.py "ignored" --task-id vg_xxx
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

SUBMIT_URL = "https://redfox.hk/story/api/parseWork/videoGen/submit"
RESULT_URL = "https://redfox.hk/story/api/parseWork/videoGen/result"
CONFIG_DIR = Path.home() / ".redfox" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE_BASE = "seedance2.0"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"

POLL_INTERVAL = 10  # seconds
MAX_POLL_ATTEMPTS = 120  # max ~20 minutes

# ── Redfox channel attribution ──
# Appends the running AI client to the API `source` field for per-platform stats.
# Priority: REDFOX_CHANNEL env var (documented in SKILL.md) > client env markers > "github".


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


def get_api_key(cli_key=None):
    """Get API key: CLI arg > env var > config file."""
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


def confirm_retry():
    """Ask the user whether to retry."""
    while True:
        answer = input(f"{YELLOW}[?]{RESET} Retry? (y/n): ").strip().lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False


def submit_video_task(session, prompt, params, image_url=None):
    """Submit video generation task, return taskId."""
    # Build content array
    content = [{"type": "text", "text": prompt}]
    if image_url:
        content.append({
            "type": "image_url",
            "imageUrl": image_url,
            "imageRole": "first_frame",
        })

    payload = {
        "content": content,
        "model": DEFAULT_MODEL,
        "source": build_source(),
        "resolution": params["resolution"],
        "ratio": params["ratio"],
        "duration": params["duration"],
        "seed": params["seed"],
        "watermark": params["watermark"],
        "generateAudio": params["generateAudio"],
        "returnLastFrame": params["returnLastFrame"],
        "executionExpiresAfter": 172800,
    }

    try:
        resp = session.post(SUBMIT_URL, json=payload, timeout=30)
        result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        return None

    code = result.get("code")
    msg = result.get("msg", "")

    if not str(code).startswith("2"):
        error(f"Submit failed (code {code}): {msg}")
        return None

    data = result.get("data")
    if not data or not data.get("taskId"):
        error("API did not return taskId")
        return None

    return data["taskId"]


def poll_video_result(session, task_id):
    """Poll for video task result until succeeded/failed/expired/timeout."""
    consecutive_errors = 0

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        try:
            resp = session.post(RESULT_URL, json={"taskId": task_id}, timeout=15)
            result = resp.json()
        except requests.exceptions.RequestException as e:
            consecutive_errors += 1
            warn(f"Poll request failed (attempt {attempt}): {e}")
            if consecutive_errors >= 5:
                error("Too many consecutive network errors, giving up")
                return None
            time.sleep(POLL_INTERVAL)
            continue
        except json.JSONDecodeError:
            consecutive_errors += 1
            warn(f"Invalid JSON response (attempt {attempt})")
            if consecutive_errors >= 5:
                error("Too many consecutive decode errors, giving up")
                return None
            time.sleep(POLL_INTERVAL)
            continue

        consecutive_errors = 0  # Reset on success

        code = result.get("code")
        if not str(code).startswith("2"):
            error(f"Query failed (code {code}): {result.get('msg', '')}")
            return None

        data = result.get("data", {})
        status = data.get("status")

        if status == "succeeded":
            return data
        elif status == "failed":
            reason = data.get("failReason", "unknown")
            error(f"Generation failed: {reason}")
            return None
        elif status == "expired":
            error("Task expired: the task did not complete within the allowed time")
            return None
        else:
            # queued or running
            elapsed = attempt * POLL_INTERVAL
            status_label = {"queued": "queued", "running": "generating"}.get(status, status)
            print(f"\r  {CYAN}⏳ Generating... ({elapsed}s) [{status_label}]{RESET}", end="", flush=True)
            time.sleep(POLL_INTERVAL)

    print()
    error(f"Timeout: task did not complete within {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s")
    print(f"  You can query later with: --task-id {task_id}")
    return None


def download_video(session, video_url, output_dir, prefix="video", task_id=""):
    """Download generated video to output directory."""
    # Determine extension from URL
    ext = ".mp4"
    url_path = video_url.split("?")[0]
    for fmt in [".mp4", ".mov", ".avi", ".webm"]:
        if url_path.lower().endswith(fmt):
            ext = fmt
            break

    # Handle filename conflict: append short taskId if file exists
    filename = f"{prefix}{ext}"
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath) and task_id:
        short_id = task_id.replace("vg_", "")[:8]
        filename = f"{prefix}_{short_id}{ext}"
        filepath = os.path.join(output_dir, filename)

    step(f"Downloading video: {filename}")
    try:
        resp = session.get(video_url, stream=True, timeout=300)
        resp.raise_for_status()
        total_size = int(resp.headers.get("content-length", 0))
        dl = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    dl += len(chunk)
                    if total_size > 0:
                        pct = int(dl * 100 / total_size)
                        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                        print(f"\r  {bar} {pct}%", end="", flush=True)
        print()
        return filepath
    except requests.exceptions.RequestException as e:
        error(f"Download failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="AI Video Generator - based on the Seedance 2.0 model, turns prompts into videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic generation
  python3 videogen.py "An orange cat yawning on a windowsill, warm sunlight on its fur"

  # Vertical short video
  python3 videogen.py "Stylish city night scene, neon lights flickering" --ratio 9:16

  # HD 10 seconds
  python3 videogen.py "Slow motion of waves crashing on rocks" --resolution 1080p --duration 10

  # Preset virtual character
  python3 videogen.py "A young woman reading in a library" --image-url "asset://female_student_01"

  # Submit only
  python3 videogen.py "complex scene" --no-download

  # Query an existing task
  python3 videogen.py "ignored" --task-id vg_abc123def456
        """,
    )
    parser.add_argument("prompt", help="Video generation prompt (any language)")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"],
                        help="Video resolution (default 720p)")
    parser.add_argument("--ratio", default="16:9",
                        choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
                        help="Aspect ratio (default 16:9)")
    parser.add_argument("--duration", type=int, default=5,
                        help="Video duration in seconds: 4-15 or -1 (smart) (default 5)")
    parser.add_argument("--seed", type=int, default=-1,
                        help="Random seed: -1 (random) to 2147483647 (default -1)")
    parser.add_argument("--no-audio", action="store_true",
                        help="Disable audio generation (enabled by default)")
    parser.add_argument("--watermark", action="store_true",
                        help="Add watermark (disabled by default)")
    parser.add_argument("--return-last-frame", action="store_true",
                        help="Return the URL of the video's last frame")
    parser.add_argument("--image-url",
                        help="Reference image URL (asset:// format references preset virtual characters)")
    parser.add_argument("--api-key", help="API key (sign up at https://redfox.hk/settings/api-keys?source=github)")
    parser.add_argument("-o", "--output-dir", help="Output directory (default ~/Downloads/RedfoxVideos)")
    parser.add_argument("--prefix", default="video", help="Downloaded filename prefix (default video)")
    parser.add_argument("--no-download", action="store_true",
                        help="Submit the task and return the taskId only, without waiting for the result")
    parser.add_argument("--task-id", help="Query the result of an existing task directly (skip submission)")

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════════╗
  ║      Redfox AI Video Generator           ║
  ║      Seedance 2.0 · text-to-video        ║
  ╚══════════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── API Key ──
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        error("API Key not found. Set the REDFOX_API_KEY environment variable or pass --api-key")
        print(f"  Get a key: https://redfox.hk/settings/api-keys?source=github")
        sys.exit(1)

    # ── Session (all requests use HTTPS with SSL verification) ──
    session = requests.Session()
    session.verify = True
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    # ── Mode: Query existing task ──
    if args.task_id:
        step(f"Querying task: {args.task_id}")
        result = poll_video_result(session, args.task_id)
        if not result:
            sys.exit(1)

        print()
        video_url = result.get("videoUrl")
        last_frame_url = result.get("lastFrameUrl")
        duration = result.get("duration", "?")
        resolution = result.get("resolution", "?")
        ratio = result.get("ratio", "?")
        usage = result.get("usage", {})
        tokens = usage.get("totalTokens", "?") if usage else "?"

        info(f"Video ready: {duration}s, {resolution}, {ratio}")
        if last_frame_url:
            info(f"Last frame: {last_frame_url}")
        if usage:
            info(f"Token usage: {tokens}")

        if video_url:
            output_dir = os.path.expanduser(args.output_dir) if args.output_dir else str(Path.home() / "Downloads" / "RedfoxVideos")
            os.makedirs(output_dir, exist_ok=True)
            filepath = download_video(session, video_url, output_dir, args.prefix, args.task_id)
            if filepath:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"\n{GREEN}{BOLD}✓ Done!{RESET}")
                print(f"  {filepath} ({size_mb:.1f} MB)")
            else:
                print(f"\n{RED}{BOLD}✗ Download failed{RESET}")
                sys.exit(1)
        else:
            warn("Task succeeded but no videoUrl returned")
        sys.exit(0)

    # ── Mode: Submit new task ──
    prompt = args.prompt.strip()
    if not prompt:
        error("Prompt cannot be empty")
        sys.exit(1)

    # Validate image-url format
    if args.image_url and not args.image_url.startswith("asset://"):
        error(f"image-url only supports the asset:// format for preset virtual characters, got: {args.image_url}")
        error("See the Volcano Ark asset & virtual-character library docs for available IDs")
        sys.exit(1)

    # Validate duration
    if args.duration != -1 and (args.duration < 4 or args.duration > 15):
        error(f"duration must be 4-15 or -1 (smart), got: {args.duration}")
        sys.exit(1)

    step(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    step(f"Settings: {args.resolution}, {args.ratio}, {args.duration}s, seed={args.seed}, audio={'off' if args.no_audio else 'on'}")

    if args.image_url:
        step(f"Reference image: {args.image_url}")

    # Build parameters
    params = {
        "resolution": args.resolution,
        "ratio": args.ratio,
        "duration": args.duration,
        "seed": args.seed,
        "watermark": args.watermark,
        "generateAudio": not args.no_audio,
        "returnLastFrame": args.return_last_frame,
    }

    # Submit
    while True:
        step("Submitting video generation task...")
        task_id = submit_video_task(session, prompt, params, args.image_url)
        if task_id:
            break
        if not confirm_retry():
            sys.exit(1)

    info(f"Task submitted: {task_id}")

    if args.no_download:
        print(f"\n{GREEN}{BOLD}✓ Task submitted successfully{RESET}")
        print(f"  taskId: {task_id}")
        print(f"  Query command: python3 videogen.py \"ignored\" --task-id {task_id}")
        sys.exit(0)

    # Poll for result
    step("Waiting for video generation (may take several minutes)...")
    result = poll_video_result(session, task_id)
    if not result:
        sys.exit(1)

    print()
    video_url = result.get("videoUrl")
    last_frame_url = result.get("lastFrameUrl")
    duration = result.get("duration", "?")
    resolution = result.get("resolution", "?")
    ratio = result.get("ratio", "?")
    usage = result.get("usage", {})
    tokens = usage.get("totalTokens", "?") if usage else "?"

    info(f"Video ready: {duration}s, {resolution}, {ratio}")
    if last_frame_url:
        info(f"Last frame: {last_frame_url}")
    if usage:
        info(f"Token usage: {tokens}")

    if video_url:
        output_dir = os.path.expanduser(args.output_dir) if args.output_dir else str(Path.home() / "Downloads" / "RedfoxVideos")
        os.makedirs(output_dir, exist_ok=True)
        filepath = download_video(session, video_url, output_dir, args.prefix, task_id)
        if filepath:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"\n{GREEN}{BOLD}✓ Done!{RESET}")
            print(f"  {filepath} ({size_mb:.1f} MB)")
            sys.exit(0)
        else:
            print(f"\n{RED}{BOLD}✗ Download failed{RESET}")
            sys.exit(1)
    else:
        error("Task succeeded but no videoUrl returned")
        sys.exit(1)


if __name__ == "__main__":
    main()
