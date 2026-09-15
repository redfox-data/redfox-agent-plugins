---
name: tiktok-video-downloader
description: TikTok video downloader — paste one or more TikTok video links and get watermark-free direct download URLs, with automatic TikTok link validation. Use when the user wants to download TikTok videos, save TikTok videos offline, get direct TikTok video links, or batch-download multiple TikTok videos. Trigger words: TikTok video download, TK video downloader, TikTok video parser, download TikTok video, batch TikTok download.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** when running this skill's commands, prefix them with `REDFOX_CHANNEL=<client>` where `<client>` is the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). Example: `REDFOX_CHANNEL=claude python3 ...`. If the client is unknown, omit the prefix — the script auto-detects the client from environment markers and falls back to `github`.

# TikTok Video Downloader

Paste TikTok video links and get watermark-free direct download URLs in one step. Powered by the [redfox.hk](https://redfox.hk/settings/api-keys?source=github) parsing service — supports single or batch links, with automatic TikTok link validation.

---

## Introduction

**Who it's for**: anyone who needs to download TikTok videos — content creators, video collectors, and marketing analysts.

**Core capabilities**:
- 📹 Paste a TikTok link and get a watermark-free mp4 direct download URL
- 📦 Batch parsing supported (separate multiple links with spaces)
- 🔍 Automatically validates TikTok links; non-TikTok links are rejected with a prompt and the flow stops
- ⏱️ Download links expire in about 5 minutes — use them right after parsing

---

## Features

| Feature | Description |
|------|------|
| **Watermark-free direct links** | Clean download URLs returned automatically — no manual processing |
| **Paste and parse** | Just paste the video link, nothing else required |
| **Batch parsing** | Paste multiple TikTok video links at once; results are parsed one by one and summarized |
| **Link validation** | Detects whether input links are TikTok video links; non-TikTok links are rejected and the flow stops |
| **Link agnostic** | Supports both www.tiktok.com web links and vm.tiktok.com short links |
| **Instant results** | Download URLs returned immediately after parsing |

---

## Quick Start

1. Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your API key
2. Set the environment variable: `export REDFOX_API_KEY=ark_your_key`
3. Paste a TikTok video link and go

---

## Usage Guide

> See `references/core_workflow.md` for the core execution workflow.

Just describe what you need in natural language — no commands to memorize. When a valid TikTok video link is provided, parse it directly and return the result.

### Common Phrasings

| Intent | Example prompt | Result |
|------|----------|------|
| Download a single video | "Download this video https://www.tiktok.com/@user/video/xxxxx" | Parse the link and return the watermark-free download URL |
| Batch download | "Download these videos: link1 link2 link3" | Parse in batch, return each result and a summary |
| Save a video | "Save this TikTok video for me" | Ask for the link, parse it, return the download URL |

### Supported Link Formats

| Platform | Format | Example |
|------|----------|------|
| TikTok | `https://www.tiktok.com/@<username>/video/<video-id>` | Desktop web link / mobile share link |
| TikTok | `https://vm.tiktok.com/<code>/` | Mobile share short link |

---

## Use Cases

| Scenario | Role | Example prompt | Benefit |
|------|------|----------|------|
| Footage collection | Video editor | "Download this TikTok video" | Get watermark-free footage straight into the editing workflow |
| Batch footage | Video editor | "Download these videos: link1 link2 link3" | Parse multiple links, get all footage at once |
| Content backup | Collector | "Save this TikTok video" | Keep a local copy even if the original is deleted |
| Trend analysis | Marketer | "Download this viral video" | Watch offline repeatedly and break down why it went viral |

---

## FAQ

**Q: How do I get my own API key?**
A: Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your token.

**Q: Do downloaded videos have watermarks?**
A: No. The returned URLs are watermark-free direct video links.

**Q: Can I parse multiple links in batch?**
A: Yes. Separate multiple TikTok video links with spaces; they are processed one by one with a success/failure summary at the end.

**Q: What happens if I pass a non-TikTok link?**
A: Links are validated automatically. A non-TikTok link triggers the prompt "Please provide a valid TikTok video link" and the flow stops.

**Q: What if a link fails to parse?**
A: Make sure the link is complete, the video still exists, and the account is public. Private accounts and deleted videos cannot be parsed.

**Q: Do download links expire?**
A: Yes. Download links are valid for about 5 minutes after parsing — copy and use them immediately; re-parse after expiry.

---

## Learn More

This tool is built on the video parsing service of [redfox.hk](https://redfox.hk/settings/api-keys?source=github). Visit the website for more capabilities and documentation.
