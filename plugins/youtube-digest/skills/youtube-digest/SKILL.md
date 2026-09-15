---
name: youtube-digest
description: YouTube transcript extractor — paste a YouTube video link or ID and extract the full spoken transcript (captions). Defaults to clean text without timestamps; caption track priority zh,en,asr with automatic translation of non-Chinese captions into Chinese (disable with --no-translate to keep the original language). Results are shown as a table (title/duration/transcript), exportable to Excel, with an optional timestamped version. Use when the user wants to extract a YouTube transcript, turn a video into text, or take video notes/summaries/translations/remixes.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

# YouTube Transcript Extractor

Paste a YouTube video link and extract the full spoken transcript — terminal output + Markdown archive + optional Excel export.

**Supported link formats (the link must contain a video ID):**

- Full URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Short URL: `https://youtu.be/dQw4w9WgXcQ`
- Video ID: `dQw4w9WgXcQ`

**Default behavior (important):**

- Outputs **clean text without timestamps** by default; add `--timestamp` for the timestamped version
- Caption tracks are selected with `zh,en,asr` priority: **if the video has a Chinese caption track it is output directly**; otherwise it falls back to English and **the script auto-translates non-Chinese captions into Chinese** (via Google Translate, batched for efficiency). Add `--no-translate` to keep the original language — recommended for non-Chinese users, e.g. `--language "en" --no-translate`
- Video metadata (title/channel) is fetched automatically, no extra flags needed

> An API key is required — pass it via the REDFOX_API_KEY environment variable or the --api-key argument.
> Transcript source: video caption tracks (manual + auto-generated ASR), selected by language priority with Chinese first; non-Chinese captions are auto-translated to Chinese by the script unless disabled.

---

## Use Cases

Prefer this skill when you need to:

| Scenario | Example |
|------|------|
| **Video to text** | Drop a YouTube link, get the full spoken transcript |
| **Study notes** | Extract a tutorial/talk transcript, then let the AI summarize it into chapter notes |
| **Content remixing** | Extract an English transcript → AI translation/rewrite → blog or social post |
| **Podcast/interview archiving** | Extract the full interview text and export to Excel for archiving |
| **Competitor content analysis** | Batch-extract transcripts from peer channels, analyze hooks and structure |
| **Topic research** | Extract the transcript first to quickly decide whether a video deserves a deep watch |

---

## Usage

```bash
# Basic extraction (default: no timestamps + metadata fetched automatically)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Short links and plain video IDs also work
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "https://youtu.be/dQw4w9WgXcQ"
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "dQw4w9WgXcQ"

# Keep the original language (recommended for English videos)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --language "en" --no-translate

# Timestamped version (easy to locate positions in the original video)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --timestamp

# Also export Excel (four columns: title/duration/video URL/transcript)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --excel

# Timestamps + Excel (Excel content matches the current mode)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --timestamp --excel

# Raw JSON / skip saving / skip metadata
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --json
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --no-save
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/extract.py" "URL" --no-metadata
```

Terminal output: video summary (title/language/segment count/total duration) + full transcript text.

Markdown archives are saved to `~/Downloads/RedfoxYoutubeDigest/` by default, named `{videoId}_{timestamp}.md`, with a video info header table + full text; Excel (.xlsx) goes to the same directory.

---

## Workflow (the AI must follow this)

1. **Extract**: run the script to get the transcript
2. **Table display**: present the result as a table per the "Result Display Rules" below (title/duration/transcript), showing the **full transcript text** in the transcript column (no timestamps; non-Chinese captions already auto-translated unless --no-translate)
3. **Closing question**: after displaying, **always ask the user**:
   > "Would you like the timestamped version (easy to locate positions in the video)? I can also export it to Excel."
   - User wants timestamps → re-run with `--timestamp` and display
   - User wants Excel → re-run with `--excel` (add `--timestamp` too if requested) and give the file path

> Note: the script auto-translates non-Chinese captions into Chinese by default. If the user explicitly wants the original text, re-run with `--no-translate`.

---

## Result Display Rules

When showing extraction results to the user, this table is **mandatory** — no fields may be omitted:

| # | Field | Description |
|------|------|------|
| 1 | Title | Video title (from metadata) |
| 2 | Duration | Format `MM:SS` or `HH:MM:SS` |
| 3 | Transcript | **Full text without timestamps** (non-Chinese captions auto-translated to Chinese unless disabled) |

