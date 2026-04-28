import os
import pytest
from unittest.mock import MagicMock, patch
from brain.parser import parse_pdf

@patch("brain.parser.fitz.open")
@patch("brain.parser.pymupdf4llm.to_markdown")
def test_parse_pdf(mock_to_markdown, mock_fitz_open, tmp_path):
    # Setup mocks
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 15  # 15 pages
    mock_fitz_open.return_value = mock_doc
    
    mock_to_markdown.side_effect = ["Markdown chunk 1\n", "Markdown chunk 2\n"]
    
    # Run parser
    slug = "test-pdf"
    file_path = "/fake/path/test.pdf"
    
    # We patch IMAGES_STORE_DIR to avoid writing to real paths during test
    with patch("brain.parser.IMAGES_STORE_DIR", str(tmp_path)):
        md_text, images = parse_pdf(file_path, slug)
        
    assert "Markdown chunk 1" in md_text
    assert "Markdown chunk 2" in md_text
    
    # fitz.open was called
    mock_fitz_open.assert_called_once_with(file_path)
    
    # to_markdown should be called twice (pages 0-9, then 10-14)
    assert mock_to_markdown.call_count == 2
