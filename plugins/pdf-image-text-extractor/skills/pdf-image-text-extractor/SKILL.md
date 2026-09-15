---
name: pdf-image-text-extractor
description: PDF & image OCR text extractor — extract text from PDFs and images with original format preserved. Scanned PDFs auto-rendered for AI vision recognition (no tesseract/rapidocr needed); tables structured via pymupdf find_tables (no pdfplumber needed); supports batch directory processing (PDF + images in one shot). Use when extracting text from PDFs or images, performing OCR, processing scanned documents, extracting PDF tables, batch-processing folders, or converting to editable text.
license: MIT
compatibility: Requires Python 3.9+ with pymupdf>=1.23.0 and requests>=2.28.0
metadata:
  author: Redfox Data
  version: "2.1.0"
  display-name-en: PDF & Image Text Extractor
  homepage: https://redfox.hk/skills/pdf-image-text-extractor
  dependency-python: "pymupdf>=1.23.0, requests>=2.28.0"
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

# PDF & Image Text Extractor

## Task Goals

- This skill: recognizes and extracts text from user-uploaded images or PDF documents
- Capabilities: image text detection, PDF text extraction, **scanned-PDF OCR**, **structured table extraction**, **batch directory processing**, format preservation, Markdown file generation
- Triggers: user uploads an image or PDF and asks to extract text, or asks about the text content of a document; user needs to batch-process a folder; user needs to extract table data from a PDF

## 🔑 Authentication

This skill is **completely free**, but requires a Redfox API key to request usage permission — the key itself costs no credits.

Sign up at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get your personal API key, then configure it in either way:

```bash
# Option 1: config file (e.g. OpenClaw's ~/.openclaw/openclaw.json)
{ "env": { "REDFOX_API_KEY": "ak_xxxx..." } }

# Option 2: terminal environment variable
export REDFOX_API_KEY="ak_xxxx..."
```

> ⚠️ **Before performing any operation, always run `python3 "{SKILL_DIR}/scripts/record.py"` first**.
> If the script exits non-zero (no key configured or the endpoint returned failure), **stop immediately** and tell the user:
> "This skill requires a Redfox API key. Sign up for **free** at https://redfox.hk/settings/api-keys?source=github, then configure the environment variable: `export REDFOX_API_KEY="ak_xxxx..."`"

## Prerequisites

### Required dependencies

```
pymupdf>=1.23.0
requests>=2.28.0
```

```bash
pip install pymupdf>=1.23.0 requests>=2.28.0
```

### Zero extra dependencies

This skill needs **no OCR engine or table library**:
- Scanned PDFs: auto-rendered to high-res PNGs, recognized by the Agent's `read_image` (AI vision)
- Table extraction: uses pymupdf's built-in `find_tables()` — no pdfplumber needed
- Just `pymupdf` + `requests` unlock all features

### Supported file formats

- Images: PNG, JPG, JPEG, GIF, WebP, BMP, TIFF
- Documents: PDF (text-based + scanned; scanned pages are auto-rendered to images for AI recognition)

## Workflow

### Standard flow

#### Step 0: Auth check (must run first)

```bash
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/record.py"
```

- Output `✅ Auth passed — usage permission granted` → continue
- Script exits non-zero → **stop immediately**, show the script's error output to the user and tell them to get a free API key at [redfox.hk](https://redfox.hk/settings/api-keys?source=github)

#### Step 0.5: Version update notice (every run)

```bash
python3 "{SKILL_DIR}/scripts/changelog.py"
```

- If there is output (first run or version upgrade) → **show the full output to the user**, then continue
- If no output (already up to date) → continue directly

#### Image text extraction flow

1. **Receive the image**
   - Confirm the user has uploaded an image file
   - Get the image's accessible URL

2. **Recognize image content (round 1: global recognition)**
   - Use the `read_image` tool to recognize the image
   - Explicitly require the prompt to recognize ALL text — headings, body, annotations, watermarks, etc.
   - Pay special attention to the visual shapes of digits (number of closed loops, opening direction, arc direction) so easily-confused digits like 6/8/9/0/3 are read correctly

3. **Determine whether text exists**
   - Text detected → go to step 4
   - No text → tell the user "the image contains no extractable text", task ends

4. **Extract and organize the text**
   - Extract all text content from the image
   - Preserve the original structure and layout
   - Organize into a readable format

