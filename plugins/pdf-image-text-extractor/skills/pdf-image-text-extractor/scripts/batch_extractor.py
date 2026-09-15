#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf-image-text-extractor/scripts/batch_extractor.py  v2.1.0 (lightweight)

Batch file text extraction script — only core dependency is pymupdf.
Supported formats:
  - PDF: text-layer extraction + structured table extraction (find_tables) + scanned-page rendering
  - Images (PNG/JPG/JPEG/WebP/BMP/TIFF): paths collected directly for the Agent's read_image

⚠️ This script does NOT perform local OCR. All content needing vision recognition
   (scanned pages + images) is aggregated into the ocr_images list in the result,
   and the Agent recognizes them one by one via read_image.

Usage:
  python3 scripts/batch_extractor.py ./documents/
  python3 scripts/batch_extractor.py ./documents/ -o result.md
  python3 scripts/batch_extractor.py ./documents/ --json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

PDF_EXTS   = {'.pdf'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.gif'}
ALL_EXTS   = PDF_EXTS | IMAGE_EXTS


def scan_directory(dir_path: str) -> list:
    """Scan the directory and return absolute paths of all supported files (sorted by name)"""
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        return []
    return sorted(
        [str(f.resolve()) for f in p.iterdir()
         if f.is_file() and f.suffix.lower() in ALL_EXTS],
        key=lambda x: Path(x).name.lower()
    )


def batch_extract(
    dir_path: str,
    extract_tables: bool = True,
    render_scan: bool = True,
    scan_dir: str = None,
) -> dict:
    """
    Batch-extract all PDFs and images in a directory.

    Returns dict:
        success           bool
        dir_path          str
        total_files       int
        pdf_count         int
        image_count       int
        results           list  — per-file processing results
        ocr_images        list  — images needing Agent read_image [{'source','image'}]
        combined_markdown str   — merged Markdown report
        error             str
    """
    scripts_dir = Path(__file__).parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from pdf_text_extractor import extract_text_from_pdf

    dirp = Path(dir_path)
    files = scan_directory(dir_path)
    if not files:
        return {
            'success': False, 'dir_path': dir_path, 'total_files': 0,
            'pdf_count': 0, 'image_count': 0, 'results': [],
            'ocr_images': [], 'combined_markdown': '',
            'error': (
                f'Directory not found or no supported files: {dir_path}\n'
                f'Supported formats: PDF, {", ".join(sorted(IMAGE_EXTS))}'
            )
        }

    # Shared output directory for scanned-page images in batch mode
    out_scan_dir = scan_dir or str((dirp / '_ocr_pages').resolve())
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    results = []
    ocr_images_all = []
    body_parts = []

    for file_path in files:
        fname = Path(file_path).name
        ext   = Path(file_path).suffix.lower()
        print(f'  Processing: {fname} ...', file=sys.stderr)

        # ── PDF ──────────────────────────────
        if ext in PDF_EXTS:
            pdf_res = extract_text_from_pdf(
                pdf_path=file_path,
                extract_tables=extract_tables,
                render_scan=render_scan,
                scan_dir=out_scan_dir,
            )
            entry = {
                'file': fname, 'type': 'pdf',
                'success': pdf_res['success'],
                'text': pdf_res['text'],
                'page_count': pdf_res['page_count'],
                'tables_markdown': pdf_res.get('tables_markdown', ''),
                'ocr_images': pdf_res.get('ocr_images', []),
                'warnings': pdf_res.get('warnings', []),
                'error': pdf_res['error'],
            }
            # Merge scanned-page images into the master list
            for oi in pdf_res.get('ocr_images', []):
                ocr_images_all.append({'source': fname, 'page': oi['page'], 'image': oi['image']})

            body_parts.append(f'\n---\n\n## 📄 {fname}\n')
            if pdf_res['success']:
                body_parts.append(f'*{pdf_res["page_count"]} pages*')
                if pdf_res['text']:
                    body_parts.append('\n' + pdf_res['text'] + '\n')
                if pdf_res.get('ocr_images'):
                    pages = ', '.join(str(o['page']) for o in pdf_res['ocr_images'])
                    body_parts.append(f'\n> 🔍 Pages {pages} are scanned pages, rendered to images, pending read_image recognition\n')
                if pdf_res.get('tables_markdown'):
                    body_parts.append('\n### 📊 Extracted tables\n\n' + pdf_res['tables_markdown'] + '\n')
            else:
                body_parts.append(f'\n❌ Extraction failed: {pdf_res["error"]}\n')

        # ── Image ────────────────────────────
        elif ext in IMAGE_EXTS:
            abs_img = str(Path(file_path).resolve())
            entry = {
                'file': fname, 'type': 'image',
                'success': True, 'text': '',
                'ocr_images': [{'page': None, 'image': abs_img}],
                'warnings': [], 'error': '',
            }
            ocr_images_all.append({'source': fname, 'page': None, 'image': abs_img})
            body_parts.append(
                f'\n---\n\n## 🖼️ {fname}\n\n> Pending read_image recognition: `{abs_img}`\n'
            )

        results.append(entry)

    pdf_count   = sum(1 for r in results if r['type'] == 'pdf')
    image_count = sum(1 for r in results if r['type'] == 'image')
    ok_count    = sum(1 for r in results if r['success'])
    tbl_count   = sum(1 for r in results if r.get('tables_markdown'))

    header = [
        '# Batch Text Extraction Report\n',
        '| Item | Value |',
        '|------|-----|',
        f'| Directory | `{dir_path}` |',
        f'| Total files | {len(files)} (PDF {pdf_count} / images {image_count}) |',
        f'| Parsed OK | {ok_count} |',
        f'| With tables | {tbl_count} |',
        f'| Pending read_image | {len(ocr_images_all)} |',
        f'| Extracted at | {now} |',
        '',
    ]
    if ocr_images_all:
        header.append('> ⚠️ The following images must be recognized by the Agent one by one via read_image (see the ocr_images field in the JSON)\n')

    combined_md = '\n'.join(header + body_parts)

    return {
        'success': True, 'dir_path': dir_path,
        'total_files': len(files), 'pdf_count': pdf_count, 'image_count': image_count,
        'results': results, 'ocr_images': ocr_images_all,
        'combined_markdown': combined_md, 'error': '',
    }


def main():
    parser = argparse.ArgumentParser(
        description='Batch file text extraction tool v2.1.0 (lightweight, pymupdf only)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  python3 scripts/batch_extractor.py ./documents/\n'
            '  python3 scripts/batch_extractor.py ./documents/ -o result.md\n'
            '  python3 scripts/batch_extractor.py ./documents/ --json\n'
        )
    )
    parser.add_argument('dir_path', help='Directory path to process')
    parser.add_argument('--no-tables', action='store_true', help='Skip PDF table extraction')
    parser.add_argument('--no-render', action='store_true', help="Don't render scanned pages to images")
    parser.add_argument('--scan-dir', default=None, help='Output directory for scanned-page images (default <dir>/_ocr_pages/)')
    parser.add_argument('-o', '--output', metavar='FILE', help='Save the merged Markdown to a file')
    parser.add_argument('--json', action='store_true', help='Output as JSON (includes the ocr_images list)')

    args = parser.parse_args()
    print(f'📁 Starting batch extraction: {args.dir_path}', file=sys.stderr)

    result = batch_extract(
        dir_path=args.dir_path,
        extract_tables=not args.no_tables,
        render_scan=not args.no_render,
        scan_dir=args.scan_dir,
    )

    if not result['success']:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.json:
        output = {k: v for k, v in result.items() if k != 'combined_markdown'}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result['combined_markdown'], encoding='utf-8')
        print(json.dumps({
            'success': True,
            'total_files': result['total_files'],
            'ocr_images': len(result['ocr_images']),
            'output_file': str(out_path.resolve()),
        }, ensure_ascii=False, indent=2))
        print(f'\n✅ Markdown report saved to: {out_path.resolve()}', file=sys.stderr)
    else:
        print(result['combined_markdown'])

    print(
        f'\n✅ Done: {result["total_files"]} files (PDF {result["pdf_count"]} / images {result["image_count"]}), '
        f'{len(result["ocr_images"])} images pending recognition',
        file=sys.stderr
    )


if __name__ == '__main__':
    main()