**Display example:**

```
| Title | Duration | Transcript |
|------|------|----------|
| Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) | 03:31 | We're no strangers to love / You know the rules and so do I / …(full text) |
```

- Transcript column: multi-paragraph text is joined inside the cell with "/" or line breaks — keep it complete, never truncate
- Append one archive-info line after the table: `Archived: ~/Downloads/RedfoxYoutubeDigest/dQw4w9WgXcQ_xxx.md`

---

## Arguments

| Argument | Description | Default |
|------|------|--------|
| `video_url` | YouTube video link (full URL / short URL / video ID, must contain a video ID; required positional) | — |
| `--language` | Caption language priority, comma separated (Chinese track first; `asr` = auto-generated captions fallback; track selection only, no translation at API level) | `zh,en,asr` |
| `--timestamp` | Output transcript with `[MM:SS]` timestamps | **No** timestamps by default |
| `--excel` | Also export Excel (.xlsx, four columns: title/duration/video URL/transcript) | Not exported |
| `--no-metadata` | Skip fetching video metadata | Fetched by default (title/channel) |
| `--json` | Print the raw JSON response to the terminal | — |
| `--no-save` | Do not save the Markdown file | Saved automatically |
| `--output-dir` | Output directory | `~/Downloads/RedfoxYoutubeDigest` |
| `--no-translate` | Disable auto translation, keep captions in the original language | Auto-translate **on** by default |
| `--api-key` | RedFox API key | — |

---

## API Key Configuration

Configure your personal key in any of these ways:

| Method | Command |
|------|------|
| Environment variable (recommended) | `export REDFOX_API_KEY=ak_your_key` |
| CLI argument | `--api-key ak_your_key` |
| Config file | `echo '{"api_key":"ak_your_key"}' > ~/.redfox/apis/redfox.json` |

Sign up: [redfox.hk](https://redfox.hk/settings/api-keys?source=github)

---

## Features

- **Three input formats**: full URL, `youtu.be` short link, plain video ID — detected automatically
- **Clean text by default**: no timestamps, directly readable and ready to feed to an AI; switch anytime with `--timestamp`
- **Auto translation**: non-Chinese captions are translated to Chinese (via Google Translate); keep the original with `--no-translate`
- **Table delivery**: title/duration/transcript in one table — everything at a glance
- **Excel export**: `--excel` exports xlsx with wrapped text and fitted column widths, ready for archiving and sharing
- **Chinese-track priority**: tracks selected by `zh,en,asr`; Chinese captions output directly, otherwise English fallback + auto translation
- **Robust retries**: network errors / bad status codes / empty data retried with incremental delays (0.5s→1.0s); rate limits (3108) auto-wait 5 seconds and retry
- **AI friendly**: chains naturally into summarization, translation, rewriting and publishing workflows

---

## Dependencies

```bash
pip3 install requests openpyxl deep-translator
```

(`openpyxl` is only needed for Excel export; `deep-translator` only for auto translation — missing packages degrade the corresponding feature gracefully, everything else keeps working)

---

## FAQ

**Q: Does the default output have timestamps?**
A: No. The default is clean text; add `--timestamp` for the `[MM:SS]` version. After extraction the AI will also ask whether you want it.

**Q: Can I get the transcript in the video's original language?**
A: Yes. Add `--no-translate` (optionally with `--language "en"` to force the English track). By default non-Chinese captions are auto-translated to Chinese, since this skill was built for Chinese creators.

**Q: What's inside the Excel file?**
A: Four columns — title, duration, video URL, transcript. The transcript matches the current mode: with `--timestamp` the Excel contains timestamps, otherwise clean text.

**Q: Why did extraction fail with "the video may have no captions"?**
A: Transcripts come from caption tracks. Videos with no captions at all (including auto-generated) cannot be extracted; some restricted/private videos are also unsupported.

**Q: What do link errors mean?**
A: An invalid link returns `Invalid YouTube URL or video ID` (no credits deducted) — check that the link contains a valid video ID. Invalid keys (3106/3107) mean the API key configuration is wrong. Rate limits (3108) auto-wait and retry.

**Q: What can I do with the transcript?**
A: Let the AI summarize it into notes, translate it, rewrite it into an article, or feed it into any downstream content workflow.

**Q: Out of quota?**
A: Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your token.