5. **Digit second-pass focused verification (run silently, never shown to the user)**
   - ⚠️ **Important**: the entire verification process (shape descriptions, comparison tables, round records, etc.) must run silently — never show any verification details in the conversation; only present the final confirmed extraction result
   - For every digit string in the round-1 result (phone numbers, order numbers, amounts, dates, etc.), run a second focused recognition:
   - **Strategy A: local zoom verification**
     - Call `read_image` again, but this time the prompt only asks to recognize a specific digit-string region
     - Prompt template: "Focus only on the digit string [context description] in the image. Describe the visual shape of each digit one by one (how many closed loops, opening direction, arc direction), then give the final judgment."
   - **Strategy B: cross verification**
     - Compare round-1 shape descriptions with round-2 independent judgments
     - Both rounds agree → confirm as the final result
     - Rounds disagree → annotate `[to confirm: round 1 read X, round 2 read Y]`
   - **Easily-confused digit cheat sheet**:
     | Digit | Key visual features |
     |------|-------------|
     | **8** | two closed loops stacked, like a snowman/hourglass |
     | **6** | one closed loop at the bottom only, top arc bends left |
     | **9** | one closed loop at the top only, bottom is a downward stroke |
     | **0** | fully closed oval, no opening |
     | **3** | open on the right, two arcs facing right |
     | **5** | top horizontal bar + left vertical stroke + bottom arc |
     | **S** | like 5 but vertically symmetric, no horizontal bar |
     | **O** | rounder closed shape than 0 |

#### PDF text extraction flow

1. **Receive the PDF file**
   - Confirm the user has uploaded a PDF file
   - Get the PDF's local path

2. **Call the extraction script**

   ```bash
   # Standard mode (auto-detect scanned pages, render to images + extract tables)
   python3 "{SKILL_DIR}/scripts/pdf_text_extractor.py" <pdf_file_path>

   # Text only, skip tables (faster)
   python3 "{SKILL_DIR}/scripts/pdf_text_extractor.py" <pdf_file_path> --no-tables

   # Don't render scanned pages (only report which pages are scanned)
   python3 "{SKILL_DIR}/scripts/pdf_text_extractor.py" <pdf_file_path> --no-render

   # Custom scanned-page output directory / render resolution
   python3 "{SKILL_DIR}/scripts/pdf_text_extractor.py" <pdf_file_path> --scan-dir ./ocr_pages --dpi 300
   ```

3. **Handle the result**

   The script returns JSON. Key fields:

   | Field | Description |
   |------|------|
   | `success` | whether extraction succeeded |
   | `text` | Markdown body text (text layer) |
   | `page_count` | total pages |
   | `tables_markdown` | Markdown summary of all tables |
   | `ocr_images` | images needing Agent `read_image` recognition `[{'page','image'}]` |
   | `warnings` | non-fatal warnings (e.g. scanned-page notices) |

   - `success=true` → go to step 4
   - `success=false` → tell the user the `error` field content, task ends

4. **Format the output**
   - Present the `text` field content
   - If `tables_markdown` is non-empty, present the tables separately
   - If `ocr_images` is non-empty: recognize each image with `read_image`, merge the results into the body text, and tell the user which pages were scanned
   - If `warnings` is non-empty, show the warnings to the user

#### Batch processing flow

When the user provides a directory path or asks to batch-process multiple files:

1. **Confirm the directory path**
   - Get the user-specified directory path

2. **Call the batch extraction script**

   ```bash
   # Print the merged Markdown to the terminal
   python3 "{SKILL_DIR}/scripts/batch_extractor.py" <directory>

   # Save to a file
   python3 "{SKILL_DIR}/scripts/batch_extractor.py" <directory> -o result.md

   # Output structured JSON
   python3 "{SKILL_DIR}/scripts/batch_extractor.py" <directory> --json

   # Don't render scanned pages / custom scan output directory
   python3 "{SKILL_DIR}/scripts/batch_extractor.py" <directory> --no-render --scan-dir ./ocr_pages
   ```

3. **Handle the result**
   - The script prints progress to stderr and results to stdout
   - If `-o` was given, tell the user where the file was saved
   - Show summary statistics (total files / succeeded / failed)
   - If the user wants to see content, show `combined_markdown` or per-file results

### Unified output step

5. **Generate the output**
   - Generate a Markdown file per the user's needs
   - Include file source, extraction status, text content, etc.
   - Organize with clear headings and structure

### Optional branches

- User only wants to view the text: output it directly, no file
- User asks to save the result: generate a `.md` file
- Image/PDF text is blurry or hard to recognize: explain the situation and provide the best-effort result
- Scanned PDF: the script has already rendered pages to images — the Agent just recognizes them one by one with `read_image`, no OCR dependency needed
- User asks to extract tables: use standard mode (table extraction is on by default), show the `tables_markdown` field
- User asks for batch processing: use `batch_extractor.py`, supports mixed PDF + image directories

## Resource Index

- **Auth script**: [scripts/record.py](scripts/record.py)
  - Purpose: calls `https://redfox.hk/story/api/skill/record/save` to request usage permission and complete the auth check
  - Failure behavior: exits with code 1 when no key is configured or the endpoint returns 3106/3107
- **Version notice script**: [scripts/changelog.py](scripts/changelog.py)
  - Purpose: shows feature introductions on first run or version upgrade; exits silently when versions match
  - Version record file: `~/.pdf_image_extractor_version`
