---
name: instagram-video-downloader
description: Instagram video downloader — paste an Instagram Reel or post link and get a watermark-free direct video download URL in one step. Use when the user wants to download Instagram videos, save IG Reels, or get a direct Instagram video link. Trigger words: Instagram video download, IG video download, Ins video saver, Instagram Reel download, parse Instagram video.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** when running this skill's commands, prefix them with `REDFOX_CHANNEL=<client>` where `<client>` is the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). Example: `REDFOX_CHANNEL=claude python3 ...`. If the client is unknown, omit the prefix — the script auto-detects the client from environment markers and falls back to `github`.

# Instagram Video Downloader

Parse Instagram video links through the [redfox.hk](https://redfox.hk/settings/api-keys?source=github) API and return watermark-free direct download URLs.

---

## Overview

- **Platform**: Instagram
- **Content type**: Video (mp4 direct download link)
- **Input**: Paste an Instagram video link (one link per call; batch input is not supported)
- **Output**: A direct video download URL — copy it into a browser or download manager to save
- **Link display rule**: Always show the full original download and cover URLs — never truncate them with `...` or any other form

---

## Usage

### Example Command

Download an Instagram video:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.instagram.com/reel/xxxxx/"
```

### First-Time Setup

Configure your API key, then run:

```bash
# Set the environment variable
export REDFOX_API_KEY=ark_your_key

# Parse the video and get the download link
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.instagram.com/reel/xxxxx/"
```

> Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your API key.

### Configuration Options

Choose any one:

| Method | Command |
|------|------|
| **Environment variable** (recommended) | `export REDFOX_API_KEY=ark_your_key` |
| **CLI argument** | `REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "<url>" --api-key ark_your_key` |
| **Config file** | `echo '{"api_key":"ark_your_key"}' > ~/.redfox/apis/redfox.json` |

---

## Features

| Feature | Description |
|------|------|
| **Watermark-free direct links** | The API returns clean download URLs automatically — no manual processing |
| **Paste and parse** | Just paste the post link, nothing else required |
| **Link agnostic** | Supports both Instagram Reel and regular post links |
| **Instant results** | Download URL returned immediately after parsing |

---

## Common Use Cases

| Scenario | Example link | Notes |
|------|----------|------|
| Save a video from IG | `https://www.instagram.com/reel/xxxxx/` | Get the watermark-free download URL |
| Offline Reel collection | `https://www.instagram.com/reel/xxxxx/` | Parse, copy the link, download and keep |
| Content remixing | Any Instagram video link | Download footage for editing and creation |
| Personal backup | Any Instagram video link | Back up videos you like to local storage |

### Supported Link Formats

| Platform | Format | Example |
|------|----------|------|
| Instagram Reel | `https://www.instagram.com/reel/<shortcode>/` | Reel short video |
| Instagram Post | `https://www.instagram.com/p/<shortcode>/` | Regular post video |

---

## FAQ

**Q: How do I get my own API key?**
A: Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your token.

**Q: Do downloaded videos have watermarks?**
A: No. The API returns watermark-free direct video URLs.

**Q: Can I pass multiple links at once?**
A: No. One link per call — batch input will fail parsing.

**Q: What if a link fails to parse?**
A: Make sure the link is complete, the post still exists, and the account is public. Private accounts and deleted posts cannot be parsed.

---

## Learn More

This tool is built on the `parseWork/videoDownload/instagram` endpoint of [redfox.hk](https://redfox.hk/settings/api-keys?source=github). Visit the website for more API capabilities and documentation.
