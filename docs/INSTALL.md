# Installation Guide

All 10 Redfox plugins can be installed on four platforms from this single repository.

## Prerequisites

- A Redfox API key — see [API_KEY.md](API_KEY.md)
- Python 3.9+ (for plugins that run local scripts)

## Claude Code

```bash
# 1. Add the marketplace (once)
/plugin marketplace add redfox-data/redfox-agent-plugins

# 2. Browse available plugins
/plugin marketplace browse redfox-agent-plugins

# 3. Install
/plugin install youtube-video-downloader@redfox-agent-plugins

# 4. Restart Claude Code if prompted, then just ask:
#    "Download this YouTube video: https://www.youtube.com/watch?v=..."
```

Manage installed plugins with `/plugin` (enable/disable/uninstall).

## OpenAI Codex

```bash
codex plugin marketplace add redfox-data/redfox-agent-plugins
codex plugin install youtube-video-downloader
```

Manual install (works on any Agent Plugins v1.0.0 compatible client):

```bash
git clone https://github.com/redfox-data/redfox-agent-plugins.git
cp -R redfox-agent-plugins/plugins/youtube-video-downloader ~/.codex/plugins/
```

## Cursor

1. Open Cursor → Settings → Plugins (or visit the [Cursor Marketplace](https://cursor.com/marketplace) and search "Redfox")
2. Install the plugin
3. Fill in `REDFOX_API_KEY` when prompted (Cursor reads the `variables` schema from `.cursor-plugin/plugin.json`)

Manual install:

```bash
git clone https://github.com/redfox-data/redfox-agent-plugins.git
cp -R redfox-agent-plugins/plugins/youtube-video-downloader ~/.cursor/plugins/
```

## Gemini CLI

```bash
git clone https://github.com/redfox-data/redfox-agent-plugins.git
cd redfox-agent-plugins/plugins/youtube-video-downloader
gemini extensions install .
```

Gemini CLI will prompt for the settings declared in `gemini-extension.json`
(including `REDFOX_API_KEY`) on first run.

## Verify Installation

After installing, ask your agent something like:

> "Download the video from https://www.youtube.com/watch?v=dQw4w9WgXcQ"

If the API key is missing, every skill prints a sign-up link:
`https://redfox.hk/settings/api-keys?source=<platform>`

## Troubleshooting

| Symptom | Fix |
|---|---|
| `REDFOX_API_KEY not set` | Export the key in your shell profile, or fill it in the platform's plugin settings |
| Plugin not discovered | Restart the client; confirm the manifest paths above exist |
| `python3: command not found` | Install Python 3.9+ and ensure it is on PATH |
| Network errors | The Redfox API is hosted at `redfox.hk`; check firewall/proxy settings |
