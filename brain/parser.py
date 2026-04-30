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

_PDF_CHUNK_SIZE = 10

def parse_pdf(file_path: str, slug: str) -> Tuple[str, List[str]]:
    """
    Parse a PDF file, convert to Markdown, and extract images.
    Text is extracted in 10-page chunks (memory-safe for large PDFs).
    Images are extracted separately via fitz to avoid pymupdf4llm path bugs.
    """
    doc = fitz.open(file_path)
    total_pages = len(doc)

    image_dir = os.path.join(IMAGES_STORE_DIR, slug)
    os.makedirs(image_dir, exist_ok=True)

    markdown_chunks = []
    for start_page in range(0, total_pages, _PDF_CHUNK_SIZE):
        end_page = min(start_page + _PDF_CHUNK_SIZE - 1, total_pages - 1)
        pages = list(range(start_page, end_page + 1))
        try:
            md_text = pymupdf4llm.to_markdown(doc, pages=pages, write_images=False)
            markdown_chunks.append(md_text)
        except Exception as e:
            print(f"Error processing pages {start_page}-{end_page}: {e}")

    extracted_image_paths = []
    seen_xrefs: set[int] = set()
    img_index = 0
    for page_num in range(total_pages):
        page = doc[page_num]
        for img in page.get_images(full=False):
            xref = img[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                base_image = doc.extract_image(xref)
                ext = base_image.get("ext", "png")
                img_path = os.path.join(image_dir, f"{img_index:04d}.{ext}")
                with open(img_path, "wb") as f:
                    f.write(base_image["image"])
                extracted_image_paths.append(img_path)
                img_index += 1
            except Exception as e:
                print(f"[parser] Skipping image xref={xref}: {e}")

    doc.close()
    return "\n\n".join(markdown_chunks), extracted_image_paths


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
