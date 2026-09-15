---
name: seedance-video-gen
description: AI video generator powered by the Seedance 2.0 model — enter a prompt and get an MP4 video with synchronized audio. Supports text-to-video, resolution/aspect-ratio/duration control and preset virtual characters. Use when the user wants Seedance video generation, AI video, or text-to-video.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

# Seedance2.0

## Introduction

Seedance2.0 is an AI video generation tool based on Volcano Ark's **Seedance 2.0** model. The redfox.hk platform wraps the complex ARK API authentication flow, so you can **generate a video with a single command**.

> **Skill highlights**
>
> - Parameterized command-line control of resolution, aspect ratio and duration
> - Text-to-video + virtual-character reference dual modes

### Why use this skill?

- **For developers**: no need to apply for Volcano Ark whitelisting, configure AK/SK, or integrate ARK auth — one command does it all
- **For creators**: no subscriptions or credit cards — pay per use, walk away when done
- **For everyone**: extremely low barrier — sign up and generate, no API plumbing required

### Who is it for?

Social media creators, product managers, content operators, AI enthusiasts — anyone who needs to turn copy into video fast.

---

## Features

### Core capabilities

- **Text-to-video**: enter a description in any language, Seedance 2.0 generates an MP4 video with synchronized audio
- **Parameter control**: resolution (480p/720p/1080p), aspect ratio (7 options incl. 16:9/9:16), duration (4-15 seconds)
- **Virtual characters**: reference preset virtual characters via the `asset://` format — no need to upload real face material
- **Task management**: get a taskId after submission, query progress and results any time
- **Auto polling**: the script polls task status (queued/generating/succeeded) automatically — no manual waiting

### Technical highlights

- Underlying model: `doubao-seedance-2-0-260128`
- Synchronized audio: video and sound generated together
- Last-frame extraction: return the final frame for continuous multi-segment video generation
- Random seed: set a seed value for reproducible results
- HTTPS: end-to-end SSL verification

### Arguments

| Argument | Description | Default |
|------|------|--------|
| `prompt` | Video prompt (required, any language) | — |
| `--resolution` | Resolution: `480p` / `720p` / `1080p` | `720p` |
| `--ratio` | Aspect ratio: `16:9` / `4:3` / `1:1` / `3:4` / `9:16` / `21:9` / `adaptive` | `16:9` |
| `--duration` | Duration (seconds): 4-15 or -1 (smart) | `5` |
| `--seed` | Random seed: -1 to 2147483647 | `-1` |
| `--no-audio` | Disable audio | Audio on by default |
| `--watermark` | Add watermark | Off by default |
| `--return-last-frame` | Return the last-frame image URL | Off by default |
| `--image-url` | Reference image URL (`asset://` format) | — |
| `-o, --output-dir` | Output directory | `~/Downloads/RedfoxVideos` |
| `--prefix` | Filename prefix | `video` |
| `--no-download` | Submit only, don't wait | — |
| `--task-id` | Query an existing task | — |

---

## Use Cases

### Case 1: Social media content creation

**Role**: short-video creator / social media operator

**Need**: quickly generate vertical (9:16) video material for TikTok / Instagram / YouTube Shorts

**Command**:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Beauty product showcase, soft lighting, product slowly rotating" --ratio 9:16
```

**Benefit**: cut material production from hours to minutes

---

### Case 2: Product feature demos

**Role**: product manager / founder

**Need**: quickly generate product concept videos for pitches, roadshows or demos

**Command**:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "A smartwatch on a desk, the display cycling through feature screens" --resolution 1080p --duration 8
```

**Benefit**: no professional video production skills needed — copy becomes video

---

### Case 3: Brand content operations

**Role**: content operator / marketer

**Need**: batch-generate brand backdrop videos to pair with copy for promo shorts

**Command**:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Brand-color background, text fading in with a gradient, professional and elegant" --ratio 16:9 --no-audio
```

**Benefit**: boost content throughput with a consistent brand visual style

---

### Case 4: Rapid creative validation

**Role**: designer / creative

**Need**: turn mental imagery into visible video with natural language to validate creative directions

**Command**:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Cyberpunk city night scene, neon lights flickering, raindrops landing on the lens" --duration 6
```

**Benefit**: from idea to video in one command

---

### Case 5: Education & training visuals

**Role**: teacher / trainer

**Need**: turn abstract concepts into visual shorts to improve teaching effectiveness

**Command**:

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Animation of the solar system planets orbiting the sun, each planet labeled with its name" --duration 10
```

**Benefit**: zero-barrier knowledge visualization, no animation skills required

---

## First-Time Setup

Configure your API key, then run:

```bash
# Set the environment variable
export REDFOX_API_KEY=ak_your_key

# Run
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "An orange cat yawning on a windowsill, warm sunlight on its fur"
```

> Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your API key.

---

## Configuration Options

Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your own API key, then choose any one:

| Method | Description | Command |
|----------|------|------|
| **Environment variable** (recommended) | Set once, works globally | `export REDFOX_API_KEY=ak_your_key` |
| **CLI argument** | One-off, per invocation | `python3 "{SKILL_DIR}/scripts/videogen.py" "prompt" --api-key ak_your_key` |
| **Config file** | Persisted across sessions | `mkdir -p ~/.redfox/apis && echo '{"api_key":"ak_your_key"}' > ~/.redfox/apis/redfox.json` |

---

## Installation

### Dependencies

```bash
pip3 install requests
```

### Environment variables

| Variable | Required | Description |
|--------|------|------|
| `REDFOX_API_KEY` | — | API access key for the redfox.hk platform |

---

## User Guide

### Basic usage

#### 1. Enter a prompt to generate a video

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "An orange cat yawning on a windowsill, warm sunlight on its fur"
```

