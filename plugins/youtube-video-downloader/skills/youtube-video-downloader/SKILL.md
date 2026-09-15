---
name: youtube-video-downloader
description: YouTube video downloader — paste a YouTube video link (regular videos, Shorts, or youtu.be) and get watermark-free direct download URLs in multiple resolutions. Use when the user wants to download YouTube videos, save YouTube videos offline, or get direct YouTube video/audio links. Trigger words: YouTube video download, yt video downloader, save YouTube video, YouTube video parser, YouTube Shorts download.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** when running this skill's commands, prefix them with `REDFOX_CHANNEL=<client>` where `<client>` is the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). Example: `REDFOX_CHANNEL=claude python3 ...`. If the client is unknown, omit the prefix — the script auto-detects the client from environment markers and falls back to `github`.

# YouTube Video Downloader

Parse YouTube video links through the [redfox.hk](https://redfox.hk/settings/api-keys?source=github) API and return watermark-free direct download URLs (resources may include both video and audio files in different formats).

---

## Overview

- **Platform**: YouTube
- **Content type**: Video / audio (mp4 / webm / m4a etc.; resources may contain both video and audio files)
- **Input**: Paste a YouTube video link (one link per call; batch input is not supported)
- **Output**: Direct download URLs — copy into a browser or download manager to save
- **Link display rule**: Always show the full original download and cover URLs — never truncate them with `...` or any other form
- **Field display rules**: The result must show all of the following fields:
  - Description (desc): full original text, line by line, never truncated
  - Resource list: for each resource object show its type (type), duration (durationSeconds), download URL (downloadUrl) and cover URL (coverUrl)
  - When the API returns no resources array, automatically fall back to the top-level fields of the same name for compatibility

---

## Usage

### Example Command

Download a YouTube video:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.youtube.com/watch?v=xxxxx"
```

### First-Time Setup

Configure your API key, then run:

```bash
# Set the environment variable
export REDFOX_API_KEY=ark_your_key

# Parse the video and get the download links
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.youtube.com/watch?v=xxxxx"
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
| **Multiple resources** | Returns several resources (video files, audio files, etc.); all download links are listed in order — pick the ones you need by type |
| **Paste and parse** | Just paste the video link, nothing else required |
| **Instant results** | Download URLs returned immediately after parsing |

---

## Common Use Cases

| Scenario | Example link | Notes |
|------|----------|------|
| Save a video from YouTube | `https://www.youtube.com/watch?v=xxxxx` | Get watermark-free video/audio download URLs |
| Offline Shorts collection | `https://www.youtube.com/shorts/xxxxx` | Parse, copy the link, download and keep |
| Content remixing | Any YouTube video link | Download footage for editing and creation |
| Personal backup | Any YouTube video link | Back up videos you like to local storage |

### Supported Link Formats

| Platform | Format | Example |
|------|----------|------|
| YouTube regular video | `https://www.youtube.com/watch?v=<videoId>` | Standard video link |
| YouTube Shorts | `https://www.youtube.com/shorts/<videoId>` | Shorts vertical video |
| YouTube short link | `https://youtu.be/<videoId>` | Share short link |

---

## FAQ

**Q: How do I get my own API key?**
A: Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your token.

**Q: Do downloaded videos have watermarks?**
A: No. The API returns watermark-free direct video URLs.

**Q: Will multiple resources be returned?**
A: Yes. The API usually returns several resources, possibly including video and audio files in different formats (mp4, webm, m4a, etc.). Every resource's download link is listed in full — choose what you need.

**Q: Can I pass multiple links at once?**
A: No. One link per call — batch input will fail parsing.

**Q: What if a link fails to parse?**
A: Make sure the link is complete, the video still exists, and it is not region-restricted. Deleted or restricted videos cannot be parsed.

---

## Learn More

This tool is built on the `parseWork/videoDownload/youtube` endpoint of [redfox.hk](https://redfox.hk/settings/api-keys?source=github). Visit the website for more API capabilities and documentation.
