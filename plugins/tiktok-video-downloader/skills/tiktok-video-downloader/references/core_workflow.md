# Core Workflow

> **Note:** `{SKILL_DIR}` = absolute path of this skill directory (parent of references/) — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

## Execution Rules

- **When the user provides a valid TikTok video link**: run the parsing flow directly — no extra confirmation or follow-up questions
- **When no link is provided**: ask the user for a TikTok video link
- **When the provided link is not a TikTok link**: prompt "Please provide a valid TikTok video link" and stop

## Script Invocation

### Single link

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.tiktok.com/@user/video/xxxxx"
```

### Batch links (space separated)

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.tiktok.com/@user/video/111" "https://www.tiktok.com/@user/video/222" "https://vm.tiktok.com/abc/"
```

### CLI Arguments

| Argument | Description |
|------|------|
| `urls` (positional, required) | TikTok video link(s) — multiple allowed, space separated |
| `--api-key` | API key (format ark_xxx; falls back to env var or config file) |
| `--save-key` | Save the provided API key to the config file |
| `--json` | Print the full API response as JSON |

## API Key Configuration

Priority: CLI argument > environment variable > config file

| Method | Command |
|------|------|
| **Environment variable** (recommended) | `export REDFOX_API_KEY=ark_your_key` |
| **CLI argument** | `python3 "{SKILL_DIR}/scripts/downloader.py" "<url>" [<url>...] --api-key ark_your_key` |
| **Config file** | `echo '{"api_key":"ark_your_key"}' > ~/.redfox/apis/redfox.json` |

### First-Time Setup

```bash
# Set the environment variable
export REDFOX_API_KEY=ark_your_key

# Parse the video and get the download link
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/downloader.py" "https://www.tiktok.com/@user/video/xxxxx"
```

> Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your API key.

## API Call Details

- **Endpoint**: `https://redfox.hk/story/api/parseWork/videoDownload/tiktok`
- **Method**: POST, Content-Type: application/json, Header: X-API-KEY
- **Request body**: `{"url": "<link>", "source": "<base>-<channel>"}` — the channel suffix (`claude`/`codex`/`cursor`/`gemini`/`github`) is resolved automatically at runtime for per-platform usage stats
- **Success check**: response code starts with 2 (e.g. 200, 2000)
- **Error codes**: 3106 = missing key, 3107 = invalid key, 400 = bad parameters
- **Link expiry**: returned download links are valid for about 5 minutes

## Output Format

On success, printed in order:
1. Content description (full original text)
2. Resource list (type / duration / download URL / cover / audio URL)
3. Expiry reminder

In batch mode, a success/failure summary is printed at the end.
