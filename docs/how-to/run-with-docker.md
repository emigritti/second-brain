# Run with Docker

## Prerequisites

- Docker 24+ with Docker Compose v2 (`docker compose` — note: no hyphen)
- An Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

## Quick start

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000) in your browser (or whichever port you set via `SERVER_PORT`). The UI is ready once the health-check turns green (about 30 s).

## Persisting data

All knowledge base data lives in named Docker volumes — they survive container restarts and rebuilds:

| Volume | Purpose |
|--------|---------|
| `brain-store` | Markdown documents, ChromaDB embeddings, extracted images |
| `brain-raw` | PDF staging area (watchdog ingests files placed here) |

## Ingesting a PDF

Copy a PDF into the running container's `raw/` directory. The watchdog picks it up automatically within a few seconds:

```bash
docker compose cp my-paper.pdf brain:/app/raw/
```

> **Windows + WSL2 note:** `inotify` events may not fire reliably when a bind-mount is used instead of a named volume. The named volume setup in `docker-compose.yml` avoids this issue. Always use `docker compose cp` rather than mounting a host directory for ingestion.

## Useful commands

```bash
# Rebuild the vector index from scratch
docker compose exec brain python -m brain.index --rebuild

# Export the knowledge graph
docker compose exec brain python -m brain.graph export /tmp/graph.json
docker compose cp brain:/tmp/graph.json ./graph.json

# Tail logs
docker compose logs -f brain

# Open a shell inside the container
docker compose exec brain bash
```

## Stopping and cleaning up

```bash
# Stop the container, keep all data
docker compose down

# Stop and delete all data (irreversible)
docker compose down -v
```

## Changing the port

Set `SERVER_PORT` in your `.env` file (useful if port 8000 is already in use):

```env
SERVER_PORT=8765
```

Then restart: `docker compose up -d`.

## Running tests inside the container

```bash
docker compose run --rm brain pytest -v
```
