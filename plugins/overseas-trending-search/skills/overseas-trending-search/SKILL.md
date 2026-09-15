---
name: overseas-trending-search
description: Cross-platform overseas trending search — search any keyword (Chinese/English/other) across X (Twitter), TikTok and YouTube at once, get each platform's Top N trending posts in a unified list (platform/title/author/views/likes/comments/date/link). Language-aware ranking (Chinese keyword → Chinese content first, English → English first, other languages as fallback). Grouped terminal table + CSV export + interactive HTML report (card/table views). Use for trend tracking, cross-platform comparison, competitor sentiment monitoring, topic research, content inspiration.
license: MIT
compatibility: Requires Python 3.9+ and network access to redfox.hk API
metadata:
  author: Redfox Data
  version: "1.3.0"
  category: data-analysis
  display-name-en: Overseas Trending Search
  homepage: https://redfox.hk/skills/overseas-trending-search
  permissions: "network, filesystem-write"
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

# Overseas Trending Search

Enter any keyword (in any language) and search trending content across X / TikTok / YouTube in one shot. Each platform's Top N (default 5) is picked by likes/views/comments/publish time, output as a unified list: platform, title, author, views, likes, comments, publish time, link.

> API requests carry a `ChinaTrendingDigest-<Channel>` attribution tag. An API key is required — pass it via the REDFOX_API_KEY environment variable or the --api-key argument.
> The architecture uses the platform-adapter pattern: adding a platform (e.g. YouTube) only requires a new adapter file — zero changes to the main flow.

---

## Use Cases

| Scenario | Example |
|------|------|
| **Daily trend tracking** | Run "AI" every day to see the hottest content across all three platforms |
| **Cross-platform comparison** | Compare heat and content formats for the same keyword across X / TikTok / YouTube |
| **Topic & event tracking** | Search "new energy,EV" to track a topic's cross-platform spread |
| **Competitor / sentiment monitoring** | Search a brand or product name to see real overseas discussions and viral feedback |
| **Content inspiration** | Export CSV to build a topic library and run data analysis |
| **Account content mining** | TikTok side supports drilling into an author's video list (userAwemeList) |

---

## Usage

```bash
# Basic: single keyword (default last 24 hours, sorted by views desc)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "AI"

# Multiple keywords (comma-separated)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "artificial intelligence,AI agent"

# Widen the time window to the last 3 days (TikTok trending posts are often older — recommended)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "AI" --days 3

# Run specific platforms only
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "AI" --platforms tiktok

# Sort by publish time
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "AI" --sort time

# Sort by likes / adjust per-platform item count (default 5)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "AI" --sort likes --top 10

# CSV only / don't auto-open the browser
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/digest.py" "AI" --csv-only --no-open
```

CSV / HTML files are saved to `~/Downloads/RedfoxOverseasTrending/` by default.

---

## Result Presentation Rules

When presenting results to the user, the following fields are **required**:

| Field | Description |
|------|------|
| Platform | X / TikTok / YouTube (with platform badge color) |
| Title | Tweet/video caption excerpt — show the first 20 characters (full text on hover in the HTML table) |
| Author | Author display name |
| Views | Abbreviated with k/M (e.g. 473.2k), shown after the author |
| Likes | Abbreviated with k/M (e.g. 629.1k) |
| Comments | Same as above |
| Publish time | `YYYY-MM-DD HH:mm` |
| Link | Clickable link to the original post |

Platform status must be stated before the results: when a platform's upstream fails, degrade gracefully and annotate it in the report without affecting other platforms.

- Item limits: each platform returns at most `--top` N items (default 5), sorted within the platform group by the `--sort` metric descending; both the terminal and the HTML group by platform.
- Language priority tiering: with Chinese keywords, Chinese content ranks first within each platform group; with English keywords, English content ranks first; other languages fill in as fallback. Within a tier, items still sort by the chosen metric descending.
- The HTML report supports card/table dual views; the table view includes all fields (likes/comments/views/shares).
- YouTube likes/comments are enriched per item via the videoDetail endpoint (full coverage of the 20 search results by default; localized count strings are parsed to integers).

---

## Arguments

