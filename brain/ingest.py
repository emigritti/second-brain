import os
import sys
import glob
import argparse
from typing import List

from brain.parser import parse_pdf
from brain.vision import describe_images
from brain.tagger import extract_tags
from brain.linker import inject_wikilinks
from brain.index import BrainIndex
from brain.graph import BrainGraph

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'raw')
DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'store', 'documents')

def ingest_pdf(file_path: str, brain_graph: BrainGraph, brain_index: BrainIndex):
    """
    Run the full ingestion pipeline on a single PDF.
    parser -> vision -> tagger -> linker -> index -> graph
    """
    slug = os.path.splitext(os.path.basename(file_path))[0]
    
    print(f"[{slug}] Starting ingestion...")
    
    # 1. Parser
    print(f"[{slug}] Parsing PDF and extracting images...")
    markdown_text, image_paths = parse_pdf(file_path, slug)
    
    # 2. Vision (if images were extracted)
    if image_paths:
        print(f"[{slug}] Describing {len(image_paths)} images via Claude Vision...")
        descriptions = describe_images(image_paths, slug)
        
        # Inject descriptions into markdown as blockquotes at the end
        # (Could be done more elegantly by replacing image links in the text, 
        # but appending is safest without complex regex)
        if descriptions:
            markdown_text += "\n\n## Extracted Image Descriptions\n\n"
            for img_path, desc in descriptions.items():
                img_name = os.path.basename(img_path)
                markdown_text += f"**{img_name}**:\n> {desc}\n\n"
                
    # 3. Tagger
    print(f"[{slug}] Generating tags...")
    tags = extract_tags(markdown_text)
    print(f"[{slug}] Tags: {tags}")
    
    # 4. Linker
    print(f"[{slug}] Injecting wikilinks...")
    # Get all existing slugs from the graph (excluding the current one)
    existing_slugs = [n for n in brain_graph.graph.nodes() if n != slug]
    final_markdown = inject_wikilinks(slug, markdown_text, existing_slugs)
    
    # 5. Graph Upsert (Saves to file, updates NetworkX)
    print(f"[{slug}] Saving to store and updating knowledge graph...")
    # We use slug as title for now; could use LLM to extract a better title later
    brain_graph.upsert_document(slug=slug, title=slug, text=final_markdown, tags=tags)
    
    # 6. Index (ChromaDB)
    print(f"[{slug}] Adding to vector index...")
    brain_index.add_document(slug, final_markdown)
    
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
        ingest_pdf(specific_file, graph, index)
    elif all_files:
        pdfs = glob.glob(os.path.join(RAW_DIR, '*.pdf'))
        
        if not pdfs:
            print(f"No PDFs found in {RAW_DIR}")
            return
            
        for pdf in pdfs:
            slug = os.path.splitext(os.path.basename(pdf))[0]
            # Skip if already ingested
            if os.path.exists(os.path.join(DOCS_DIR, f"{slug}.md")):
                print(f"Skipping {slug}, already ingested.")
                continue
                
            try:
                ingest_pdf(pdf, graph, index)
            except Exception as e:
                print(f"Error ingesting {slug}: {e}")
    else:
        print("Please specify a file or use --all.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ingest PDFs into Second Brain")
    parser.add_argument('file', nargs='?', help='Specific PDF file to ingest')
    parser.add_argument('--all', action='store_true', help='Ingest all new PDFs in raw/')
    args = parser.parse_args()
    
    run_ingest(args.all, args.file)
