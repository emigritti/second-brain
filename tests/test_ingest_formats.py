import pytest
from unittest.mock import MagicMock, patch
from brain.ingest import ingest_document


@patch("brain.ingest.brain_index", create=True)
@patch("brain.ingest.brain_graph", create=True)
@patch("brain.ingest.inject_wikilinks", return_value="final md")
@patch("brain.ingest.extract_tags", return_value=["test"])
@patch("brain.ingest.describe_images")
@patch("brain.ingest.parse_document", return_value=("# Doc content", []))
def test_ingest_non_pdf_skips_vision(
    mock_parse, mock_vision, mock_tags, mock_links, mock_graph, mock_index
):
    """Vision step must be skipped when parse_document returns no image paths."""
    graph = MagicMock()
    graph.graph.nodes.return_value = []
    index = MagicMock()

    ingest_document("report.docx", graph, index)

    mock_parse.assert_called_once_with("report.docx", "report")
    mock_vision.assert_not_called()
    mock_tags.assert_called_once()
    mock_links.assert_called_once()
    graph.upsert_document.assert_called_once()
    index.add_document.assert_called_once()


@patch("brain.ingest.inject_wikilinks", return_value="final md")
@patch("brain.ingest.extract_tags", return_value=["tag1"])
@patch("brain.ingest.describe_images", return_value={"/img/a.png": "a chart"})
@patch("brain.ingest.parse_document", return_value=("# PDF content", ["/img/a.png"]))
def test_ingest_pdf_calls_vision(mock_parse, mock_vision, mock_tags, mock_links):
    """Vision step must be called when parse_document returns image paths (PDF)."""
    graph = MagicMock()
    graph.graph.nodes.return_value = []
    index = MagicMock()

    ingest_document("book.pdf", graph, index)

    mock_vision.assert_called_once_with(["/img/a.png"], "book")
