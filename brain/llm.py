import os
import json
import threading
from typing import Literal

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "store", "config.json")

DEFAULT_CONFIG: dict = {
    "localai_base_url": "http://localai:8080",
    "ollama_base_url": "http://host.docker.internal:11434",
    "anthropic_require_approval": False,
    "anthropic_fallback_enabled": True,
    "vision_enabled": True,
    "query_escalation_enabled": True,
    "tagger": {
        "backend": "anthropic",
        "localai_model": "mistral-7b-instruct",
        "ollama_model": "qwen2.5:7b",
        "anthropic_model": "claude-haiku-4-5",
        "temperature": 0.2,
    },
    "linker": {
        "backend": "anthropic",
        "localai_model": "mistral-7b-instruct",
        "ollama_model": "gemma3:27b",
        "anthropic_model": "claude-sonnet-4-6",
        "temperature": 0.3,
    },
}

_warn_lock = threading.Lock()
_pending_warnings: list[dict] = []


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            stored = json.load(f)
        result: dict = {}
        for key, default_val in DEFAULT_CONFIG.items():
            if isinstance(default_val, dict):
                merged = {**default_val, **stored.get(key, {})}
                if "local_model" in stored.get(key, {}) and "localai_model" not in stored.get(key, {}):
                    merged["localai_model"] = stored[key]["local_model"]
                result[key] = merged
            else:
                result[key] = stored.get(key, default_val)
        return result
    except (FileNotFoundError, json.JSONDecodeError):
        return {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULT_CONFIG.items()}


def save_config(config: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def pop_warnings() -> list[dict]:
    """Consume and return any pending fallback warnings (called by ingest.py)."""
    with _warn_lock:
        warnings = _pending_warnings.copy()
        _pending_warnings.clear()
        return warnings


_LOCAL_BACKENDS = {
    "localai": ("localai_base_url", "localai_model"),
    "ollama": ("ollama_base_url", "ollama_model"),
}


def chat(
    task: Literal["tagger", "linker"],
    system: str,
    user: str,
    max_tokens: int = 1024,
) -> str:
    config = load_config()
    task_cfg = config[task]
    backend = task_cfg["backend"]
    temperature = float(task_cfg.get("temperature", 0.3))

    if backend in _LOCAL_BACKENDS:
        url_key, model_key = _LOCAL_BACKENDS[backend]
        model = task_cfg[model_key]
        result = _openai_chat(
            base_url=config[url_key],
            model=model,
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if result is not None:
            return result
        if not config.get("anthropic_fallback_enabled", True):
            msg = (
                f"{backend} unavailable for '{task}' "
                f"(model: {model}), "
                f"Anthropic fallback is disabled"
            )
            print(f"[llm] {msg}")
            with _warn_lock:
                _pending_warnings.append({"task": task, "msg": msg})
            return ""
        msg = (
            f"{backend} unavailable for '{task}' "
            f"(model: {model}), "
            f"falling back to Anthropic ({task_cfg['anthropic_model']})"
        )
        print(f"[llm] {msg}")
        with _warn_lock:
            _pending_warnings.append({"task": task, "msg": msg})
    elif backend != "anthropic":
        print(f"[llm] Unknown backend '{backend}' for '{task}', falling back to Anthropic")

    return _anthropic_chat(
        model=task_cfg["anthropic_model"],
        system=system,
        user=user,
        max_tokens=max_tokens,
    )


def _make_openai_client(base_url: str):
    from openai import OpenAI
    return OpenAI(base_url=f"{base_url.rstrip('/')}/v1", api_key="none")


def list_openai_models(base_url: str) -> list[str]:
    try:
        client = _make_openai_client(base_url)
        response = client.models.list()
        return [m.id for m in response.data]
    except Exception as e:
        print(f"[llm] list_openai_models error: {e}")
        return []


def _openai_chat(
    base_url: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
) -> str | None:
    try:
        client = _make_openai_client(base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[llm] OpenAI-compatible backend error ({base_url}): {e}")
        return None


def _anthropic_chat(model: str, system: str, user: str, max_tokens: int) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip() if response.content else ""
