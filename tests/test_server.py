import pytest
from fastapi.testclient import TestClient
from brain.server import app

client = TestClient(app)

def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "SECOND BRAIN TERMINAL" in response.text

def test_graph_page():
    response = client.get("/graph")
    assert response.status_code == 200
    assert "cy" in response.text

def test_upload_page():
    response = client.get("/upload")
    assert response.status_code == 200
    assert "UPLOAD" in response.text
