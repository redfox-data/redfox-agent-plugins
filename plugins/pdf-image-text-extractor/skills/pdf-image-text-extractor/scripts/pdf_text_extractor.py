#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf-image-text-extractor/scripts/pdf_text_extractor.py  v2.1.0 (lightweight)

Only core dependency is pymupdf — no pdfplumber / tesseract / rapidocr needed.

Features:
  1. Text-layer extraction: pymupdf get_text, preserving heading & paragraph structure
  2. Structured table extraction: pymupdf's built-in page.find_tables(), output as Markdown tables
  3. Scanned-page handling: pages with an empty text layer are rendered to PNG images
     and listed as paths for the Agent's read_image (AI vision) to recognize —
     no local OCR engine required

Usage:
  python3 scripts/pdf_text_extractor.py document.pdf
  python3 scripts/pdf_text_extractor.py document.pdf --no-tables
  python3 scripts/pdf_text_extractor.py scan.pdf --scan-dir ./ocr_pages
"""

import sys
import json
import argparse
import contextlib
from pathlib import Path

# pymupdf 1.24+ recommends `import pymupdf`; older versions use `import fitz`
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz  # noqa: F401
    except ImportError:
        print(json.dumps({
            'success': False,
            'error': 'Missing dependency: pymupdf. Install it with: pip install pymupdf',
            'text': '', 'page_count': 0,
            'tables': [], 'tables_markdown': '',
            'ocr_images': [], 'warnings': []
        }, ensure_ascii=False))
        sys.exit(1)


# ─────────────────────────────────────────────
# Tables: Markdown conversion + find_tables extraction
# ─────────────────────────────────────────────

def _table_to_markdown(rows: list) -> str:
    """Convert a 2D list into a Markdown table string"""
    if not rows:
        return ''

    cleaned = [
        [str(cell).replace('\n', ' ').strip() if cell is not None else ''
         for cell in row]
        for row in rows
    ]
    cleaned = [r for r in cleaned if any(c for c in r)]  # drop all-empty rows
    if not cleaned:
        return ''

    max_cols = max(len(r) for r in cleaned)
    for r in cleaned:
        while len(r) < max_cols:
            r.append('')

    header, body = cleaned[0], cleaned[1:]
    lines = [
        '| ' + ' | '.join(header) + ' |',
        '| ' + ' | '.join(['---'] * max_cols) + ' |',
    ]
    lines += ['| ' + ' | '.join(row) + ' |' for row in body]
    return '\n'.join(lines)


def _extract_tables(doc) -> tuple:
    """
    Extract all tables in the document with pymupdf's built-in find_tables().
    Returns (tables_list, tables_markdown)
    """
    tables_list = []
    md_parts = []

    for page_idx, page in enumerate(doc):
        try:
            finder = page.find_tables()
            tables = getattr(finder, 'tables', [])
        except Exception:
            continue

        for t_idx, table in enumerate(tables):
            try:
                data = table.extract()
            except Exception:
                continue
            if not data or not any(any(c for c in row) for row in data):
                continue

            tables_list.append({
                'page': page_idx + 1,
                'table_index': t_idx + 1,
                'data': data,
            })
            md = _table_to_markdown(data)
            if md:
                md_parts.append(
                    f"#### Page {page_idx + 1} · Table {t_idx + 1}\n\n{md}"
                )

    return tables_list, '\n\n'.join(md_parts)


# ─────────────────────────────────────────────
# Scanned-page rendering (for Agent read_image recognition)
# ─────────────────────────────────────────────

def _render_page_to_png(page, out_path: str, dpi: int = 200) -> bool:
    """Render a PDF page to a PNG image; returns True on success"""
    try:
        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=mat)
        pix.save(out_path)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# Core extraction function
# ─────────────────────────────────────────────

def extract_text_from_pdf(*args, **kwargs) -> dict:
    """
    Public entry point.
    Wraps a stdout redirect: pymupdf may print non-JSON notices to stdout while
    processing (e.g. "Consider using the pymupdf_layout package ..."), which would
    pollute the caller's JSON / Markdown output. Here all stdout during extraction
    is redirected to stderr so the caller (Agent / batch_extractor) always gets a
    clean result from stdout.
    """
    with contextlib.redirect_stdout(sys.stderr):
        return _extract_impl(*args, **kwargs)


def _extract_impl(
    pdf_path: str,
    extract_tables: bool = True,
    render_scan: bool = True,
    scan_dir: str = None,
    scan_threshold: int = 20,
    dpi: int = 200,
) -> dict:
    """
    Extract text + tables from a PDF and render scanned pages to images for the Agent.

    Args:
        pdf_path       : path to the PDF file
        extract_tables : whether to extract tables with find_tables()
        render_scan    : whether to render text-less scanned pages to PNG
        scan_dir       : output directory for scanned-page images (default <pdf_name>_ocr_pages/)
        scan_threshold : character-count threshold for treating a page as scanned (default < 20)
        dpi            : render resolution for scanned pages (default 200; higher = sharper)

    Returns dict:
        success          bool
        text             str   — Markdown body text (text layer)
        page_count       int
        tables           list  — raw table data [{'page','table_index','data'}]
        tables_markdown  str   — Markdown summary of all tables
        ocr_images       list  — images needing Agent read_image recognition [{'page','image'}]
        warnings         list  — non-fatal warnings
        error            str
    """
    warnings = []
    result = {
        'success': False, 'text': '', 'page_count': 0,
        'tables': [], 'tables_markdown': '',
        'ocr_images': [], 'warnings': warnings, 'error': ''
    }

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        result['error'] = f'File not found: {pdf_path}'
        return result
    if pdf_file.suffix.lower() != '.pdf':
        result['error'] = f'Unsupported file format: {pdf_file.suffix}, only PDF is supported'
        return result

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result['error'] = f'Cannot open the PDF (possibly encrypted or corrupted): {e}'
        return result

    page_count = len(doc)
    if page_count == 0:
        result['error'] = 'The PDF is empty — no pages found'
        return result

    # Output directory for scanned-page images
    if scan_dir:
        out_dir = Path(scan_dir)
    else:
        out_dir = pdf_file.parent / f'{pdf_file.stem}_ocr_pages'

    md_parts = []
    ocr_images = []

    for page_num in range(page_count):
        page = doc[page_num]
        if page_num > 0:
            md_parts.append('\n---\n')

        # ── Extract the text layer (preserving heading structure) ──
        page_text = ''
        try:
            blocks = page.get_text("dict")["blocks"]
            text_lines = []
            for block in blocks:
                if block.get("type") != 0:
                    continue
                block_lines = []
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        txt = span["text"].strip()
                        if not txt:
                            continue
                        if span["size"] > 16:
                            if line_text:
                                block_lines.append(line_text)
                            is_bold = "bold" in span["font"].lower()
                            line_text = f"### {txt}" if is_bold else f"## {txt}"
                        else:
                            line_text += txt + " "
                    if line_text.strip():
                        block_lines.append(line_text.strip())
                if block_lines:
                    text_lines.append('\n'.join(block_lines))
            page_text = '\n\n'.join(text_lines).strip()
        except Exception:
            page_text = ''

        # ── Sparse text layer → treat as scanned page, render to image ──
        if len(page_text) < scan_threshold:
            if render_scan:
                out_dir.mkdir(parents=True, exist_ok=True)
                img_path = str((out_dir / f'{pdf_file.stem}_p{page_num + 1}.png').resolve())
                if _render_page_to_png(page, img_path, dpi=dpi):
                    ocr_images.append({'page': page_num + 1, 'image': img_path})
                else:
                    warnings.append(f'Page {page_num + 1}: looks like a scanned page but rendering failed')
            else:
                warnings.append(f'Page {page_num + 1}: looks like a scanned page (empty text layer), rendering skipped')
        elif page_text:
            md_parts.append(page_text)

    doc.close()

    full_text = '\n'.join(md_parts)
    while '\n\n\n' in full_text:
        full_text = full_text.replace('\n\n\n', '\n\n')

    # ── Table extraction ──
    tables, tables_markdown = [], ''
    if extract_tables:
        try:
            doc2 = fitz.open(pdf_path)
            tables, tables_markdown = _extract_tables(doc2)
            doc2.close()
        except Exception as e:
            warnings.append(f'Error during table extraction: {e}')

    if ocr_images:
        pages_str = ', '.join(str(i['page']) for i in ocr_images)
        warnings.append(
            f'Pages {pages_str} are scanned pages, rendered to images — recognize them with read_image (see the ocr_images field)'
        )

    result.update({
        'success': True,
        'text': full_text.strip(),
        'page_count': page_count,
        'tables': tables,
        'tables_markdown': tables_markdown,
        'ocr_images': ocr_images,
    })
    return result


# ─────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='PDF text extraction tool v2.1.0 (lightweight, pymupdf only)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  python3 scripts/pdf_text_extractor.py document.pdf\n'
            '  python3 scripts/pdf_text_extractor.py report.pdf --no-tables\n'
            '  python3 scripts/pdf_text_extractor.py scan.pdf --scan-dir ./ocr_pages\n'
        )
    )
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--no-tables', action='store_true', help='Skip table extraction')
    parser.add_argument('--no-render', action='store_true',
                        help="Don't render scanned pages to images (only report which pages are scanned)")
    parser.add_argument('--scan-dir', default=None,
                        help='Output directory for scanned-page images (default <pdf_name>_ocr_pages/)')
    parser.add_argument('--threshold', type=int, default=20,
                        help='Character-count threshold for treating a page as scanned (default 20)')
    parser.add_argument('--dpi', type=int, default=200,
                        help='Render resolution for scanned pages (default 200)')

    args = parser.parse_args()

    result = extract_text_from_pdf(
        pdf_path=args.pdf_path,
        extract_tables=not args.no_tables,
        render_scan=not args.no_render,
        scan_dir=args.scan_dir,
        scan_threshold=args.threshold,
        dpi=args.dpi,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result['success']:
        sys.exit(1)


if __name__ == '__main__':
    main()
