# ADR 0005: Optional Local LLM Backend via Ollama

## Context

The ingestion pipeline calls the Anthropic Claude API on every document ingested — once for tagging (`tagger.py`) and once for wikilink injection (`linker.py`). On a high-ingestion workload these calls accumulate quickly, exhausting API rate limits and incurring recurring cost.

The target deployment machine (Mac M5, 32 GB unified RAM) is capable of running quantised open-weights models locally at useful quality. Ollama provides a simple runtime for these models and exposes a stable Python SDK.

ADR 0003 chose Claude exclusively. This ADR amends that decision for the two high-volume enrichment tasks.

## Decision

Introduce an optional Ollama backend for `tagger.py` and `linker.py`, selectable per-task at runtime via a new `/settings` page. The Anthropic backend remains available and is the default.

A new `brain/llm.py` module owns all provider logic. `tagger.py` and `linker.py` call `llm.chat(task, system, user, max_tokens)` instead of constructing Anthropic clients directly. Configuration is persisted in `store/config.json`.

## Rationale

1. **Hardware fit** — Quantised 7–27B models run entirely in unified RAM on Apple Silicon with Metal acceleration. `qwen2.5:7b` (Q4, ~5 GB) is sufficient for tagging; `gemma3:27b` (Q4, ~16 GB) handles wikilink reasoning. Both fit comfortably alongside Docker workloads within 32 GB.
2. **Graceful fallback** — If Ollama is unreachable the system falls back to Anthropic automatically, and the fallback is surfaced in the `/settings` ingestion log so the operator knows what happened.
3. **Zero mandatory dependency** — `ollama` is imported lazily inside `_ollama_chat()`. The system starts and runs normally without Ollama installed.
4. **Runtime configurability** — Model names, temperatures, and Anthropic model overrides are editable in the UI without restarting the server.
5. **Scope boundary** — `vision.py` and `query.py` continue to use Anthropic exclusively. Vision requires a multimodal model; query quality is user-facing and warrants the best available model.

## Consequences

- **Positive**: Near-zero API cost during bulk ingestion when Ollama is configured.
- **Positive**: No hard dependency on Ollama — existing deployments (Docker, CI) continue working unchanged.
- **Negative**: First-time setup requires `ollama pull <model>` on the host machine.
- **Negative**: Local inference is slower than Haiku for tagging; acceptable since ingestion is already a background task.
- **Neutral**: `store/config.json` is created on first save. Absent file = all defaults (Anthropic).
