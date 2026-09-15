---
name: twitter-video-downloader
description: X (Twitter) video downloader — paste an X (Twitter) post link and get a watermark-free direct video download URL in one step. Use when the user wants to download X/Twitter videos, save a tweet's video, or get a direct X video link. Trigger words: X video download, Twitter video download, tweet video saver, X video parser, download Twitter video.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** when running this skill's commands, prefix them with `REDFOX_CHANNEL=<client>` where `<client>` is the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). Example: `REDFOX_CHANNEL=claude python3 ...`. If the client is unknown, omit the prefix — the script auto-detects the client from environment markers and falls back to `github`.

# X (Twitter) Video Downloader

Parse X (Twitter) video links through the [redfox.hk](https://redfox.hk/settings/api-keys?source=github) API and return watermark-free direct download URLs.

---

## Overview

- **Platform**: X (Twitter)
- **Content type**: Video (mp4 direct download link)
- **Input**: Paste an X (Twitter) video post link (one link per call; batch input is not supported)
- **Output**: A direct video download URL — copy it into a browser or download manager to save

---

## Usage

### Example Command

Download an X (Twitter) video:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://x.com/user/status/xxxxx"
```

### First-Time Setup

Configure your API key, then run:

```bash
# Set the environment variable
export REDFOX_API_KEY=ark_your_key

# Parse the video and get the download link
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://x.com/user/status/xxxxx"
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
| **Domain agnostic** | Supports both x.com and twitter.com links |
| **Instant results** | Download URL returned immediately after parsing |

---

## Common Use Cases

| Scenario | Example link | Notes |
|------|----------|------|
| Save a video from X | `https://x.com/user/status/xxxxx` | Get the watermark-free download URL |
| Offline collection | `https://twitter.com/user/status/xxxxx` | Parse, copy the link, download and keep |
| Content remixing | Any X video link | Download footage for editing and creation |
| Personal backup | Any X video link | Back up videos you like to local storage |

### Supported Link Formats

| Platform | Format | Example |
|------|----------|------|
| X (Twitter) | `https://x.com/<username>/status/<tweet-id>` | Desktop web link / mobile share link |
| X (Twitter) | `https://twitter.com/<username>/status/<tweet-id>` | Legacy domain link |

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

This tool is built on the `parseWork/videoDownload/x` endpoint of [redfox.hk](https://redfox.hk/settings/api-keys?source=github). Visit the website for more API capabilities and documentation.
