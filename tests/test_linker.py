import pytest
from unittest.mock import patch
from brain.linker import inject_wikilinks


def test_inject_wikilinks_skips_when_no_existing_slugs():
    """No slugs → original text returned without any LLM call."""
    with patch("brain.llm.chat") as mock_chat:
        result = inject_wikilinks("my-doc", "# Hello world", [])
    mock_chat.assert_not_called()
    assert result == "# Hello world"


def test_inject_wikilinks_calls_llm_with_slugs():
    """With existing slugs, LLM is called and updated text returned."""
    from unittest.mock import ANY
    updated = "# Hello [[other-doc]] world"
    with patch("brain.llm.chat", return_value=updated) as mock_chat:
        result = inject_wikilinks("my-doc", "# Hello other-doc world", ["other-doc"])
    mock_chat.assert_called_once_with(task="linker", system=ANY, user=ANY, max_tokens=4096)
    assert result == updated


def test_inject_wikilinks_passes_slug_exclusion():
    """The document's own slug is mentioned in the user prompt to avoid self-links."""
    with patch("brain.llm.chat", return_value="# Long enough text " * 20) as mock_chat:
        inject_wikilinks("self-slug", "# Long enough text " * 20, ["other-doc"])
    call_user = mock_chat.call_args.kwargs["user"]
    assert "self-slug" in call_user


def test_inject_wikilinks_safety_check_keeps_original():
    """If LLM returns text shorter than 50% of original, keep original."""
    original = "# " + "x " * 200
    with patch("brain.llm.chat", return_value="short"):
        result = inject_wikilinks("doc", original, ["other"])
    assert result == original


def test_inject_wikilinks_returns_original_on_exception():
    """LLM exception yields original text, no exception propagated."""
    original = "# Some document text"
    with patch("brain.llm.chat", side_effect=RuntimeError("network error")):
        result = inject_wikilinks("doc", original, ["other-doc"])
    assert result == original
