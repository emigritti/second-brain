# ADR 0006: Reintroduce Ollama Alongside LocalAI

## Status

Accepted — 2026-04-30.

Amends [ADR 0005](0005-local-models-ollama.md).

## Context

[ADR 0005](0005-local-models-ollama.md) introduced Ollama as the optional local LLM backend for `tagger.py` and `linker.py`. Shortly after acceptance, a macOS-specific compatibility issue made the Ollama-on-host + Docker-brain setup unreachable, and the local backend was hastily migrated to **LocalAI + llama.cpp** running as a Docker service. That migration was not captured in an ADR.

The macOS issue has now been resolved. The user wants Ollama back — specifically because it provides direct Apple Silicon Metal acceleration when run natively on the host, which LocalAI's `latest-aio-cpu` image cannot match — but LocalAI has now been validated in production and there is no reason to remove it. Different deployments have different constraints:

- A Linux server with no GPU benefits from LocalAI running entirely inside Docker, no host setup required.
- A developer laptop on Apple Silicon benefits from Ollama running natively on the host with Metal.

## Decision

Make `backend` a three-valued field per task: `"anthropic" | "localai" | "ollama"`. Both LocalAI and Ollama are first-class local backends, selectable per task in the existing `/settings` UI. Anthropic remains the default and the universal fallback.

Implementation:

1. **Single OpenAI-SDK client for both local backends.** Ollama exposes an OpenAI-compatible API at `/v1/chat/completions` and `/v1/models`, identical in shape to LocalAI's. `brain/llm.py` factors a generic `_openai_chat(base_url, model, ...)` and `list_openai_models(base_url)` helper that serves both backends — no `ollama` Python SDK dependency.
2. **Per-backend URL and per-task model.** `DEFAULT_CONFIG` gains `ollama_base_url` (default `http://host.docker.internal:11434`, since Ollama runs on the host on macOS for Metal access) alongside the existing `localai_base_url`. Each task config carries both `localai_model` and `ollama_model` so switching backends preserves each one's selection.
3. **Settings UI.** Adds an OLLAMA CONNECTION section (BASE URL + TEST CONNECTION) and a third radio `OLLAMA` to the Tagger and Linker backend toggles. The existing `applyVisibility(task, backend)` JS already supports N values.
4. **Server route.** New `POST /settings/test-ollama`, parallel to `/settings/test-localai`. Both endpoints internally call `llm.list_openai_models(base_url)`.
5. **Docker.** No new service; Ollama runs natively on the host. Adds `extra_hosts: ["host.docker.internal:host-gateway"]` to the `brain` service so the default URL resolves on Linux hosts (Mac/Windows Docker Desktop already inject this automatically).
6. **Back-compat.** `load_config()` migrates legacy `local_model` keys (from the LocalAI-only schema written between 2026-04-29 and 2026-04-30) to `localai_model` on read, so existing `store/config.json` files keep working without manual edits.

## Rationale

1. **Why keep LocalAI rather than rip it out** — The interim work hardened the OpenAI-compatible code path, which is now reused for Ollama too. Keeping both backends costs essentially one extra config key and a UI section, and gives users a real choice between Docker-native and host-native local inference.
2. **Why use Ollama's OpenAI-compatible endpoint instead of the `ollama` Python SDK** — A single client implementation eliminates the dual lazy-import patching pattern in tests, avoids a second optional dependency, and makes the dispatch logic trivially uniform across local backends.
3. **Why `host.docker.internal` as the default Ollama URL** — Ollama on macOS must run natively for Metal GPU access (per ADR 0005 §1 and `MEMORY.md`); the brain container needs to reach the host. Docker Desktop on Mac/Windows resolves this hostname automatically; on Linux the `extra_hosts` mapping makes it work too.
4. **Anthropic remains the safety net** — Both local backends fall back to Anthropic on error, with the failure surfaced in the ingestion log.

## Consequences

- **Positive** — Users on Apple Silicon get native Metal performance via Ollama; users without a host LLM runtime get LocalAI in-container. No deployment is forced into a configuration that doesn't fit it.
- **Positive** — One client implementation (`_openai_chat`) covers both backends; tests no longer need the `sys.modules` patch trick that the original Ollama SDK required.
- **Positive** — Legacy configs from the brief LocalAI-only window auto-migrate on first load.
- **Negative** — `DEFAULT_CONFIG` and the Settings UI grow by one section. Two backend names to document and explain to operators.
- **Neutral** — `vision.py` and `query.py` still call Anthropic exclusively (per ADR 0005 §5). No change to that scope boundary.

## Verification

1. `pytest tests/test_llm.py tests/test_server.py` — green.
2. From `/settings`: enter `http://localhost:11434` (or `host.docker.internal:11434` from inside Docker) → TEST CONNECTION returns the Ollama model list.
3. Switch Tagger backend to OLLAMA, save, drop a file in `raw/` — ingestion succeeds with no fallback warning in the log.
4. Switch Tagger backend to LOCALAI — same flow still works (regression check).
