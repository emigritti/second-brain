import os
from mcp.server.fastmcp import FastMCP

from brain.graph import BrainGraph
from brain.index import BrainIndex
from brain.search import BrainSearch
from brain.ingest import ingest_pdf

mcp = FastMCP("Second Brain")

# Initialize core engines for MCP
brain_graph = BrainGraph()
brain_index = BrainIndex()
brain_search = BrainSearch(brain_index, brain_graph)

@mcp.tool()
def search(query: str, limit: int = 5) -> str:
    """
    Search the Second Brain using hybrid vector and BM25 search.
    Returns the top matching context chunks.
    """
    results = brain_search.hybrid_search(query, limit)
    if not results:
        return "No results found."
        
    formatted = []
    for slug, text, score in results:
        formatted.append(f"--- Document: {slug} (Score: {score:.2f}) ---\n{text}\n")
    return "\n".join(formatted)

@mcp.tool()
def get_document(slug: str) -> str:
    """
    Retrieve the full raw Markdown content of a specific document by its slug.
    """
    safe_name = os.path.basename(slug)
    store_dir = os.path.realpath(brain_graph.store_dir)
    doc_path = os.path.realpath(os.path.join(store_dir, f"{safe_name}.md"))
    if not doc_path.startswith(store_dir + os.sep):
        return f"Error: Invalid slug '{slug}'."
    if not os.path.exists(doc_path):
        return f"Error: Document '{slug}' not found."

    with open(doc_path, 'r', encoding='utf-8') as f:
        return f.read()

@mcp.tool()
def get_graph_neighbors(slug: str, hops: int = 1) -> str:
    """
    Get all documents connected to the specified document within the given number of hops.
    """
    neighbors = brain_graph.get_neighbors(slug, hops)
    if not neighbors['nodes']:
        return f"Document '{slug}' not found or has no connections."
        
    connected_slugs = [n['id'] for n in neighbors['nodes'] if n['id'] != slug]
    if not connected_slugs:
        return f"Document '{slug}' has no connections."
        
    return f"Documents connected to {slug} (up to {hops} hops):\n" + "\n".join(connected_slugs)

@mcp.tool()
def ingest(file_path: str) -> str:
    """
    Trigger the full ingestion pipeline for a new PDF file.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' does not exist."
        
    try:
        ingest_pdf(file_path, brain_graph, brain_index)
        return f"Successfully ingested {file_path}"
    except Exception as e:
        return f"Failed to ingest {file_path}: {str(e)}"

@mcp.tool()
def list_tags() -> str:
    """
    Return a list of all unique tags used across all documents in the Second Brain.
    """
    brain_graph._load_from_files()  # Ensure up to date
    all_tags = set()
    for node_id, data in brain_graph.graph.nodes(data=True):
        tags = data.get('tags', [])
        for t in tags:
            all_tags.add(t)
            
    if not all_tags:
        return "No tags found in the system."
        
    return "Available tags:\n" + ", ".join(sorted(list(all_tags)))

def run_mcp():
    """Run the MCP server via stdio."""
    mcp.run()

if __name__ == '__main__':
    run_mcp()
