import pytest
from unittest.mock import patch
from brain.tagger import extract_tags


def test_extract_tags_returns_existing_tags():
    """Existing tags short-circuit the LLM call entirely."""
    tags = extract_tags("Some text", existing_tags=["python", "pytest"])
    assert tags == ["python", "pytest"]


def test_extract_tags_skips_llm_for_empty_existing():
    """Empty existing_tags list should still trigger LLM."""
    with patch("brain.llm.chat", return_value='["ai", "ml"]') as mock_chat:
        tags = extract_tags("Some text", existing_tags=[])
    mock_chat.assert_called_once()
    assert tags == ["ai", "ml"]


def test_extract_tags_calls_llm_when_no_tags():
    """No existing tags triggers LLM and parses JSON response."""
    from unittest.mock import ANY
    with patch("brain.llm.chat", return_value='["ai", "machine-learning"]') as mock_chat:
        tags = extract_tags("Some text")
    mock_chat.assert_called_once_with(task="tagger", system=ANY, user=ANY, max_tokens=150)
    assert tags == ["ai", "machine-learning"]


def test_extract_tags_strips_markdown_fences():
    """LLM response wrapped in ```json fences is handled correctly."""
    with patch("brain.llm.chat", return_value='```json\n["tag-a", "tag-b"]\n```'):
        tags = extract_tags("Some text")
    assert tags == ["tag-a", "tag-b"]


def test_extract_tags_returns_empty_on_invalid_json():
    """Malformed JSON from LLM yields empty list, no exception."""
    with patch("brain.llm.chat", return_value="not json at all"):
        tags = extract_tags("Some text")
    assert tags == []


def test_extract_tags_returns_empty_on_llm_exception():
    """Exception during LLM call yields empty list."""
    with patch("brain.llm.chat", side_effect=RuntimeError("boom")):
        tags = extract_tags("Some text")
    assert tags == []
