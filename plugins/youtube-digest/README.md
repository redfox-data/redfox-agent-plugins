# YouTube Transcript Extractor

> Extract YouTube video transcripts as clean text or Excel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)
[![Agent Plugins v1.0.0](https://img.shields.io/badge/Agent%20Plugins-v1.0.0-blue)](https://agent-plugins.org)

**Powered by [Redfox Data](https://redfox.hk)** — this plugin works across **Claude Code / OpenAI Codex / Cursor / Gemini CLI** and any client conforming to the [Agent Plugins](https://agent-plugins.org) or [Agent Skills](https://agentskills.io) open standards.

---

## What It Does

Paste any YouTube URL or video ID and extract the full transcript. Chinese subtitles preferred; falls back to English with auto-translation to Chinese if needed. Output as clean text without timestamps by default, or as a timestamped table exportable to Excel.

## Installation

### 1. Get Your Redfox API Key

Sign up at **<https://redfox.hk/settings/api-keys?source=agent_plugins>** and copy your API key (starts with `ak_` or `ark_`).

### 2. Configure the API Key

Choose one method:

**Method A — Environment variable (recommended):**

```bash
export REDFOX_API_KEY=ak_your_key_here
```

**Method B — Config file:**

```bash
mkdir -p ~/.redfox && echo '{"api_key":"ak_your_key_here"}' > ~/.redfox/config.json
```

**Method C — Per-command flag:**

```bash
python3 scripts/xxx.py "<args>" --api-key ak_your_key_here
```

### 3. Install the Plugin

Pick your client:

<details>
<summary><b>Claude Code</b></summary>

```
/plugin marketplace add redfox-data/redfox-agent-plugins
/plugin install youtube-digest@redfox-agent-plugins
```

</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
codex plugin marketplace add redfox-data/redfox-agent-plugins
codex plugin add youtube-digest@redfox-agent-plugins
```

</details>

<details>
<summary><b>Cursor</b></summary>

1. Open **Customize** in the sidebar
2. Search for `youtube-digest` (or add the marketplace repo URL first)
3. Click **Install**
</details>

<details>
<summary><b>Gemini CLI / Antigravity</b></summary>

```bash
gemini extensions install https://github.com/redfox-data/redfox-agent-plugins --path plugins/youtube-digest
# or with Antigravity:
agy plugin install https://github.com/redfox-data/redfox-agent-plugins/plugins/youtube-digest
```

</details>

<details>
<summary><b>Any Agent Skills compatible client</b></summary>

Copy the skill folder into your client's skills directory:

```bash
cp -r plugins/youtube-digest/skills/youtube-digest ~/.agents/skills/
```

Compatible with 30+ clients including Junie, Roo Code, GitHub Copilot, VS Code, OpenHands, Goose, Tabnine, and more. See <https://agentskills.io>.

</details>

## Usage

After installation, just ask your agent naturally:

> Extract the transcript of this YouTube video: https://www.youtube.com/watch?v=xxxxx

The agent will discover the skill by its description and activate it automatically.

## Directory Structure

```
youtube-digest/
├── plugin.json                    # Agent Plugins v1.0.0 universal manifest
├── .claude-plugin/plugin.json     # Claude Code specific
├── .codex-plugin/plugin.json      # OpenAI Codex specific
├── .cursor-plugin/plugin.json     # Cursor specific
├── gemini-extension.json          # Gemini CLI specific
├── assets/logo.svg
└── skills/youtube-digest/
    ├── SKILL.md                   # Agent Skills open standard
    ├── scripts/                   # Executable scripts
    └── README.md / README.zh.md   # Detailed docs
```

## Requirements

- Python 3.9+ (for script execution)
- Network access to `redfox.hk` API
- Valid `REDFOX_API_KEY`

## License

MIT © [Redfox Data](https://redfox.hk)

## Support

- Docs: <https://redfox.hk/skills/youtube-digest>
- Issues: <https://github.com/redfox-data/redfox-agent-plugins/issues>
- Email: <support@redfox.hk>
