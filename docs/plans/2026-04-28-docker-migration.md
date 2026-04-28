# Docker Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Package the second-brain application as a reproducible Docker image with compose orchestration for local and CI deployment.

**Architecture:** Single-container setup (FastAPI + watchdog in one process) with named volumes for persistent state (`store/` and `raw/`). No separate services needed — ChromaDB runs embedded, SQLite is file-based. A `docker-compose.yml` provides the developer-facing interface; the raw `Dockerfile` enables future CI/CD use.

**Tech Stack:** Python 3.11-slim base image, docker compose v2, named volumes for `store/` and `raw/`.

---

### Task 1: ADR-0004 — Record the Docker decision

**Files:**
- Create: `docs/ADR/0004-containerize-with-docker.md`

**Step 1: Write the ADR**

See ADR template in `docs/ADR/0001-drop-sqlite-for-markdown.md` for style reference.

**Step 2: Commit**

```bash
git add docs/ADR/0004-containerize-with-docker.md
git commit -m "docs: ADR-0004 containerize second-brain with Docker"
```

---

### Task 2: .env.example

**Files:**
- Create: `.env.example`

**Step 1: Write the file**

```env
# Required — get yours at https://console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides
BRAIN_ROOT=./store
QUERY_CONFIDENCE_THRESHOLD=0.72
SERVER_PORT=8000
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: add .env.example"
```

---

### Task 3: .dockerignore

**Files:**
- Create: `.dockerignore`

**Step 1: Write the file** (keep image lean; exclude data volumes, dev artifacts)

```
.git
.gitignore
__pycache__
*.pyc
*.pyo
.pytest_cache
.mypy_cache
.venv
venv
*.egg-info
dist
build
store/
raw/
vault/
docs/
tests/
*.md
.env
.env.*
!.env.example
```

**Step 2: Commit**

```bash
git add .dockerignore
git commit -m "chore: add .dockerignore"
```

---

### Task 4: Dockerfile

**Files:**
- Create: `Dockerfile`

**Step 1: Write the Dockerfile**

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        pkg-config \
        libssl-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY brain/ brain/
COPY static/ static/
COPY templates/ templates/

RUN mkdir -p raw store/documents store/images store/chroma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["python", "-m", "brain.app"]
```

**Step 2: Build and verify locally**

```bash
docker build -t second-brain:local .
```

Expected: successful build, ~1-2 GB image.

**Step 3: Commit**

```bash
git add Dockerfile
git commit -m "feat: add Dockerfile for second-brain"
```

---

### Task 5: docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

**Step 1: Write the file**

```yaml
services:
  brain:
    build: .
    image: second-brain:local
    ports:
      - "${SERVER_PORT:-8000}:8000"
    env_file:
      - .env
    volumes:
      - brain-store:/app/store
      - brain-raw:/app/raw
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
      interval: 30s
      timeout: 10s
      start_period: 30s
      retries: 3

volumes:
  brain-store:
  brain-raw:
```

**Step 2: Smoke-test with compose**

```bash
docker compose up --build -d
docker compose ps
docker compose logs brain
```

Expected: container running, healthy after ~30s.

**Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose.yml for local orchestration"
```

---

### Task 6: Update documentation

**Files:**
- Modify: `docs/architecture.md`
- Create: `docs/how-to/run-with-docker.md`

**Step 1: Add Docker section to architecture.md**

Append a "## Deployment" section describing the single-container model and volume layout.

**Step 2: Write how-to/run-with-docker.md**

```markdown
# Run with Docker

## Prerequisites
- Docker 24+ and Docker Compose v2
- An Anthropic API key

## Quick start

    cp .env.example .env
    # edit .env and set ANTHROPIC_API_KEY
    docker compose up --build

Open http://localhost:8000 in your browser.

## Persisting data

All knowledge base data lives in named Docker volumes:

| Volume | Purpose |
|--------|---------|
| `brain-store` | Markdown docs, ChromaDB embeddings, extracted images |
| `brain-raw` | PDF staging area (auto-ingested by watchdog) |

## Ingesting a PDF

    docker compose cp my-paper.pdf brain:/app/raw/
    # watchdog picks it up automatically within ~2s

## Rebuilding the vector index

    docker compose exec brain python -m brain.index --rebuild

## Stopping and cleaning up

    docker compose down          # stop, keep volumes
    docker compose down -v       # stop + delete all data
```

**Step 3: Commit**

```bash
git add docs/
git commit -m "docs: add Docker deployment guide and update architecture"
```

---

### Task 7: Run tests and verify

**Step 1: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass (tests mock external APIs, no live network needed).

**Step 2: If tests fail**, fix the issue before proceeding.

---

### Task 8: Final push to main

```bash
git push origin main
```
