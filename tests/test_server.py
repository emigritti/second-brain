import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from brain.server import app

client = TestClient(app)



def test_settings_save_valid(tmp_path, monkeypatch):
    """POST /settings with valid form data returns saved status."""
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(tmp_path / "config.json"))
    response = client.post("/settings", data={
        "ollama_base_url": "http://localhost:11434",
        "tagger_backend": "ollama",
        "tagger_ollama_model": "qwen2.5:7b",
        "tagger_anthropic_model": "claude-haiku-4-5",
        "tagger_temperature": "0.2",
        "linker_backend": "anthropic",
        "linker_ollama_model": "gemma3:27b",
        "linker_anthropic_model": "claude-sonnet-4-6",
        "linker_temperature": "0.3",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    saved = json.loads((tmp_path / "config.json").read_text())
    assert saved["tagger"]["backend"] == "ollama"
    assert saved["linker"]["backend"] == "anthropic"


def test_settings_save_invalid_temperature(tmp_path, monkeypatch):
    """POST /settings with non-numeric temperature returns 400."""
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(tmp_path / "config.json"))
    response = client.post("/settings", data={
        "ollama_base_url": "http://localhost:11434",
        "tagger_backend": "anthropic",
        "tagger_ollama_model": "qwen2.5:7b",
        "tagger_anthropic_model": "claude-haiku-4-5",
        "tagger_temperature": "not-a-number",
        "linker_backend": "anthropic",
        "linker_ollama_model": "gemma3:27b",
        "linker_anthropic_model": "claude-sonnet-4-6",
        "linker_temperature": "0.3",
    })
    assert response.status_code == 400


def test_test_ollama_success():
    """POST /settings/test-ollama returns ok=True and model list on success."""
    with patch("brain.llm.list_ollama_models", return_value=["qwen2.5:7b", "gemma3:27b"]):
        response = client.post(
            "/settings/test-ollama",
            json={"base_url": "http://localhost:11434"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "qwen2.5:7b" in data["models"]


def test_test_ollama_failure():
    """POST /settings/test-ollama returns ok=False with error message on failure."""
    with patch("brain.llm.list_ollama_models", side_effect=ConnectionError("refused")):
        response = client.post(
            "/settings/test-ollama",
            json={"base_url": "http://localhost:11434"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "error" in data


def test_ingest_log_empty():
    """GET /ingest/log returns an empty list when no ingestions have run."""
    from brain.ingest import INGEST_LOG
    INGEST_LOG.clear()
    response = client.get("/ingest/log")
    assert response.status_code == 200
    assert response.json() == []