The script submits the task, polls until done (about 3-15 minutes), then downloads to `~/Downloads/RedfoxVideos/`.

#### 2. Check the result

On success the video info and file path are printed:

```
[✓] Video ready: 5s, 720p, 16:9
[✓] Token usage: 108900
[→] Downloading video: video.mp4
[✓] Done!
  /Users/you/Downloads/RedfoxVideos/video.mp4 (2.5 MB)
```

### Advanced usage

#### Vertical short video (TikTok / Instagram)

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Stylish city night scene, neon lights flickering" --ratio 9:16
```

#### HD long video

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Slow motion of waves crashing on rocks" --resolution 1080p --duration 10
```

#### Preset virtual characters

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "A young woman reading quietly in a library" --image-url "asset://female_student_01"
```

For more preset virtual-character IDs, see the Volcano Ark "asset & virtual-character library" documentation.

#### Task management

```bash
# Submit only — prints the taskId and exits immediately
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "complex scene" --no-download

# Query the result later with the taskId
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "ignored" --task-id vg_abc123def456
```

#### Multi-segment continuous video

```bash
# 1. Generate the first segment and capture its last frame
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Opening scene" --return-last-frame

# 2. Feed the returned lastFrameUrl in as the first frame of the next segment
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/videogen.py" "Transition to the second scene" --image-url "<lastFrameUrl from step 1>"
```

### Command cheat sheet

| Command | Function |
|------|------|
| `python3 videogen.py "prompt"` | Basic text-to-video |
| `--ratio 9:16` | Vertical aspect ratio |
| `--resolution 1080p` | HD resolution |
| `--duration 10` | Explicit duration |
| `--no-audio` | Silent video |
| `--watermark` | Add watermark |
| `--seed 42` | Fixed seed for reproducibility |
| `--image-url "asset://..."` | Reference a virtual character |
| `--no-download` | Submit the task only |
| `--task-id <id>` | Query an existing task |
| `--api-key <key>` | Explicit API key |
| `-o ~/Desktop` | Custom output directory |

---

## Architecture

### Directory layout

```
seedance-video-gen/
├── SKILL.md              # Skill definition & docs
└── scripts/              # Tooling
    └── videogen.py       # Main video generation program
```

### Tech stack

| Component | Technology |
|------|------|
| Runtime | Python 3.6+ |
| HTTP library | requests |
| API platform | redfox.hk |
| Underlying model | Volcano Ark Seedance 2.0 (doubao-seedance-2-0-260128) |
| Output format | MP4 |

### Core modules

| Module | Responsibility |
|------|------|
| `get_api_key()` | Three-tier API key resolution: CLI > env var > config file |
| `submit_video_task()` | Builds the content array and submits the generation task |
| `poll_video_result()` | Polls task status (queued/running/succeeded/failed/expired) for up to 20 minutes |
| `download_video()` | Streams the MP4 download with a progress bar |
| `main()` | CLI entry: argument parsing, key validation, submit/query branches |

### Data flow

```
User prompt → submit_video_task() → redfox.hk API → Volcano Ark Seedance 2.0
                                                            ↓
User gets MP4 ← download_video() ← poll_video_result() ← task completion
```

---

## FAQ

### Setup

**Q1: Do I need an API key?**

A: Yes. Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your own API key, then configure it via the `REDFOX_API_KEY` environment variable or the `--api-key` argument.

**Q2: Where does the config file live?**

A: At `~/.redfox/apis/redfox.json`, in the format `{"api_key": "ak_your_key"}`.

**Q3: How do I verify my API key works?**

A: Run `python3 videogen.py "test" --no-download` — if a taskId comes back, you're good.

---

### Usage

**Q4: How long does one video take?**

A: Usually 3-15 minutes; complex scenes can take longer. The script polls automatically for up to 20 minutes.

**Q5: Can I upload my own reference images?**

A: Seedance 2.0 does not support uploading reference images/videos containing real human faces. To specify a character's appearance, describe it in the prompt (e.g. "an Asian woman wearing glasses") or use a preset virtual character `asset://` URL. See the Volcano Ark "asset & virtual-character library" docs for more.

**Q6: Which prompt languages are supported?**

A: Any language — the API handles it automatically.

**Q7: Where are output files saved?**

A: By default to `~/Downloads/RedfoxVideos/video.mp4`; use `-o` to pick a directory.

---

### Troubleshooting

**Q8: What if the task times out?**

A: The script waits up to 20 minutes. On timeout it prints the taskId — you can query and download later with `--task-id`.

**Q9: "API request failed"?**

A: Check your network connection and confirm redfox.hk is reachable. Persistent failures may mean an expired API key or insufficient balance.

**Q10: Video download failed?**

A: Make sure the output directory is writable and the disk has space. If the OSS link expired, re-query with `--task-id` to get a fresh download URL.

---

### Getting help

For anything else, visit [redfox.hk](https://redfox.hk/settings/api-keys?source=github) for platform docs or contact support.
