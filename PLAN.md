# Second Brain — Implementation Plan

## Status: Not started

---

## Phase 1 — Ingestion Pipeline

Build the core pipeline that transforms a dropped PDF into a searchable, linked document.

### 1.1 `brain/parser.py`
- Accept a file path to a PDF
- Convert to Markdown using `pymupdf4llm`
- Extract images to `store/images/<slug>/<n>.png`
- Return Markdown text + list of extracted image paths
- Parse/preserve existing frontmatter if present

### 1.2 `brain/vision.py`
- Accept a list of image paths + the parent slug
- For each image: call Claude API (`claude-haiku-4-5`) with the image
- Return a dict mapping image path → description string
- Called by `ingest.py`; descriptions injected as blockquotes in Markdown

### 1.3 `brain/tagger.py`
- Accept Markdown text + existing frontmatter tags (may be empty)
- If frontmatter already has `tags`: return them as-is (skip LLM call)
- Else: call Claude API (`claude-haiku-4-5`) to generate tag list
- Return list of tag strings

### 1.4 `brain/graph.py`
- SQLite schema: `documents` table (slug, title, path, tags, created_at) + `edges` table (src, dst, type, weight)
- `NetworkX DiGraph` rebuilt from SQLite on startup
- Public API: `upsert_document()`, `add_edge()`, `get_neighbors(slug, hops)`, `export_json()`

### 1.5 `brain/index.py`
- Wrap ChromaDB collection
- `add_document(slug, text)`: chunk text, embed, upsert to ChromaDB
- `query(text, limit)`: vector similarity search, returns ranked (slug, score) list
- `rebuild()`: drop + re-embed all documents in `store/documents/`

### 1.6 `brain/linker.py`
- Accept a slug + its Markdown text + list of all existing slugs
- Call Claude API (`claude-sonnet-4-6`) to suggest relevant `[[wikilink]]` insertions
- Return modified Markdown with wikilinks injected
- Add `wikilink` edges to graph for each generated link

### 1.7 `brain/ingest.py`
- Orchestrate the full pipeline: parser → vision → tagger → linker → index → graph
- Write final Markdown to `store/documents/<slug>.md`
- `--all` flag: process every PDF in `raw/` that hasn't been ingested yet
- Emit progress to stdout

---

## Phase 2 — Search & Query

### 2.1 `brain/search.py`
- `hybrid_search(query, limit)`:
  1. BM25 pass over all document chunks (rank_bm25)
  2. Vector similarity pass (ChromaDB)
  3. Graph traversal from top-N hits (1–2 hops, wikilink edges)
  4. Merge + re-rank results
- Returns list of `(slug, chunk_text, score)` tuples

### 2.2 `brain/query.py`
- Accept a natural-language question
- Call `search.py` to gather context chunks
- Compute confidence score from top chunk scores
- If score ≥ `QUERY_CONFIDENCE_THRESHOLD` (default 0.72): answer locally from context
- Else: escalate to Claude API (`claude-sonnet-4-6`) with local context as grounding
- Return answer string + list of cited source slugs

---

## Phase 3 — Web UI

### 3.1 `brain/server.py`
FastAPI routes:
- `GET /` — search/Q&A terminal prompt page
- `POST /query` — accepts question, returns answer + sources (JSON)
- `GET /graph` — Cytoscape.js knowledge graph page
- `GET /graph/data` — graph nodes + edges as JSON for Cytoscape
- `GET /doc/<slug>` — rendered Markdown document viewer
- `GET /upload` — drag-and-drop PDF upload page
- `POST /upload` — save PDF to `raw/`, trigger ingest, return status

### 3.2 `templates/`
- `base.html` — shared layout: phosphor green (#33ff33) on black, CRT scanline overlay, VT323/Share Tech Mono fonts
- `index.html` — terminal prompt input + streaming answer display
- `graph.html` — full-viewport Cytoscape.js canvas, node glow on hover
- `doc.html` — Markdown rendered as terminal-style text
- `upload.html` — retro file-selector drag-and-drop zone

### 3.3 `static/`
- `style.css` — CRT/phosphor aesthetic, scanline overlay, cursor blink
- `graph.js` — Cytoscape.js init + edge coloring by type (wikilink/tag/semantic)
- `terminal.js` — typewriter effect, query submission, SSE stream handling

---

## Phase 4 — MCP Server & Entry Point

### 4.1 `brain/mcp.py`
MCP tools to expose:
- `search(query, limit)` — calls `search.py`
- `get_document(slug)` — returns raw Markdown
- `get_graph_neighbors(slug, hops)` — calls `graph.py`
- `ingest(file_path)` — triggers ingestion pipeline
- `list_tags()` — returns all tags from SQLite

### 4.2 `brain/app.py`
- Start `watchdog` file watcher on `raw/` (auto-ingest new PDFs)
- Start FastAPI server via `uvicorn`
- Load env vars from `.env` via `python-dotenv`

### 4.3 `brain/migrations/`
- `001_initial.sql` — create `documents` and `edges` tables
- Migration runner: `python -m brain.migrations`

---

## Phase 5 — Tests

- `tests/test_parser.py` — PDF → Markdown conversion, image extraction
- `tests/test_tagger.py` — tag extraction, frontmatter short-circuit
- `tests/test_graph.py` — node upsert, edge creation, neighbor traversal
- `tests/test_search.py` — BM25 + vector hybrid ranking
- `tests/test_query.py` — confidence threshold branching, citation output
- `tests/test_server.py` — FastAPI route smoke tests (httpx)

---

## Build Order

```
1. graph.py + migrations    ← foundation (no deps)
2. parser.py                ← PDF in, Markdown + images out
3. vision.py                ← images → descriptions
4. tagger.py                ← Markdown → tags
5. index.py                 ← ChromaDB wrapper
6. linker.py                ← wikilink injection
7. ingest.py                ← orchestrate 2–6
8. search.py                ← BM25 + vector + graph
9. query.py                 ← Q&A engine
10. server.py + templates   ← web UI
11. mcp.py                  ← MCP server
12. app.py                  ← entry point + watcher
13. tests/                  ← test suite
```
