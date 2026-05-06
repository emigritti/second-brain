import os
import sys
import glob
import argparse
from collections import deque
from datetime import datetime
from typing import List

from brain.parser import parse_document, MARKITDOWN_EXTENSIONS
from brain.vision import describe_images
from brain.tagger import extract_tags
from brain.linker import inject_wikilinks
from brain.index import BrainIndex
from brain.graph import BrainGraph
from brain import llm

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'raw'))
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'store', 'documents'))

# In-memory log of recent ingestion events (survives across background tasks within one process)
INGEST_LOG: deque = deque(maxlen=50)


def ingest_document(file_path: str, brain_graph: BrainGraph, brain_index: BrainIndex, skip_api_calls: bool = False):
    """
    Run the full ingestion pipeline on any supported document format.
    parser -> vision (PDF only) -> tagger -> linker -> index -> graph

    Args:
        skip_api_calls: If True, skip all Anthropic API calls (vision, tagger, linker).
    """
    slug = os.path.splitext(os.path.basename(file_path))[0]
    warnings: list[dict] = []

    print(f"[{slug}] Starting ingestion...")

    # 1. Parser
    print(f"[{slug}] Parsing document...")
    markdown_text, image_paths = parse_document(file_path, slug)

    # 2. Vision (if images were extracted)
    if image_paths and not skip_api_calls:
        print(f"[{slug}] Describing {len(image_paths)} images via Claude Vision...")
        descriptions = describe_images(image_paths, slug)
        if descriptions:
            markdown_text += "\n\n## Extracted Image Descriptions\n\n"
            for img_path, desc in descriptions.items():
                img_name = os.path.basename(img_path)
                markdown_text += f"**{img_name}**:\n> {desc}\n\n"

    # 3. Tagger
    if skip_api_calls:
        tags = []
    else:
        print(f"[{slug}] Generating tags...")
        tags = extract_tags(markdown_text)
        warnings.extend(llm.pop_warnings())
    print(f"[{slug}] Tags: {tags}")

    # 4. Linker
    existing_slugs = [n for n in brain_graph.graph.nodes() if n != slug]
    if skip_api_calls:
        final_markdown = markdown_text
    else:
        print(f"[{slug}] Injecting wikilinks...")
        final_markdown = inject_wikilinks(slug, markdown_text, existing_slugs)
        warnings.extend(llm.pop_warnings())

    # 5. Graph Upsert (saves to file, updates NetworkX)
    print(f"[{slug}] Saving to store and updating knowledge graph...")
    brain_graph.upsert_document(slug=slug, title=slug, text=final_markdown, tags=tags)

    # 6. Index (ChromaDB)
    print(f"[{slug}] Adding to vector index...")
    brain_index.add_document(slug, final_markdown)

    # 7. Semantic edges
    print(f"[{slug}] Computing semantic similarity with existing documents...")
    similar = brain_index.get_similar_documents(slug)
    if similar:
        brain_graph.update_semantic_links(slug, [s for s, _ in similar])
        print(f"[{slug}] Linked to {len(similar)} semantically similar documents.")
    else:
        print(f"[{slug}] No semantic neighbors found above threshold.")

    INGEST_LOG.appendleft({
        "slug": slug,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "warnings": warnings,
    })

    print(f"[{slug}] Ingestion complete!\n")


def run_ingest(all_files: bool = False, specific_file: str = None):
    """Main entrypoint for ingestion."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    graph = BrainGraph()
    index = BrainIndex()

    if specific_file:
        if not os.path.exists(specific_file):
            print(f"Error: File {specific_file} not found.")
            sys.exit(1)
        ingest_document(specific_file, graph, index)
    elif all_files:
        all_extensions = {'.pdf'} | MARKITDOWN_EXTENSIONS
        files = []
        for ext in all_extensions:
            files.extend(glob.glob(os.path.join(RAW_DIR, f'*{ext}')))

        if not files:
            print(f"No supported files found in {RAW_DIR}")
            return

        for f in files:
            slug = os.path.splitext(os.path.basename(f))[0]
            if os.path.exists(os.path.join(DOCS_DIR, f"{slug}.md")):
                print(f"Skipping {slug}, already ingested.")
                continue
            try:
                ingest_document(f, graph, index)
            except Exception as e:
                print(f"Error ingesting {slug}: {e}")
    else:
        print("Please specify a file or use --all.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ingest documents into Second Brain")
    parser.add_argument('file', nargs='?', help='Specific file to ingest')
    parser.add_argument('--all', action='store_true', help='Ingest all new files in raw/')
    args = parser.parse_args()
    run_ingest(args.all, args.file)
