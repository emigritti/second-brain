import os
import fitz  # pymupdf
import pymupdf4llm
from typing import Tuple, List

IMAGES_STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'store', 'images'))

MARKITDOWN_EXTENSIONS = {
    '.docx', '.xlsx', '.xls', '.pptx',
    '.html', '.htm', '.xml', '.csv', '.json',
    '.epub', '.md', '.mp3', '.wav', '.m4a', '.zip'
}

def parse_pdf(file_path: str, slug: str) -> Tuple[str, List[str]]:
    """
    Parse a PDF file, convert to Markdown, and extract images.
    Optimized to handle large PDFs (e.g., books > 300MB) by processing page by page.
    
    Args:
        file_path: Absolute path to the PDF.
        slug: The unique identifier for this document, used for organizing images.
        
    Returns:
        Tuple containing (markdown_text, list_of_image_paths)
    """
    doc = fitz.open(file_path)
    total_pages = len(doc)
    
    image_dir = os.path.join(IMAGES_STORE_DIR, slug)
    os.makedirs(image_dir, exist_ok=True)
    
    markdown_chunks = []
    extracted_image_paths = []
    
    # We use pymupdf4llm's ability to process specific pages
    # To save memory on 300MB+ books, we process in chunks of 10 pages
    CHUNK_SIZE = 10
    
    for start_page in range(0, total_pages, CHUNK_SIZE):
        end_page = min(start_page + CHUNK_SIZE - 1, total_pages - 1)
        pages = list(range(start_page, end_page + 1))
        
        try:
            # write_images=True extracts images, image_path tells it where to put them
            md_text = pymupdf4llm.to_markdown(
                doc,
                pages=pages,
                write_images=True,
                image_path=image_dir,
                image_format="png"
            )
            markdown_chunks.append(md_text)
        except Exception as e:
            print(f"Error processing pages {start_page}-{end_page}: {e}")
            
    doc.close()
    
    # Collect the extracted image paths
    if os.path.exists(image_dir):
        for img_name in os.listdir(image_dir):
            if img_name.endswith('.png'):
                extracted_image_paths.append(os.path.join(image_dir, img_name))
                
    full_markdown = "\n\n".join(markdown_chunks)
    
    return full_markdown, extracted_image_paths


def parse_document(file_path: str, slug: str) -> Tuple[str, List[str]]:
    """Format-agnostic entry point. Routes PDFs to pymupdf4llm (preserving image
    extraction) and all other formats to MarkItDown."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return parse_pdf(file_path, slug)
    if ext in MARKITDOWN_EXTENSIONS:
        return _parse_with_markitdown(file_path), []
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_with_markitdown(file_path: str) -> str:
    from markitdown import MarkItDown
    result = MarkItDown(enable_plugins=False).convert(file_path)
    return result.text_content or ""
