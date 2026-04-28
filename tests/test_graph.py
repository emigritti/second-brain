import os
import pytest
from brain.graph import BrainGraph

@pytest.fixture
def temp_graph(tmp_path, monkeypatch):
    # Override the store directory to use the pytest temp directory
    store_dir = tmp_path / "documents"
    store_dir.mkdir()
    
    # Create the graph
    graph = BrainGraph()
    graph.store_dir = str(store_dir)
    return graph

def test_upsert_document(temp_graph):
    temp_graph.upsert_document(
        slug="test-doc",
        title="Test Document",
        text="This is a test document with a [[wikilink]].",
        tags=["test", "pytest"]
    )
    
    # Reload from files to check if it parsed correctly
    temp_graph._load_from_files()
    
    assert temp_graph.graph.has_node("test-doc")
    node_data = temp_graph.graph.nodes["test-doc"]
    assert node_data["title"] == "Test Document"
    assert "test" in node_data["tags"]
    
    # Check if wikilink created a dangling edge
    assert temp_graph.graph.has_edge("test-doc", "wikilink")

def test_neighbor_traversal(temp_graph):
    # Create two connected documents
    temp_graph.upsert_document(
        slug="doc1",
        title="Doc 1",
        text="Links to [[doc2]]",
        tags=[]
    )
    temp_graph.upsert_document(
        slug="doc2",
        title="Doc 2",
        text="I am doc 2",
        tags=[]
    )
    
    temp_graph._load_from_files()
    
    neighbors = temp_graph.get_neighbors("doc1", hops=1)
    
    node_ids = [n["id"] for n in neighbors["nodes"]]
    assert "doc1" in node_ids
    assert "doc2" in node_ids
    
    # Verify edge
    assert len(neighbors["edges"]) == 1
    edge = neighbors["edges"][0]
    assert edge["source"] == "doc1"
    assert edge["target"] == "doc2"
