import os
import pytest
from unittest.mock import MagicMock, patch
from brain.parser import parse_pdf, parse_document, MARKITDOWN_EXTENSIONS

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


# --- parse_document dispatcher tests ---

@patch("brain.parser.parse_pdf")
def test_parse_document_routes_pdf(mock_parse_pdf):
    mock_parse_pdf.return_value = ("# PDF content", ["/img/a.png"])
    result = parse_document("doc.pdf", "doc")
    mock_parse_pdf.assert_called_once_with("doc.pdf", "doc")
    assert result == ("# PDF content", ["/img/a.png"])


@patch("markitdown.MarkItDown")
def test_parse_document_routes_docx(mock_md_class):
    mock_md_class.return_value.convert.return_value.text_content = "# Hello"
    markdown, images = parse_document("report.docx", "report")
    assert markdown == "# Hello"
    assert images == []


@pytest.mark.parametrize("ext", sorted(MARKITDOWN_EXTENSIONS))
@patch("markitdown.MarkItDown")
def test_parse_document_returns_empty_images_for_non_pdf(mock_md_class, ext):
    mock_md_class.return_value.convert.return_value.text_content = "text"
    _, images = parse_document(f"file{ext}", "file")
    assert images == []


def test_parse_document_raises_on_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document("file.exe", "file")


@patch("markitdown.MarkItDown")
def test_parse_document_handles_none_text_content(mock_md_class):
    mock_md_class.return_value.convert.return_value.text_content = None
    markdown, images = parse_document("doc.docx", "doc")
    assert markdown == ""
    assert images == []
