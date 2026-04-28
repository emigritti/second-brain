import pytest
from unittest.mock import patch
from brain.tagger import extract_tags

def test_extract_tags_existing():
    """Test that existing tags short-circuit the LLM call."""
    tags = extract_tags("Some text", existing_tags=["python", "pytest"])
    assert tags == ["python", "pytest"]

@patch("brain.tagger.client.messages.create")
def test_extract_tags_llm(mock_create):
    """Test that LLM is called if no existing tags."""
    class MockMessage:
        @property
        def text(self):
            return '["ai", "machine-learning"]'
            
    class MockContent:
        @property
        def content(self):
            return [MockMessage()]
            
    mock_create.return_value = MockContent()
    
    tags = extract_tags("Some text", existing_tags=[])
    
    assert mock_create.called
    assert tags == ["ai", "machine-learning"]
