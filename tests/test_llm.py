import json
import os
import pytest
from unittest.mock import MagicMock, patch


# ── load_config / save_config ─────────────────────────────────

def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(tmp_path / "config.json"))
    from brain import llm
    config = llm.load_config()
    assert config["tagger"]["backend"] == "anthropic"
    assert config["linker"]["backend"] == "anthropic"
    assert "ollama_base_url" in config


def test_load_config_merges_stored_values(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "ollama_base_url": "http://custom:11434",
        "tagger": {"backend": "ollama"},
    }))
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    config = llm.load_config()
    # stored value overrides default
    assert config["ollama_base_url"] == "http://custom:11434"
    assert config["tagger"]["backend"] == "ollama"
    # missing keys fall back to default
    assert "ollama_model" in config["tagger"]
    assert "anthropic_model" in config["linker"]


def test_save_config_writes_json(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    llm.save_config({"ollama_base_url": "http://test", "tagger": {}, "linker": {}})
    data = json.loads(cfg_path.read_text())
    assert data["ollama_base_url"] == "http://test"


def test_load_config_tolerates_corrupt_json(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("not valid json{{{")
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    config = llm.load_config()
    assert config == llm.load_config()  # idempotent, returns defaults


# ── pop_warnings ──────────────────────────────────────────────

def test_pop_warnings_clears_after_read():
    from brain import llm
    llm._pending_warnings.clear()
    llm._pending_warnings.append({"task": "tagger", "msg": "test"})
    first = llm.pop_warnings()
    second = llm.pop_warnings()
    assert len(first) == 1
    assert len(second) == 0


# ── _anthropic_chat ───────────────────────────────────────────

def test_anthropic_chat_returns_text():
    # Anthropic is imported lazily inside _anthropic_chat; patch at source
    from brain import llm
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="  result text  ")]
    with patch("anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = mock_response
        result = llm._anthropic_chat("claude-haiku-4-5", "sys", "user", 100)
    assert result == "result text"


def test_anthropic_chat_returns_empty_on_no_content():
    from brain import llm
    mock_response = MagicMock()
    mock_response.content = []
    with patch("anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = mock_response
        result = llm._anthropic_chat("claude-haiku-4-5", "sys", "user", 100)
    assert result == ""


# ── _ollama_chat ──────────────────────────────────────────────

def test_ollama_chat_returns_text_on_success():
    # ollama is an optional lazy import; inject a mock module via sys.modules
    import sys
    from brain import llm
    mock_ollama = MagicMock()
    mock_response = MagicMock()
    mock_response.message.content = "  ollama result  "
    mock_ollama.Client.return_value.chat.return_value = mock_response
    with patch.dict(sys.modules, {"ollama": mock_ollama}):
        result = llm._ollama_chat("http://localhost:11434", "qwen2.5:7b", "sys", "user", 100, 0.2)
    assert result == "ollama result"


def test_ollama_chat_returns_none_on_error():
    import sys
    from brain import llm
    mock_ollama = MagicMock()
    mock_ollama.Client.return_value.chat.side_effect = ConnectionError("refused")
    with patch.dict(sys.modules, {"ollama": mock_ollama}):
        result = llm._ollama_chat("http://localhost:11434", "qwen2.5:7b", "sys", "user", 100, 0.2)
    assert result is None


# ── chat() — routing and fallback ────────────────────────────

def test_chat_uses_anthropic_when_backend_is_anthropic(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "ollama_base_url": "http://localhost:11434",
        "tagger": {"backend": "anthropic", "anthropic_model": "claude-haiku-4-5",
                   "ollama_model": "qwen2.5:7b", "temperature": 0.2},
        "linker": {"backend": "anthropic", "anthropic_model": "claude-sonnet-4-6",
                   "ollama_model": "gemma3:27b", "temperature": 0.3},
    }))
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    with patch.object(llm, "_anthropic_chat", return_value="tags") as mock_ant, \
         patch.object(llm, "_ollama_chat") as mock_oll:
        result = llm.chat("tagger", "sys", "user", 150)
    assert result == "tags"
    mock_ant.assert_called_once()
    mock_oll.assert_not_called()


def test_chat_uses_ollama_when_backend_is_ollama(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "ollama_base_url": "http://localhost:11434",
        "tagger": {"backend": "ollama", "anthropic_model": "claude-haiku-4-5",
                   "ollama_model": "qwen2.5:7b", "temperature": 0.2},
        "linker": {"backend": "anthropic", "anthropic_model": "claude-sonnet-4-6",
                   "ollama_model": "gemma3:27b", "temperature": 0.3},
    }))
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    with patch.object(llm, "_ollama_chat", return_value="ollama-tags") as mock_oll, \
         patch.object(llm, "_anthropic_chat") as mock_ant:
        result = llm.chat("tagger", "sys", "user", 150)
    assert result == "ollama-tags"
    mock_oll.assert_called_once()
    mock_ant.assert_not_called()


def test_chat_falls_back_to_anthropic_when_ollama_fails(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "ollama_base_url": "http://localhost:11434",
        "tagger": {"backend": "ollama", "anthropic_model": "claude-haiku-4-5",
                   "ollama_model": "qwen2.5:7b", "temperature": 0.2},
        "linker": {"backend": "anthropic", "anthropic_model": "claude-sonnet-4-6",
                   "ollama_model": "gemma3:27b", "temperature": 0.3},
    }))
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    llm._pending_warnings.clear()
    with patch.object(llm, "_ollama_chat", return_value=None), \
         patch.object(llm, "_anthropic_chat", return_value="fallback") as mock_ant:
        result = llm.chat("tagger", "sys", "user", 150)
    assert result == "fallback"
    mock_ant.assert_called_once()
    warnings = llm.pop_warnings()
    assert len(warnings) == 1
    assert "tagger" in warnings[0]["msg"]
    assert "fallback" in warnings[0]["msg"].lower() or "anthropic" in warnings[0]["msg"].lower()
