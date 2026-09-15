#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf-image-text-extractor/scripts/changelog.py

Version update notice script
- First run: show the full feature introduction
- Version upgrade: show the changelog
- Same version: exit silently (no output)

Version record file: ~/.pdf_image_extractor_version
Usage: python3 scripts/changelog.py
"""

import sys
from pathlib import Path

CURRENT_VERSION = "2.1.0"
VERSION_FILE = Path.home() / ".pdf_image_extractor_version"

CHANGELOG = {
    "2.1.0": {
        "title": "PDF & Image Text Extractor v2.1.0 — zero-dependency lightweight upgrade",
        "features": [
            "🔍  Scanned-PDF recognition (zero extra dependencies)\n"
            "     Auto-detects text-less pages, renders them to high-res PNGs for AI vision recognition\n"
            "     No tesseract / rapidocr or any other OCR engine needed\n"
            "     Handles mixed Chinese/English text; accuracy depends on the AI vision capability",

            "📊  Structured table extraction (zero extra dependencies)\n"
            "     Uses pymupdf's built-in find_tables() to detect tables, output in Markdown format\n"
            "     No pdfplumber needed\n"
            "     Supports multiple tables across pages, preserving row/column structure",

            "📁  Batch processing mode\n"
            "     Pass a directory path to process all PDF and image files at once\n"
            "     Supported formats: PDF / PNG / JPG / JPEG / WebP / BMP / TIFF\n"
            "     Can output a merged Markdown file or structured JSON data\n"
            "     Usage: python3 scripts/batch_extractor.py <directory> [-o result.md]",

            "⚡  Drastically slimmed dependencies\n"
            "     All features need just two packages: pymupdf + requests\n"
            "     Installation drops from \"hundreds of MB + system-level engines\" to \"one pip command, done in seconds\"",
        ],
        "deps": "pip install pymupdf requests",
    }
}


def get_stored_version() -> str:
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return ""


def save_version(version: str) -> None:
    try:
        VERSION_FILE.write_text(version, encoding="utf-8")
    except Exception:
        pass


def show_changelog() -> None:
    stored = get_stored_version()

    if stored == CURRENT_VERSION:
        # Same version — exit silently
        return

    entry = CHANGELOG.get(CURRENT_VERSION, {})
    title = entry.get("title", f"PDF & Image Text Extractor v{CURRENT_VERSION}")
    features = entry.get("features", [])
    deps = entry.get("deps", "")

    if not stored:
        # First run
        print(f"👋 Welcome to {title}!")
        print()
        print("This release adds the following features:")
        print()
        for feat in features:
            print(f"  {feat}")
            print()
    else:
        # Version upgrade
        print(f"🔄 Upgraded from v{stored} to v{CURRENT_VERSION}")
        print()
        print("New features:")
        print()
        for feat in features:
            print(f"  {feat}")
            print()

    if deps:
        print("─" * 50)
        print(f"📦 Required dependencies (one command installs everything): {deps}")

    print()
    save_version(CURRENT_VERSION)


if __name__ == "__main__":
    show_changelog()
