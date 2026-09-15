# Overseas Trending Search

> Cross-platform trending search across X, TikTok and YouTube in one query

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)
[![Agent Plugins v1.0.0](https://img.shields.io/badge/Agent%20Plugins-v1.0.0-blue)](https://agent-plugins.org)

**Powered by [Redfox Data](https://redfox.hk)** — this plugin works across **Claude Code / OpenAI Codex / Cursor / Gemini CLI** and any client conforming to the [Agent Plugins](https://agent-plugins.org) or [Agent Skills](https://agentskills.io) open standards.

---

## What It Does

Search any keyword (Chinese/English/other) across X (Twitter), TikTok and YouTube at once. Returns each platform's Top N trending posts in a unified list. Language-aware ranking. Grouped terminal table + CSV export + interactive HTML report (card/table views).

## Installation

### 1. Get Your Redfox API Key

Sign up at **<https://redfox.hk/settings/api-keys?source=agent-plugins>** and copy your API key (starts with `ak_` or `ark_`).

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
/plugin install overseas-trending-search@redfox-agent-plugins
```
</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
codex plugin marketplace add redfox-data/redfox-agent-plugins
codex plugin add overseas-trending-search@redfox-agent-plugins
```
</details>

<details>
<summary><b>Cursor</b></summary>

1. Open **Customize** in the sidebar
2. Search for `overseas-trending-search` (or add the marketplace repo URL first)
3. Click **Install**
</details>

<details>
<summary><b>Gemini CLI / Antigravity</b></summary>

```bash
gemini extensions install https://github.com/redfox-data/redfox-agent-plugins --path plugins/overseas-trending-search
# or with Antigravity:
agy plugin install https://github.com/redfox-data/redfox-agent-plugins/plugins/overseas-trending-search
```
</details>

<details>
<summary><b>Any Agent Skills compatible client</b></summary>

Copy the skill folder into your client's skills directory:
```bash
cp -r plugins/overseas-trending-search/skills/overseas-trending-search ~/.agents/skills/
```
Compatible with 30+ clients including Junie, Roo Code, GitHub Copilot, VS Code, OpenHands, Goose, Tabnine, and more. See <https://agentskills.io>.
</details>

## Usage

After installation, just ask your agent naturally:

> Search trending posts about 'AI agents' across X, TikTok, and YouTube

The agent will discover the skill by its description and activate it automatically.

## Directory Structure

```
overseas-trending-search/
├── plugin.json                    # Agent Plugins v1.0.0 universal manifest
├── .claude-plugin/plugin.json     # Claude Code specific
├── .codex-plugin/plugin.json      # OpenAI Codex specific
├── .cursor-plugin/plugin.json     # Cursor specific
├── gemini-extension.json          # Gemini CLI specific
├── assets/logo.svg
└── skills/overseas-trending-search/
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

- Docs: <https://redfox.hk/skills/overseas-trending-search>
- Issues: <https://github.com/redfox-data/redfox-agent-plugins/issues>
- Email: <support@redfox.hk>
