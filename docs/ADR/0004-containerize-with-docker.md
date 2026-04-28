# ADR 0004: Containerize with Docker

## Context

The application currently runs directly on the developer's host machine. This requires manual Python environment setup, compatible native library versions (PyMuPDF, ChromaDB), and correct path configuration. Onboarding is fragile and environment drift causes hard-to-reproduce bugs.

## Decision

We containerize the application using a single Docker image (`Dockerfile`) and provide a `docker-compose.yml` for local orchestration. Persistent state (`store/`, `raw/`) lives in named Docker volumes.

## Rationale

1. **Reproducible environments**: Every contributor runs the exact same Python version, native libraries, and system packages — eliminating "works on my machine" failures caused by PyMuPDF or ChromaDB native extension mismatches.
2. **Zero-config onboarding**: `cp .env.example .env && docker compose up` is the entire setup. No virtualenv, no `apt` packages, no PATH gymnastics.
3. **Data portability**: Named volumes decouple the knowledge base lifecycle from the container lifecycle. `docker compose down` does not destroy notes; `docker compose down -v` is an explicit, deliberate wipe.
4. **Single-container simplicity**: ChromaDB is embedded and SQLite-free. No need for a multi-service compose setup (no separate DB container). One container, one port.

## Consequences

- **Positive**: Consistent builds across macOS, Linux, and Windows (via Docker Desktop). Easy to integrate into CI pipelines later.
- **Negative**: The image is large (~1.5-2 GB) due to PyMuPDF and ChromaDB native extensions. First `docker compose up --build` takes several minutes.
- **Negative**: File-watching via `watchdog` works correctly inside the container only when PDFs are copied with `docker compose cp`, not via bind-mounts on some Windows + WSL2 configurations (inotify limitation). Documented in `docs/how-to/run-with-docker.md`.
