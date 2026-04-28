# Architecture Overview

Second Brain is a local-first, AI-powered Zettelkasten system designed to ingest, process, and query documents seamlessly.

## Core Design Principles

1. **Local-First & Obsidian Compatible**: The absolute source of truth is the `store/documents/` folder. Documents are plain Markdown files with YAML frontmatter. There is no SQL database locking your notes in.
2. **AI Enrichment**: The system relies on Anthropic's Claude APIs to automatically categorize, tag, describe images, and inject semantic links between documents.
3. **Hybrid Retrieval**: Search relies on a multi-stage pipeline combining keyword match (BM25), vector similarity (ChromaDB), and graph topology (NetworkX).

## Component Stack

### 1. Ingestion Pipeline (`brain/ingest.py`)
- **Parser (`parser.py`)**: Uses `pymupdf4llm` to chunk and parse massive PDFs into Markdown and extract images into `store/images/`.
- **Vision (`vision.py`)**: Uses `claude-3-5-haiku-latest` to analyze extracted images and append contextual descriptions.
- **Tagger (`tagger.py`)**: Uses `claude-3-5-haiku-latest` to read document text and generate a structured JSON taxonomy (tags). Short-circuits if tags already exist in the file.
- **Linker (`linker.py`)**: Uses `claude-3-5-sonnet-latest` to semantically inject `[[wikilinks]]` into the text, linking the new document to the existing knowledge graph.

### 2. Knowledge Graph (`brain/graph.py`)
- Built on `NetworkX DiGraph`.
- Rebuilt dynamically in-memory on startup by parsing all `.md` files and scanning for `[[wikilinks]]` and YAML tags.

### 3. Vector Engine (`brain/index.py`)
- Built on `ChromaDB`.
- Persisted locally in `store/chroma/`. Chunks Markdown text and stores local embeddings for semantic search.

### 4. Query & Search Engine (`brain/query.py` & `brain/search.py`)
- **Search**: Combines BM25 (keyword), ChromaDB (semantic), and NetworkX (graph traversal boost).
- **Query**: Routes based on confidence. High confidence hits use Haiku to summarize the exact context. Low confidence hits escalate to Sonnet for deep reasoning.

### 5. Web Interface & API (`brain/server.py`)
- Built on `FastAPI`.
- Uses Jinja2 templates and vanilla JS/CSS for a retro CRT terminal aesthetic.
- Includes `Cytoscape.js` for rendering the knowledge graph visually.

### 6. MCP Server (`brain/mcp.py`)
- Implements the Model Context Protocol using `mcp.server.fastmcp`.
- Allows external AI assistants (like Claude Desktop) to hook into the Second Brain's search, graph, and ingestion tools.

## Deployment

### Docker (recommended)

The application ships as a single Docker container. See [docs/how-to/run-with-docker.md](how-to/run-with-docker.md) for the quick-start guide.

**Container layout:**

| Path in container | Role |
|---|---|
| `/app/brain/` | Application source |
| `/app/static/` | Web UI assets |
| `/app/templates/` | Jinja2 templates |
| `/app/raw/` | PDF staging area (watchdog input) — backed by `brain-raw` volume |
| `/app/store/` | All persistent state — backed by `brain-store` volume |

**Named volumes:**

| Volume | Contents |
|---|---|
| `brain-store` | `documents/` (Markdown), `chroma/` (embeddings), `images/` (extracted PNGs) |
| `brain-raw` | PDFs awaiting ingestion |

The container exposes port **8000**. A built-in `HEALTHCHECK` polls the root endpoint every 30 s.

### Local (development)

```bash
pip install -r requirements.txt
python -m brain.app
```

Required environment variable: `ANTHROPIC_API_KEY`.
