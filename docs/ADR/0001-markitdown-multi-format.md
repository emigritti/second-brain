# ADR 0001 — Adopt MarkItDown for multi-format ingestion

## Status

Accepted — 2026-04-29

## Context

second-brain ingested only PDFs. Users need to drop DOCX, XLSX, PPTX, HTML, EPUB,
audio, ZIP and other file types into `raw/` and have them processed through the same
pipeline without building custom format-specific converters for each.

## Decision

Adopt `markitdown[all]` (MIT license, 118k+ stars, actively maintained) as the
conversion layer for all non-PDF formats. Retain `pymupdf4llm` for PDFs because
MarkItDown does not extract images from PDFs as separate files — replacing it would
break the `vision.py` pipeline that sends per-image PNGs to Claude Haiku for
description.

The integration point is a new `parse_document()` dispatcher in `brain/parser.py`
that routes `.pdf` files to the existing `parse_pdf()` / pymupdf4llm path and all
other supported extensions to `_parse_with_markitdown()`. The rest of the ingestion
pipeline (`vision.py`, `tagger.py`, `linker.py`, `graph.py`, `index.py`) is
unchanged — the vision step was already gated on `if image_paths:`, so it is
naturally skipped for non-PDF documents.

### Supported formats added

| Extension(s) | Format |
|---|---|
| `.docx` | Word |
| `.xlsx`, `.xls` | Excel |
| `.pptx` | PowerPoint |
| `.html`, `.htm` | Web pages |
| `.xml`, `.csv`, `.json` | Structured data |
| `.epub` | E-books |
| `.md` | Raw Markdown |
| `.mp3`, `.wav`, `.m4a` | Audio (transcription) |
| `.zip` | Archives |

## Alternatives considered

1. **Replace PDF parser entirely with MarkItDown** — rejected. MarkItDown does not
   extract images from PDFs as separate files, which would break per-image Claude
   vision descriptions. The existing pymupdf4llm path is well-tested and handles
   large PDFs (300 MB+) via 10-page chunked processing.

2. **Build format-specific converters** (python-docx, openpyxl, python-pptx, etc.)
   — rejected. This reinvents what MarkItDown already provides with no benefit,
   and would require maintaining N separate parsing modules.

## Consequences

- `requirements.txt` gains `markitdown[all]` and its transitive dependencies.
- Audio transcription (`.mp3`, `.wav`, `.m4a`) requires additional service
  configuration (Azure Speech or compatible); the pipeline degrades gracefully if
  not configured — MarkItDown returns minimal/empty content rather than raising.
- Future format support added by MarkItDown upstream is available for free with a
  dependency upgrade; no code changes needed.
- `brain/parser.py` now has two code paths; the PDF path is completely unchanged.
- `ingest_pdf()` has been renamed to `ingest_document()` — callers updated in
  `app.py`, `server.py`.
