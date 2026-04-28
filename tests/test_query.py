import pytest
from unittest.mock import MagicMock, patch
from brain.query import QueryEngine

@patch("brain.query.client.messages.create")
def test_query_routing(mock_create):
    mock_search = MagicMock()
    
    # Return high scores to trigger Haiku
    mock_search.hybrid_search.return_value = [
        ('doc1', 'text 1', 0.9),
        ('doc2', 'text 2', 0.8)
    ]
    
    class MockMessage:
        @property
        def text(self):
            return 'High confidence answer.'
            
    class MockContent:
        @property
        def content(self):
            return [MockMessage()]
            
    mock_create.return_value = MockContent()
    
    engine = QueryEngine(mock_search)
    answer, sources = engine.query("What is this?")
    
    assert answer == "High confidence answer."
    assert set(sources) == {'doc1', 'doc2'}
    
    # Verify the model used was Haiku
    args, kwargs = mock_create.call_args
    assert kwargs['model'] == 'claude-3-5-haiku-latest'
