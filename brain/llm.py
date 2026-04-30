import os
import json
import threading
from typing import Literal

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "store", "config.json")

DEFAULT_CONFIG: dict = {
    "localai_base_url": "http://localai:8080",
    "tagger": {
        "backend": "anthropic",
        "local_model": "mistral-7b-instruct",
        "anthropic_model": "claude-haiku-4-5",
        "temperature": 0.2,
    },
    "linker": {
        "backend": "anthropic",
        "local_model": "mistral-7b-instruct",
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
                result[key] = {**default_val, **stored.get(key, {})}
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

    if backend == "localai":
        result = _localai_chat(
            base_url=config["localai_base_url"],
            model=task_cfg["local_model"],
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if result is not None:
            return result
        msg = (
            f"LocalAI unavailable for '{task}' "
            f"(model: {task_cfg['local_model']}), "
            f"falling back to Anthropic ({task_cfg['anthropic_model']})"
        )
        print(f"[llm] {msg}")
        with _warn_lock:
            _pending_warnings.append({"task": task, "msg": msg})

    return _anthropic_chat(
        model=task_cfg["anthropic_model"],
        system=system,
        user=user,
        max_tokens=max_tokens,
    )


def list_localai_models(base_url: str) -> list[str]:
    from openai import OpenAI
    client = OpenAI(base_url=f"{base_url.rstrip('/')}/v1", api_key="none")
    response = client.models.list()
    return [m.id for m in response.data]


def _localai_chat(
    base_url: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
) -> str | None:
    try:
        from openai import OpenAI
        client = OpenAI(base_url=f"{base_url.rstrip('/')}/v1", api_key="none")
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
        print(f"[llm] LocalAI error: {e}")
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
