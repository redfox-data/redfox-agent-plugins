# Redfox Agent Plugins

[![Validate](https://github.com/redfox-data/redfox-agent-plugins/actions/workflows/validate.yml/badge.svg)](https://github.com/redfox-data/redfox-agent-plugins/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Spec%20v1-blue)](https://agentskills.io)

![Plugins](https://img.shields.io/badge/plugins-10-blue)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)
![Claude Code](https://img.shields.io/badge/Claude_Code-%E2%9C%93-D97757)
![OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-%E2%9C%93-10A37F)
![Cursor](https://img.shields.io/badge/Cursor-%E2%9C%93-000000)
![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-%E2%9C%93-8E75B9)

Production-ready [Agent Skills](https://agentskills.io) for global creators — video downloaders, AI generation, OCR and cross-platform trending search, powered by [Redfox Data](https://redfox.hk).

One repository, four platforms: **Claude Code**, **OpenAI Codex**, **Cursor**, and **Gemini CLI**.

## ⚡ Install in Claude Code

**1. Add the marketplace** (one time):

```text
/plugin marketplace add redfox-data/redfox-agent-plugins
```

**2. Install any plugin** (swap in the plugin ID you want):

```text
/plugin install youtube-video-downloader@redfox-agent-plugins
```

> No approval or publisher account needed — any public GitHub marketplace installs directly. On **OpenAI Codex**, **Cursor**, or **Gemini CLI**? See [Quick Start](#quick-start).

## Plugins

| Plugin | ID | Description |
|---|---|---|
| [YouTube Video Downloader](plugins/youtube-video-downloader/) | `youtube-video-downloader` | Watermark-free YouTube video downloader with multi-resolution direct links (videos, Shorts, youtu.be) |
| [Instagram Video Downloader](plugins/instagram-video-downloader/) | `instagram-video-downloader` | Watermark-free Instagram Reel and video downloader |
| [X (Twitter) Video Downloader](plugins/twitter-video-downloader/) | `twitter-video-downloader` | Watermark-free X (Twitter) video downloader |
| [TikTok Video Downloader](plugins/tiktok-video-downloader/) | `tiktok-video-downloader` | Watermark-free TikTok video downloader |
| [YouTube Transcript Extractor](plugins/youtube-digest/) | `youtube-digest` | Extract transcripts/captions from any YouTube video, auto-translate to your language, export to Excel/Markdown |
| [AI Image Generator](plugins/image-gen/) | `image-gen` | Text-to-image and image-to-image generation powered by gpt-image-2 |
| [AI Video Generator (Seedance)](plugins/seedance-video-gen/) | `seedance-video-gen` | Text-to-video generation powered by Seedance 2.0 with resolution/ratio/duration control |
| [PDF & Image Text Extractor](plugins/pdf-image-text-extractor/) | `pdf-image-text-extractor` | OCR text extraction from PDFs and images with format preserved, table structuring, batch directory processing |
| [Overseas Trending Search](plugins/overseas-trending-search/) | `overseas-trending-search` | Search any keyword across X (Twitter), TikTok and YouTube at once, get unified Top-N trending posts with HTML report |
| [Account Video Downloader](plugins/account-video-downloader/) | `account-video-downloader` | Batch-extract videos from account homepages across YouTube, Douyin, Kuaishou and Bilibili |

## Quick Start

### 1. Get an API Key

All plugins call the Redfox API. Get your free `REDFOX_API_KEY` at:

**https://redfox.hk/settings/api-keys?source=github**

See [docs/API_KEY.md](docs/API_KEY.md) for details.

### 2. Install on Your Platform

<details>
<summary><b>Claude Code</b></summary>

```bash
# Add this repo as a marketplace
/plugin marketplace add redfox-data/redfox-agent-plugins

# Install a plugin
/plugin install youtube-video-downloader@redfox-agent-plugins
```
</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
codex plugin marketplace add redfox-data/redfox-agent-plugins
codex plugin install youtube-video-downloader
```

Or clone manually:

```bash
git clone https://github.com/redfox-data/redfox-agent-plugins.git
cp -R redfox-agent-plugins/plugins/youtube-video-downloader ~/.codex/plugins/
```
</details>

<details>
<summary><b>Cursor</b></summary>

Install via the [Cursor Plugin Marketplace](https://cursor.com/marketplace) (search "Redfox"), or manually:

```bash
git clone https://github.com/redfox-data/redfox-agent-plugins.git
cp -R redfox-agent-plugins/plugins/youtube-video-downloader ~/.cursor/plugins/
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

```bash
git clone https://github.com/redfox-data/redfox-agent-plugins.git
cd redfox-agent-plugins/plugins/youtube-video-downloader
gemini extensions install .
```
</details>

Full instructions: [docs/INSTALL.md](docs/INSTALL.md).

### 3. Configure Your API Key

Export it in your shell profile:

```bash
export REDFOX_API_KEY="your-key-here"
```

Each platform also supports declaring the key in its plugin settings (Cursor `variables`, Gemini `settings`). See [docs/API_KEY.md](docs/API_KEY.md).

## Repository Layout

```
redfox-agent-plugins/
├── .claude-plugin/marketplace.json    # Claude Code marketplace manifest
├── .agents/plugins/marketplace.json   # OpenAI Codex marketplace manifest
├── .cursor-plugin/marketplace.json    # Cursor marketplace manifest
├── plugins/
│   └── <plugin-name>/
│       ├── plugin.json                # Agent Plugins v1.0.0 (universal)
│       ├── .claude-plugin/plugin.json # Claude Code manifest
│       ├── .codex-plugin/plugin.json  # Codex manifest
│       ├── .cursor-plugin/plugin.json # Cursor manifest
│       ├── gemini-extension.json      # Gemini CLI manifest
│       ├── assets/logo.svg
│       └── skills/<plugin-name>/
│           ├── SKILL.md               # Agent Skills spec (English)
│           ├── README.md / README.zh.md
│           └── scripts/
├── docs/                              # Install & API key guides
├── scripts/validate.py                # Repo validation (used by CI)
└── .github/workflows/validate.yml     # CI
```

## Standards

- [Agent Skills Specification](https://agentskills.io/specification) — `SKILL.md` with YAML frontmatter, progressive disclosure
- [Agent Plugins v1.0.0](https://agent-plugins.org) — universal `plugin.json` + per-platform manifests

## Contributing

1. Fork this repo and create `plugins/<your-plugin>/` following the layout above
2. Run `python3 scripts/validate.py` locally — it must pass
3. Open a PR; CI will validate manifests and frontmatter automatically

## License

[MIT](LICENSE) © Redfox Data

## Support

- Website: https://redfox.hk
- Skills directory: https://redfox.hk/skills
- Email: support@redfox.hk
