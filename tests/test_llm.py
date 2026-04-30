import json
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
    assert "localai_base_url" in config


def test_load_config_merges_stored_values(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "ollama_base_url": "http://custom:11434",
        "tagger": {"backend": "ollama"},
    }))
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    config = llm.load_config()
    assert config["ollama_base_url"] == "http://custom:11434"
    assert config["tagger"]["backend"] == "ollama"
    assert "ollama_model" in config["tagger"]
    assert "localai_model" in config["tagger"]
    assert "anthropic_model" in config["linker"]


def test_load_config_migrates_legacy_local_model(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "tagger": {"backend": "localai", "local_model": "legacy-model"},
    }))
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    config = llm.load_config()
    assert config["tagger"]["localai_model"] == "legacy-model"


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


# ── _openai_chat (LocalAI / Ollama share this path) ───────────

def test_openai_chat_returns_text_on_success():
    from brain import llm
    mock_choice = MagicMock()
    mock_choice.message.content = "  openai-compat result  "
    mock_response = MagicMock(choices=[mock_choice])
    with patch("openai.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = mock_response
        result = llm._openai_chat("http://localhost:11434", "qwen2.5:7b", "sys", "user", 100, 0.2)
    assert result == "openai-compat result"


def test_openai_chat_returns_none_on_error():
    from brain import llm
    with patch("openai.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = ConnectionError("refused")
        result = llm._openai_chat("http://localhost:11434", "qwen2.5:7b", "sys", "user", 100, 0.2)
    assert result is None


def test_list_openai_models_returns_ids():
    from brain import llm
    mock_response = MagicMock()
    mock_response.data = [MagicMock(id="qwen2.5:7b"), MagicMock(id="gemma3:27b")]
    with patch("openai.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.models.list.return_value = mock_response
        result = llm.list_openai_models("http://localhost:11434")
    assert result == ["qwen2.5:7b", "gemma3:27b"]


def test_list_openai_models_returns_empty_on_error():
    from brain import llm
    with patch("openai.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.models.list.side_effect = ConnectionError("refused")
        result = llm.list_openai_models("http://localhost:11434")
    assert result == []


# ── chat() — routing and fallback ────────────────────────────

def _write_cfg(path, tagger_backend="anthropic"):
    path.write_text(json.dumps({
        "localai_base_url": "http://localai:8080",
        "ollama_base_url": "http://localhost:11434",
        "tagger": {"backend": tagger_backend, "anthropic_model": "claude-haiku-4-5",
                   "localai_model": "mistral-7b-instruct",
                   "ollama_model": "qwen2.5:7b", "temperature": 0.2},
        "linker": {"backend": "anthropic", "anthropic_model": "claude-sonnet-4-6",
                   "localai_model": "mistral-7b-instruct",
                   "ollama_model": "gemma3:27b", "temperature": 0.3},
    }))


def test_chat_uses_anthropic_when_backend_is_anthropic(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    _write_cfg(cfg_path, "anthropic")
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    with patch.object(llm, "_anthropic_chat", return_value="tags") as mock_ant, \
         patch.object(llm, "_openai_chat") as mock_oai:
        result = llm.chat("tagger", "sys", "user", 150)
    assert result == "tags"
    mock_ant.assert_called_once()
    mock_oai.assert_not_called()


@pytest.mark.parametrize("backend,expected_url", [
    ("ollama", "http://localhost:11434"),
    ("localai", "http://localai:8080"),
])
def test_chat_routes_to_openai_for_local_backends(tmp_path, monkeypatch, backend, expected_url):
    cfg_path = tmp_path / "config.json"
    _write_cfg(cfg_path, backend)
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    with patch.object(llm, "_openai_chat", return_value=f"{backend}-tags") as mock_oai, \
         patch.object(llm, "_anthropic_chat") as mock_ant:
        result = llm.chat("tagger", "sys", "user", 150)
    assert result == f"{backend}-tags"
    mock_oai.assert_called_once()
    assert mock_oai.call_args.kwargs["base_url"] == expected_url
    mock_ant.assert_not_called()


@pytest.mark.parametrize("backend", ["ollama", "localai"])
def test_chat_falls_back_to_anthropic_when_local_fails(tmp_path, monkeypatch, backend):
    cfg_path = tmp_path / "config.json"
    _write_cfg(cfg_path, backend)
    monkeypatch.setattr("brain.llm.CONFIG_PATH", str(cfg_path))
    from brain import llm
    llm._pending_warnings.clear()
    with patch.object(llm, "_openai_chat", return_value=None), \
         patch.object(llm, "_anthropic_chat", return_value="fallback") as mock_ant:
        result = llm.chat("tagger", "sys", "user", 150)
    assert result == "fallback"
    mock_ant.assert_called_once()
    warnings = llm.pop_warnings()
    assert len(warnings) == 1
    assert "tagger" in warnings[0]["msg"]
    assert backend in warnings[0]["msg"].lower()
