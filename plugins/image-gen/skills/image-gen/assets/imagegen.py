#!/usr/bin/env python3
"""
Redfox AI Image Generator - image generation tool based on gpt-image-2

Uses the Redfox v2 endpoints:
    SUBMIT: POST https://redfox.hk/story/api/parseWork/imageGen/gptImage2Submit
    RESULT: POST https://redfox.hk/story/api/parseWork/imageGen/gptImage2Result

Request parameters:
    prompt          (String, required)
    resolution      (String, required) 1k / 2k / 4k
    size            (String, required) aspect ratio: 1:1 / 3:2 / 2:3 / 4:3 / 3:4 / 5:4 / 4:5 /
                                    16:9 / 9:16 / 2:1 / 1:2 / 21:9 / 9:21
    n               (Integer, required) number of images, max 4
    referenceImages (Array, required) reference image URLs, max 2 (empty array for text-to-image)

Response fields (data):
    taskId / status(completed|processing|failed) / progress(0-100) /
    imageUrls[] / failReason / model / resolution / size

Usage:
    python3 imagegen.py "prompt" [options]
    python3 imagegen.py "edit prompt" --image ~/path/to/ref.png
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

SUBMIT_URL = "https://redfox.hk/story/api/parseWork/imageGen/gptImage2Submit"
RESULT_URL = "https://redfox.hk/story/api/parseWork/imageGen/gptImage2Result"
UPLOAD_URL = "https://redfox.hk/story/api/parseWork/imageGen/uploadImage"
CONFIG_DIR = Path.home() / ".redfox" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
POLL_INTERVAL = 3  # seconds
MAX_POLL_ATTEMPTS = 80  # max ~4 minutes

# Aspect ratios supported by the size parameter
VALID_ASPECTS = {
    "1:1", "3:2", "2:3", "4:3", "3:4", "5:4", "4:5",
    "16:9", "9:16", "2:1", "1:2", "21:9", "9:21",
}
VALID_RESOLUTIONS = {"1k", "2k", "4k"}

# Legacy pixel-format compatibility: pixel size -> (aspect ratio, recommended resolution tier)
LEGACY_SIZE_MAP = {
    "1024x1024": ("1:1", "1k"),
    "1024x1536": ("2:3", "1k"),
    "1536x1024": ("3:2", "1k"),
    "1792x1024": ("16:9", "1k"),
    "1024x1792": ("9:16", "1k"),
    "2048x2048": ("1:1", "2k"),
    "2048x1152": ("16:9", "2k"),
    "1152x2048": ("9:16", "2k"),
}

MAX_PROMPT_LENGTH = 500
MAX_REFERENCE_IMAGES = 2
MAX_COUNT = 4

# ── Redfox channel attribution ──
# Appends the running AI client to the API `source` field for per-platform stats.
# Priority: REDFOX_CHANNEL env var (documented in SKILL.md) > client env markers > "github".
SOURCE_BASE = "imageGen"


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


def upload_image(api_key, image_path):
    """Upload a local image file to OSS, return the image URL."""
    image_path = os.path.expanduser(image_path)
    if not os.path.isfile(image_path):
        error(f"Image file not found: {image_path}")
        return None

    ext = os.path.splitext(image_path)[1].lower()
    fmt_map = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}
    fmt = fmt_map.get(ext, "png")

    step(f"Uploading image: {image_path}")

    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f)}
            data = {"format": fmt}
            headers = {"REDFOX_API_KEY": api_key, "X-API-KEY": api_key}
            resp = requests.post(UPLOAD_URL, files=files, data=data, headers=headers, timeout=60, verify=True)
            result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"Upload request failed: {e}")
        return None
    except json.JSONDecodeError:
        error(f"Upload returned invalid JSON: {resp.text[:200]}")
        return None

    code = result.get("code")
    if not str(code).startswith("2"):
        error(f"Upload failed (code {code}): {result.get('msg', '')}")
        return None

    data = result.get("data") or {}
    image_url = data.get("imageUrl")
    if not image_url:
        error("Upload succeeded but no imageUrl returned")
        return None

    info(f"Upload complete: {image_url}")
    return image_url


def confirm_retry():
    """Ask the user whether to retry."""
    while True:
        answer = input(f"{YELLOW}[?]{RESET} Retry? (y/n): ").strip().lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False


def normalize_size(size_arg, resolution_arg):
    """Normalize the CLI --size value into (aspect, resolution) for the API.

    Two input formats are supported:
      1. Legacy pixel format: 1792x1024 -> ("16:9", "1k")
      2. Aspect-ratio format: 16:9 -> ("16:9", resolution_arg or "2k")
    """
    size_str = (size_arg or "").strip()

    if size_str in LEGACY_SIZE_MAP:
        aspect, default_res = LEGACY_SIZE_MAP[size_str]
        resolution = (resolution_arg or default_res).strip().lower()
        if resolution not in VALID_RESOLUTIONS:
            error(f"Unsupported --resolution: {resolution}")
            sys.exit(1)
        return aspect, resolution

    if size_str in VALID_ASPECTS:
        resolution = (resolution_arg or "2k").strip().lower()
        if resolution not in VALID_RESOLUTIONS:
            error(f"Unsupported --resolution: {resolution}")
            sys.exit(1)
        return size_str, resolution

    error(f"Unsupported --size: {size_str}")
    print(f"  Valid aspect ratios: {', '.join(sorted(VALID_ASPECTS))}")
    print(f"  Legacy pixel formats: {', '.join(sorted(LEGACY_SIZE_MAP.keys()))}")
    sys.exit(1)


def submit_task(session, prompt, resolution, aspect, n, reference_images):
    """Submit image generation task via gptImage2Submit, return taskId."""
    payload = {
        "prompt": prompt,
        "resolution": resolution,
        "size": aspect,
        "n": n,
        "referenceImages": reference_images or [],
        "source": build_source(),
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

    data = result.get("data") or {}
    task_id = data.get("taskId")
    if not task_id:
        error("API did not return taskId")
        return None

    return task_id


def poll_result(session, task_id):
    """Poll gptImage2Result until completed/failed/timeout, return imageUrls list."""
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        try:
            resp = session.post(RESULT_URL, json={"taskId": task_id}, timeout=15)
            result = resp.json()
        except requests.exceptions.RequestException as e:
            warn(f"Poll request failed (attempt {attempt}): {e}")
            time.sleep(POLL_INTERVAL)
            continue
        except json.JSONDecodeError:
            warn(f"Invalid JSON response (attempt {attempt})")
            time.sleep(POLL_INTERVAL)
            continue

        code = result.get("code")
        if not str(code).startswith("2"):
            error(f"Query failed (code {code}): {result.get('msg', '')}")
            return None

        data = result.get("data") or {}
        status = data.get("status")

        if status == "completed":
            urls = data.get("imageUrls") or []
            if isinstance(urls, str):
                urls = [urls]
            print()  # finish the progress line
            return urls
        elif status == "failed":
            reason = data.get("failReason") or "unknown"
            print()
            error(f"Generation failed: {reason}")
            return None
        else:
            # processing / pending
            progress = data.get("progress")
            elapsed = attempt * POLL_INTERVAL
            suffix = f" {progress}%" if isinstance(progress, int) else ""
            print(f"\r  {CYAN}⏳ Generating...{suffix} ({elapsed}s){RESET}", end="", flush=True)
            time.sleep(POLL_INTERVAL)

    print()
    error("Timeout: task did not complete within expected time")
    return None


def download_images(session, image_urls, output_dir, prefix="image"):
    """Download generated images to output directory."""
    downloaded = []
    total = len(image_urls)

    for i, url in enumerate(image_urls, 1):
        ext = ".png"
        url_path = url.split("?")[0]
        for fmt in [".png", ".jpg", ".jpeg", ".webp"]:
            if url_path.lower().endswith(fmt):
                ext = fmt
                break

        filename = f"{prefix}_{i}{ext}" if total > 1 else f"{prefix}{ext}"
        filepath = os.path.join(output_dir, filename)

        step(f"Downloading {i}/{total}: {filename}")
        try:
            resp = session.get(url, stream=True, timeout=120)
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
            downloaded.append(filepath)
        except requests.exceptions.RequestException as e:
            error(f"Download failed: {e}")

    return downloaded


def main():
    parser = argparse.ArgumentParser(
        description="AI Image Generator - based on gpt-image-2 (gptImage2Submit/gptImage2Result endpoints)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Text-to-image (default 16:9 + 2k)
  python3 imagegen.py "An orange cat sitting on a windowsill watching the sunset"

  # Vertical 4k
  python3 imagegen.py "cyberpunk city" --size 9:16 --resolution 4k

  # Batch of 4
  python3 imagegen.py "icon set, flat style" -n 4

  # Image-to-image (max 2 reference images)
  python3 imagegen.py "Make the cat white and change the background to a starry sky" --image ~/Pictures/cat.png

  # Legacy pixel format (auto-mapped to aspect ratio + resolution tier)
  python3 imagegen.py "logo design" --size 1792x1024
        """,
    )
    parser.add_argument("prompt", help="Image generation/editing prompt (max 500 characters)")
    parser.add_argument("--api-key", help="API key (falls back to env var or config file)")
    parser.add_argument("-o", "--output-dir", help="Output directory (default ~/Downloads/RedfoxImages)")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help=f"Number of images to generate (1-{MAX_COUNT}, default 1, API max 4)")
    parser.add_argument("--size", default="16:9",
                        help="Aspect ratio (default 16:9, options: "
                             + ", ".join(sorted(VALID_ASPECTS))
                             + "); legacy pixel formats like 1792x1024 also work")
    parser.add_argument("--resolution", default=None, choices=sorted(VALID_RESOLUTIONS),
                        help="Resolution tier 1k/2k/4k (default: follows the pixel-format tier, aspect-ratio format defaults to 2k)")
    parser.add_argument("--image", action="append", default=None,
                        help=f"Reference image path or URL (repeatable, max {MAX_REFERENCE_IMAGES}; enables image-to-image mode)")
    parser.add_argument("--no-download", action="store_true",
                        help="Submit the task and return the taskId only, without waiting for the result")
    parser.add_argument("--task-id", help="Query the result of an existing task directly (skip submission)")
    parser.add_argument("--prefix", default="image", help="Downloaded filename prefix (default image)")

    # Deprecated arguments: no longer supported by the API, kept for CLI backward compatibility and ignored
    parser.add_argument("--quality", help="[Deprecated] use --resolution for quality tiers; this argument is ignored")
    parser.add_argument("--format", dest="fmt", help="[Deprecated] the API always outputs PNG; this argument is ignored")
    parser.add_argument("--bg", "--background", dest="bg",
                        help="[Deprecated] background is no longer supported; this argument is ignored")
    parser.add_argument("--compression", type=int,
                        help="[Deprecated] outputCompression is no longer supported; this argument is ignored")
    parser.add_argument("--fidelity",
                        help="[Deprecated] inputFidelity is no longer supported; this argument is ignored")

    args = parser.parse_args()

    # Warn about deprecated arguments
    deprecated = []
    if args.quality:
        deprecated.append("--quality")
    if args.fmt:
        deprecated.append("--format")
    if args.bg:
        deprecated.append("--bg")
    if args.compression is not None:
        deprecated.append("--compression")
    if args.fidelity:
        deprecated.append("--fidelity")

    # Validate count
    if args.count < 1 or args.count > MAX_COUNT:
        error(f"-n must be between 1 and {MAX_COUNT} (API max is 4)")
        sys.exit(1)

    # Validate prompt length
    if len(args.prompt) > MAX_PROMPT_LENGTH:
        error(f"Prompt too long ({len(args.prompt)} chars), please keep it under {MAX_PROMPT_LENGTH} characters")
        sys.exit(1)

    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     Redfox AI Image Generator        ║
  ║     gpt-image-2 · text & image gen   ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    if deprecated:
        warn(f"These arguments are deprecated and will be ignored: {', '.join(deprecated)}")

    # ── API Key ──
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        error("API Key not found. Set the REDFOX_API_KEY environment variable or pass --api-key")
        print(f"  Get a key: https://redfox.hk/settings/api-keys?source=github")
        sys.exit(1)

    # ── Session (auth header REDFOX_API_KEY; X-API-KEY kept for compatibility) ──
    session = requests.Session()
    session.verify = True
    session.headers.update({
        "Content-Type": "application/json",
        "REDFOX_API_KEY": api_key,
        "X-API-KEY": api_key,
    })

    # ── Mode: Query existing task ──
    if args.task_id:
        step(f"Querying task: {args.task_id}")
        image_urls = poll_result(session, args.task_id)
        if not image_urls:
            sys.exit(1)
        info(f"Generated {len(image_urls)} image(s)")
        output_dir = args.output_dir or str(Path.home() / "Downloads" / "RedfoxImages")
        os.makedirs(output_dir, exist_ok=True)
        downloaded = download_images(session, image_urls, output_dir, args.prefix)
        if downloaded:
            print(f"\n{GREEN}{BOLD}✓ Done!{RESET}")
            for f in downloaded:
                size_kb = os.path.getsize(f) / 1024
                print(f"  {f} ({size_kb:.1f} KB)")
        sys.exit(0)

    # ── Mode: Submit new task ──
    prompt = args.prompt.strip()
    if not prompt:
        error("Prompt cannot be empty")
        sys.exit(1)

    # Normalize size / resolution to the API format
    aspect, resolution = normalize_size(args.size, args.resolution)

    # Handle reference images
    reference_images = []
    if args.image:
        if len(args.image) > MAX_REFERENCE_IMAGES:
            warn(f"Too many reference images, keeping only the first {MAX_REFERENCE_IMAGES}")
        for img in args.image[:MAX_REFERENCE_IMAGES]:
            if img.startswith("http://") or img.startswith("https://"):
                reference_images.append(img)
            else:
                url = upload_image(api_key, img)
                if not url:
                    sys.exit(1)
                reference_images.append(url)
        step(f"Mode: image-to-image (referenceImages={len(reference_images)})")
    else:
        step("Mode: text-to-image")

    step(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    step(f"Parameters: size={aspect}, resolution={resolution}, n={args.count}")

    while True:
        step("Submitting task...")
        task_id = submit_task(session, prompt, resolution, aspect, args.count, reference_images)
        if task_id:
            break
        if not confirm_retry():
            sys.exit(1)

    info(f"Task submitted: {task_id}")

    if args.no_download:
        print(f"\n{GREEN}{BOLD}✓ Task submitted successfully{RESET}")
        print(f"  taskId: {task_id}")
        print(f"  Query command: python3 imagegen.py \"\" --task-id {task_id}")
        sys.exit(0)

    step("Waiting for generation...")
    image_urls = poll_result(session, task_id)
    if not image_urls:
        sys.exit(1)

    info(f"Generated {len(image_urls)} image(s)")

    output_dir = args.output_dir or str(Path.home() / "Downloads" / "RedfoxImages")
    os.makedirs(output_dir, exist_ok=True)

    downloaded = download_images(session, image_urls, output_dir, args.prefix)

    if downloaded:
        print(f"\n{GREEN}{BOLD}✓ Done!{RESET}")
        for f in downloaded:
            size_kb = os.path.getsize(f) / 1024
            print(f"  {f} ({size_kb:.1f} KB)")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}✗ Download failed{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
