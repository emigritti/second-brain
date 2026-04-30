import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from brain.server import app

client = TestClient(app)


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "SECOND BRAIN" in response.text


def test_graph_page():
    response = client.get("/graph")
    assert response.status_code == 200
    assert "cy" in response.text


def test_upload_page():
    response = client.get("/upload")
    assert response.status_code == 200
    assert "UPLOAD" in response.text


def test_settings_page_renders(tmp_path, monkeypatch):
    """Settings page loads and shows section titles."""
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(tmp_path / "config.json"))
    response = client.get("/settings")
    assert response.status_code == 200
    assert "TAGGER" in response.text
    assert "LINKER" in response.text
    assert "OLLAMA" in response.text


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


@pytest.mark.parametrize("endpoint", ["/settings/test-ollama", "/settings/test-localai"])
def test_test_local_backend_success(endpoint):
    """Both test endpoints call list_openai_models and return the model list."""
    with patch("brain.llm.list_openai_models", return_value=["qwen2.5:7b", "gemma3:27b"]):
        response = client.post(endpoint, json={"base_url": "http://localhost:11434"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "qwen2.5:7b" in data["models"]


@pytest.mark.parametrize("endpoint", ["/settings/test-ollama", "/settings/test-localai"])
def test_test_local_backend_failure(endpoint):
    """Both test endpoints surface errors as ok=False with a message."""
    with patch("brain.llm.list_openai_models", side_effect=ConnectionError("refused")):
        response = client.post(endpoint, json={"base_url": "http://localhost:11434"})
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