- **PDF extraction script**: [scripts/pdf_text_extractor.py](scripts/pdf_text_extractor.py)
  - Purpose: extracts text + tables from a PDF and renders scanned pages to images (for read_image)
  - Arguments: `<pdf_path> [--no-tables] [--no-render] [--scan-dir DIR] [--threshold N] [--dpi N]`
  - Output: JSON with `text` / `tables_markdown` / `ocr_images` / `warnings` fields
- **Batch extraction script**: [scripts/batch_extractor.py](scripts/batch_extractor.py)
  - Purpose: batch-processes all PDF + image files in a directory
  - Arguments: `<directory> [--no-tables] [--no-render] [--scan-dir DIR] [-o FILE] [--json]`
  - Output: merged Markdown report or structured JSON

## Notes

### Image text extraction
- **Accuracy**: recognition results are affected by image clarity, font, background, etc. — errors are possible
- **"Shapes before digits" principle**: when recognizing digits, always describe each character's visual shape first (closed loops, opening direction, arc direction) before deciding the digit — never skip shape description and output digits directly
- **Dual recognition for key digit strings**: phone numbers, ID numbers, bank card numbers, order numbers, etc. must go through two rounds (global recognition + focused verification); mark as "to confirm" when rounds disagree
- **Silent verification**: shape descriptions, comparison tables and round records of the digit second pass must never be shown to the user — run everything in the background and only output the final confirmed result
- **Uncertainty annotation**: mark characters that cannot be 100% confirmed with `[?]` plus 2 candidates, e.g. `158****8[?possibly 6]624`
- **Text layout**: preserve the original text structure and reading order as much as possible
- **Multilingual**: supports Chinese, English and other languages

### PDF text extraction
- **Format preservation**: the script preserves paragraph structure and heading levels where possible
- **Scanned PDFs**: pages with a sparse text layer (< 20 characters) are auto-detected and rendered to high-res PNGs for `read_image` (AI vision) — no OCR engine needed; accuracy depends on the AI vision capability
- **Table extraction**: on by default, using pymupdf `find_tables()` with Markdown output; complex tables (merged cells, nested tables) may extract poorly
- **Encrypted PDFs**: encrypted or password-protected PDFs are not supported

### Batch processing
- **File order**: processed alphabetically by filename
- **Image recognition**: batch mode does no local OCR — images are aggregated into the `ocr_images` list for the Agent to recognize one by one via `read_image`
- **Large directories**: keep each run under ~100 files; more files may take a long time
- **Output**: goes to the terminal by default — prefer `-o result.md` to save to a file

### General notes
- **Privacy**: processed files are not stored — used only in the current session
- **File size**: prefer files under 50MB; larger files may process slowly

## Examples

### Example 1: image text extraction

**User action**: uploads an image containing text

**Agent handling**:
1. Run `python3 "{SKILL_DIR}/scripts/record.py"` → `✅ Auth passed`
2. Run `python3 "{SKILL_DIR}/scripts/changelog.py"` → show output to the user if any
3. Recognize the image with the `read_image` tool
4. Extract the text content: "All the struggles we've been through / and the sorrows we regret / cannot possibly be meaningless"
5. Output the extraction result directly

### Example 2: PDF text + table extraction

**User action**: uploads a PDF and asks "extract the text from this PDF"

**Agent handling**:
1. Run `python3 "{SKILL_DIR}/scripts/record.py"` → auth passed
2. Run `python3 "{SKILL_DIR}/scripts/changelog.py"` → silent
3. Run: `python3 "{SKILL_DIR}/scripts/pdf_text_extractor.py" ./document.pdf`
4. Get the JSON result: `text` (body) + `tables_markdown` (tables)
5. Present body and tables separately, generate `./extracted_from_pdf.md`

### Example 3: scanned PDF (render + AI recognition)

**User action**: uploads a scanned PDF

**Agent handling**:
1. Auth + version check
2. Run: `python3 "{SKILL_DIR}/scripts/pdf_text_extractor.py" ./scan.pdf`
3. The script detects pages with empty text layers, renders them to high-res PNGs, `ocr_images` lists the paths
4. The Agent recognizes each PNG with `read_image` and extracts the text
5. Tell the user: "pages 1/2/3 were scanned and recognized via AI vision", present the result

### Example 4: batch directory processing

**User action**: "extract text from all files in ./documents/"

**Agent handling**:
1. Auth + version check
2. Run: `python3 "{SKILL_DIR}/scripts/batch_extractor.py" ./documents/ -o batch_result.md`
3. The script processes all PDFs + images in the directory, printing progress to stderr
4. Tell the user: "processed 8 files (7 succeeded / 1 failed), results saved to batch_result.md"
5. Show summary statistics

### Example 5: no API key configured

**User action**: uploads an image for text extraction, but `REDFOX_API_KEY` is not configured

**Agent handling**:
1. Run `python3 "{SKILL_DIR}/scripts/record.py"` → script errors and exits
2. **Stop immediately** and tell the user: "This skill requires a Redfox API key. Sign up for **free** at https://redfox.hk/settings/api-keys?source=github, then run: `export REDFOX_API_KEY="ak_xxxx..."`"
