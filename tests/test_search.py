import pytest
from unittest.mock import MagicMock
from brain.search import BrainSearch

def test_hybrid_search():
    mock_index = MagicMock()
    mock_graph = MagicMock()
    
    # Mock index getting all chunks for BM25
    mock_index.collection.get.return_value = {
        'ids': ['chunk1', 'chunk2'],
        'documents': ['apples and oranges', 'bananas and grapes'],
        'metadatas': [{'slug': 'doc1'}, {'slug': 'doc2'}]
    }
    
    # Mock vector search
    mock_index.query.return_value = [
        ('doc1', 'apples and oranges', 0.1),
        ('doc2', 'bananas and grapes', 0.9)
    ]
    
    # Mock graph neighbors
    mock_graph.get_neighbors.return_value = {
        'nodes': [{'id': 'doc1'}, {'id': 'doc3'}],
        'edges': []
    }
    
    search = BrainSearch(mock_index, mock_graph)
    results = search.hybrid_search("apples", limit=2)
    
    # doc1 should win because of BM25 + Vector + Graph boost
    assert len(results) == 2
    assert results[0][0] == 'doc1'
