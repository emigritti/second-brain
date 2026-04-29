# Architecture Overview

Second Brain is a local-first, AI-powered Zettelkasten system designed to ingest, process, and query documents seamlessly.

## Core Design Principles

1. **Local-First & Obsidian Compatible**: The absolute source of truth is the `store/documents/` folder. Documents are plain Markdown files with YAML frontmatter. There is no SQL database locking your notes in.
2. **AI Enrichment**: The system uses a pluggable LLM backend (`brain/llm.py`) supporting both Anthropic Claude and local Ollama models. Vision and query escalation use Anthropic exclusively; tagging and wikilink injection are configurable per-task via the `/settings` page.
3. **Hybrid Retrieval**: Search relies on a multi-stage pipeline combining keyword match (BM25), vector similarity (ChromaDB), and graph topology (NetworkX).

## Component Stack

### 1. Ingestion Pipeline (`brain/ingest.py`)
- **Parser (`parser.py`)**: Uses `pymupdf4llm` to chunk and parse massive PDFs into Markdown and extract images into `store/images/`.
- **Vision (`vision.py`)**: Uses `claude-haiku-4-5` to analyze extracted images and append contextual descriptions.
- **Tagger (`tagger.py`)**: Generates a structured JSON taxonomy (3–7 tags). Short-circuits if tags already exist in the file. Delegates to `brain/llm.py` — configurable as Anthropic or Ollama.
- **Linker (`linker.py`)**: Semantically injects `[[wikilinks]]` into the text linking to existing documents. Delegates to `brain/llm.py` — configurable as Anthropic or Ollama.
- **LLM Provider (`llm.py`)**: Central dispatcher. Reads `store/config.json` on each call. Routes to Ollama first if configured; falls back to Anthropic on failure and records a warning in `INGEST_LOG`.

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
- `/settings` page allows runtime configuration of LLM backends, model names, and temperatures without restarting the server. Configuration is persisted in `store/config.json`.

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

### LLM Configuration

Model backends for tagging and wikilink injection are configurable at runtime via `/settings`. Configuration is stored in `store/config.json` and takes effect immediately (no restart needed).

| Task | Default backend | Recommended local model |
|---|---|---|
| Tagger | Anthropic `claude-haiku-4-5` | `qwen2.5:7b` (Q4, ~5 GB) |
| Linker | Anthropic `claude-sonnet-4-6` | `gemma3:27b` (Q4, ~16 GB) |

To use local models, install [Ollama](https://ollama.com) natively on macOS (not inside Docker — Docker on Mac cannot access Metal GPU):

```bash
brew install ollama
ollama pull qwen2.5:7b
ollama pull gemma3:27b
ollama serve   # starts at http://localhost:11434
```

Then open `/settings` in the UI, select the Ollama backend for each task, and save.
