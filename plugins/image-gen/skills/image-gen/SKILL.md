---
name: image-gen
description: AI image generator — powered by the gpt-image-2 model, supports text-to-image and image-to-image editing with batch generation, aspect-ratio and resolution control. Ready to use with a single prompt. Use when the user wants to generate images, create artwork, edit images with reference pictures, or produce AI illustrations.
license: MIT
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

# GPT-image2

Generate high-quality images with OpenAI's latest **gpt-image-2** model. Paste a prompt and go.

> **Skill highlights**
>
> - Batch generation from the command line with parameterized aspect-ratio and resolution-tier control
> - Text-to-image + image-to-image dual modes — one `--image` flag enables editing mode (up to 2 reference images)

---

## Overview

- **Text-to-image**: enter a prompt, get a brand-new image
- **Image-to-image**: upload reference images (max 2) + a prompt to edit and generate from the originals
- **Model**: gpt-image-2 (OpenAI's latest image model)
- **Endpoints**: Redfox v2 `gptImage2Submit` / `gptImage2Result`
- **Output format**: PNG (fixed by the v2 API)
- **Aspect ratios**: `1:1` / `3:2` / `2:3` / `4:3` / `3:4` / `5:4` / `4:5` / `16:9` (default) / `9:16` / `2:1` / `1:2` / `21:9` / `9:21`
- **Resolution tiers**: `1k` / `2k` (default) / `4k`
- **Batch generation**: up to 4 images per call (v2 API limit)
- **Legacy pixel-format compatibility**: old styles like `1792x1024` are still accepted and auto-mapped to aspect ratio + tier internally

---

## Usage

### Text-to-image — generate from a text prompt

```bash
# Basic generation (default 16:9 + 2k)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "An orange cat sitting on a windowsill watching the sunset"

# Landscape 4k HD
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "futuristic city skyline" --size 16:9 --resolution 4k

# Vertical social-media cover (3:4 + 2k)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "product cover, minimal style" --size 3:4 --resolution 2k

# Square 1k quick tier
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "minimalist cat logo, flat design" --size 1:1 --resolution 1k

# Batch of 4 (v2 API limit)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "icon set, flat style" -n 4

# Legacy pixel style (auto-mapped to 16:9 + 1k)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "cyberpunk street" --size 1792x1024
```

### Image-to-image — edit with reference images

```bash
# Single reference image (auto-uploaded to OSS → task submitted)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "Make the cat white and change the background to a starry sky" --image ~/Pictures/cat.png

# Two reference images (v2 API supports up to 2)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "Blend the styles of both images" --image ref1.png --image ref2.jpg

# Use a URL reference directly (skips the upload step)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "Replace the poster's subject with a wristwatch" --image "https://example.com/poster.jpg"
```

### Other operations

```bash
# Submit only (returns taskId, no waiting)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "complex scene" --no-download

# Query an existing task result
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "" --task-id 5f100fcb8f3c4e3087c6aba93e121f7e

# Custom output directory and filename prefix
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "illustration" -o ~/Pictures/AI --prefix artwork
```

### Arguments

| Argument | Description | Default |
|------|------|--------|
| `prompt` | Generation/editing prompt (required, max 500 characters) | - |
| `--size` | Aspect ratio (e.g. `16:9`); legacy pixel formats (e.g. `1792x1024`) also accepted | `16:9` |
| `--resolution` | Resolution tier: `1k` / `2k` / `4k` | Auto-matched for pixel formats; `2k` for aspect ratios |
| `-n, --count` | Number of images (1-4, v2 API max 4) | `1` |
| `--image` | Reference image path or URL (repeatable, max 2) | - |
| `-o, --output-dir` | Output directory | `~/Downloads/RedfoxImages` |
| `--prefix` | Filename prefix | `image` |
| `--no-download` | Submit only, don't wait | - |
| `--task-id` | Query an existing task | - |
| `--api-key` | RedFox API key | - |

**Deprecated arguments (no longer supported by the v2 API — ignored with a warning if passed)**

| Argument | Notes |
|------|------|
| `--quality` | Use `--resolution` instead |
| `--format` | The v2 API always outputs PNG |
| `--bg` / `--background` | Background control no longer supported |
| `--compression` | Compression ratio no longer supported |
| `--fidelity` | Input fidelity control no longer supported |

### Dependencies

| Dependency | Install command |
|------|----------|
| `requests` | `pip3 install requests` |

---

## First-Time Setup

Configure your API key, then run:

```bash
# Set the environment variable
export REDFOX_API_KEY=ak_your_key

# Run
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/assets/imagegen.py" "An orange cat"
```

> Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your API key.
>
> ⚠️ The v2 endpoints are **paid-only** — free account credits cannot be used for this API. If you get error code `3203`, top up paid credits at the [recharge page](https://redfox.hk/dashboard/recharge).

---

## Configuration Options

Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your own API token, then choose any one:

| Method | Description | Command |
|----------|------|------|
| **Environment variable** (recommended) | Set once, works globally | `export REDFOX_API_KEY=ak_your_key` |
| **CLI argument** | One-off, per invocation | `python3 "{SKILL_DIR}/assets/imagegen.py" "prompt" --api-key ak_your_key` |
| **Config file** | Persisted across sessions | `mkdir -p ~/.redfox/apis && echo '{"api_key":"ak_your_key"}' > ~/.redfox/apis/redfox.json` |

---

## API Specification (v2)

### Submit task

`POST https://redfox.hk/story/api/parseWork/imageGen/gptImage2Submit`

Headers: `REDFOX_API_KEY: ak_xxx` + `Content-Type: application/json`

Request body:

```json
{
  "prompt": "Replace the poster's subject with a wristwatch",
  "resolution": "2k",
  "size": "16:9",
  "n": 2,
  "referenceImages": ["https://example.com/poster.jpg"]
}
```

Response: `data.taskId` — used for polling.

### Query result

`POST https://redfox.hk/story/api/parseWork/imageGen/gptImage2Result`

Request body: `{"taskId": "..."}`

Key response fields:

| Field | Description |
|------|------|
| `data.status` | `completed` / `processing` / `queued` / `failed` |
| `data.progress` | Generation progress 0-100 |
| `data.imageUrls` | Result URL array (count matches `n`) |
| `data.failReason` | Failure reason (null on success) |
| `data.model` | Model used (`gpt-image-2`) |
| `data.resolution` / `data.size` | Actual tier and aspect ratio used |

---

## FAQ

**Q: What makes this skill special?**
A: Direct command-line access to gpt-image-2 with batch generation, aspect-ratio and resolution-tier control, and image-to-image editing (up to 2 reference images).

**Q: How long does one image take?**
A: Usually 10-60 seconds; the `4k` tier or complex scenes can take longer. The script polls automatically and shows progress.

**Q: What's the difference between the new `resolution` and the old `quality`?**
A: `resolution` is the resolution tier (`1k`/`2k`/`4k`) — it directly determines output sharpness and generation time. The old `quality` argument is deprecated and ignored.

**Q: Why did `--size` change from pixels to aspect ratios?**
A: The v2 `gptImage2Submit` API's `size` field is an aspect ratio (e.g. `16:9`). For backward compatibility the script still accepts pixel styles like `1792x1024` and maps them internally to aspect ratio + recommended tier.

**Q: How many reference images can image-to-image take?**
A: The v2 API allows up to 2. Pass `--image` multiple times; extras are truncated with a warning.

**Q: Why does the call return error code 3203?**
A: The v2 endpoints are paid-only — free credits cannot be used. Top up paid credits at [redfox.hk/dashboard/recharge](https://redfox.hk/dashboard/recharge).

**Q: How do I get an API key?**
A: Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your own API token.

**Q: Which image formats are supported as references?**
A: PNG, JPEG and WebP — local files or HTTP(S) URLs.

**Q: Is there a prompt length limit?**
A: Prompts are limited to 500 characters; longer prompts are blocked with a warning.