| Argument | Description | Default |
|------|------|--------|
| `keywords` | Keywords in any language, comma-separated for multiple (positional) | — |
| `--days` | Time window: last N days (0=unlimited) | `1` |
| `--platforms` | Platform list: any combination of `x,tiktok,youtube` | `x,tiktok,youtube` |
| `--sort` | Sort by: `views` / `likes` / `comments` / `time` | `views` |
| `--top` | Max items per platform (0=unlimited) | `5` |
| `--output-dir` | Output directory | `~/Downloads/RedfoxOverseasTrending` |
| `--api-key` | Explicit RedFox API key | — |
| `--csv-only` | Generate CSV only, no HTML | — |
| `--no-open` | Don't auto-open the browser | — |

---

## API Key Configuration

Choose any one way to configure your personal key:

| Method | Command |
|------|------|
| Environment variable (recommended) | `export REDFOX_API_KEY=ak_your_key` |
| CLI argument | `--api-key ak_your_key` |
| Config file | `echo '{"api_key":"ak_your_key"}' > ~/.redfox/apis/redfox.json` |

Sign up at: [redfox.hk](https://redfox.hk/settings/api-keys?source=github)

---

## Architecture

```
scripts/
├── digest.py            # Main orchestrator: keyword×platform collection → time filter → sort → output
├── config.py            # RedFox gateway URLs, key loading (three-tier priority), channel attribution
└── sources/             # Platform adapters (a new platform = one new file + registration in __init__)
    ├── base.py          # BaseSource: unified schema + incremental-backoff retries
    ├── x_source.py      # X: search/tweetDetail/tweetComments
    ├── tiktok_source.py # TikTok: searchVideo (one request carries likes/comments)
    └── youtube_source.py# YouTube: searchVideo list + videoDetail for likes/comments
```

Unified record schema: `platform / title / url / author / likes / comments / views / publish_ts / publish_time / keyword / shares`.

### Platform endpoint status (verified 2026-07)

| Platform | Endpoints | Status |
|------|------|------|
| X | search / tweetDetail / tweetComments | ✅ All working; search requires `searchType` (Top/Latest) — missing it triggers a misleading 3203 |
| TikTok | searchVideo / awemeDetail / userAwemeList | ✅ All working; searchVideo carries full engagement data |
| YouTube | searchVideo / videoDetail / videoComments | ✅ All working; searchVideo returns views + relative publish time, likes/comments enriched via videoDetail (Top 10) |

---

## Dependencies

```bash
pip3 install requests
```

---

## FAQ

**Q: X search returns a 3203 error?**
A: The X search endpoint requires `searchType` (`Top` trending / `Latest` newest) — when missing, RedFox returns a misleading 3203 "X capability call failed". This skill always sends the parameter; note that calling tweetDetail with an expired/invalid tweetId also returns 3203.

**Q: Does TikTok search need detail calls to fill in data?**
A: No. One searchVideo request returns likes/comments/views/shares and publish time — enough for daily digests.

**Q: Where do YouTube's likes/comments come from?**
A: The searchVideo list endpoint only returns views; likes/comments require per-item videoDetail calls. The skill enriches all 20 search results by default (`detail_top` in `youtube_source.py` can be lowered to save credits), so every video has real like/comment counts; a remaining 0 means the video genuinely has none. YouTube does not expose share counts publicly, so the shares column is always 0.

**Q: How many items per platform?**
A: By default each platform returns its Top 5 by the sort metric (likes/views/comments/publish time); adjust with `--top N` (0=unlimited). Platforms are grouped independently and sorted within groups, without affecting each other.

**Q: Why is there no TikTok content with default arguments?**
A: TikTok searchVideo returns trending videos whose publish times are often days or months old, so the default `--days 1` (last 24 hours) filters them all out. To see TikTok trending content, add `--days 0` or `--days 7`; when filtering, the terminal reports the excluded count per platform.

**Q: I searched a Chinese keyword — why is Japanese content on X ranked lower?**
A: The skill has built-in language priority tiering: with Chinese keywords, Chinese content ranks first within each platform group, then English, with Japanese and other languages as fallback (this resolves ambiguities like "南海" matching Japan's "南海電鉄"); English keywords work the same way. Language detection is based on title character sets (Han/kana/Hangul/Latin) with no third-party dependencies.

**Q: Want a daily scheduled run?**
A: Ask your AI client to register a scheduled task that runs `digest.py` and generates the report automatically every day.
