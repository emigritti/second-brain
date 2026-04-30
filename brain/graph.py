import os
import json
import re
import threading
import networkx as nx
import frontmatter
from typing import List, Dict, Any

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'store', 'documents'))

class BrainGraph:
    def __init__(self):
        self.store_dir = STORE_DIR
        os.makedirs(self.store_dir, exist_ok=True)
        self._lock = threading.RLock()
        self.graph = nx.DiGraph()
        self._load_from_files()

    def _extract_wikilinks(self, text: str) -> List[str]:
        """Extract [[wikilinks]] from markdown text."""
        # Simple regex for [[Link]] or [[Link|Alias]]
        matches = re.findall(r'\[\[(.*?)\]\]', text)
        links = []
        for match in matches:
            # Handle aliases: [[Target|Alias]] -> Target
            target = match.split('|')[0].strip()
            if target:
                links.append(target)
        return list(set(links))  # Unique links

    def _load_from_files(self):
        """Rebuild the NetworkX DiGraph by scanning Markdown files."""
        with self._lock:
            self._load_from_files_locked()

    def _load_from_files_locked(self):
        """Internal: must be called with self._lock held."""
        self.graph.clear()
        
        if not os.path.exists(self.store_dir):
            return

        # First pass: add all nodes
        # We need all nodes present before we can reliably add edges between them
        file_paths = []
        for root, _, files in os.walk(self.store_dir):
            for file in files:
                if file.endswith('.md'):
                    file_paths.append(os.path.join(root, file))
                    
        for path in file_paths:
            slug = os.path.splitext(os.path.basename(path))[0]
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    
                title = post.get('title', slug)
                tags = post.get('tags', [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',')]
                
                self.graph.add_node(slug, title=title, path=path, tags=tags)
            except Exception as e:
                print(f"Error parsing {path}: {e}")

        # Second pass: extract text and build edges
        for path in file_paths:
            slug = os.path.splitext(os.path.basename(path))[0]
            if not self.graph.has_node(slug):
                continue
                
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    text = post.content
                    
                links = self._extract_wikilinks(text)
                for link in links:
                    # Obsidian often matches by filename/slug
                    # Here we assume the link directly matches the slug
                    # A more robust version would check titles or fuzzy match
                    target_slug = link
                    
                    # If target node doesn't exist, we might create a placeholder node
                    # This represents a dangling link (a page not yet created)
                    if not self.graph.has_node(target_slug):
                        self.graph.add_node(target_slug, title=target_slug, path=None, tags=[], is_dangling=True)
                        
                    self.graph.add_edge(slug, target_slug, type='wikilink', weight=1.0)
            except Exception as e:
                print(f"Error extracting links from {path}: {e}")

    def upsert_document(self, slug: str, title: str, text: str, tags: List[str]):
        """Upsert a document: write to a .md file and update the graph."""
        path = os.path.join(self.store_dir, f"{slug}.md")

        post = frontmatter.Post(text, title=title, tags=tags)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        with self._lock:
            self._load_from_files_locked()

    def get_neighbors(self, slug: str, hops: int = 1) -> Dict[str, Any]:
        """Get neighbors of a document up to n hops."""
        with self._lock:
            return self._get_neighbors_locked(slug, hops)

    def _get_neighbors_locked(self, slug: str, hops: int) -> Dict[str, Any]:
        if not self.graph.has_node(slug):
            return {"nodes": [], "edges": []}

        visited = {slug}
        queue = [(slug, 0)]
        nodes_result = []
        edges_result = []
        edges_seen = set()

        while queue:
            current_node, current_hop = queue.pop(0)
            node_data = self.graph.nodes[current_node]
            nodes_result.append({
                "id": current_node,
                **node_data
            })

            if current_hop < hops:
                for neighbor in self.graph.successors(current_node):
                    edge_data = self.graph.get_edge_data(current_node, neighbor)
                    edge_tuple = (current_node, neighbor, edge_data.get('type'))
                    if edge_tuple not in edges_seen:
                        edges_result.append({
                            "source": current_node,
                            "target": neighbor,
                            **edge_data
                        })
                        edges_seen.add(edge_tuple)
                        
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_hop + 1))
                        
                for neighbor in self.graph.predecessors(current_node):
                    edge_data = self.graph.get_edge_data(neighbor, current_node)
                    edge_tuple = (neighbor, current_node, edge_data.get('type'))
                    if edge_tuple not in edges_seen:
                        edges_result.append({
                            "source": neighbor,
                            "target": current_node,
                            **edge_data
                        })
                        edges_seen.add(edge_tuple)
                        
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_hop + 1))

        return {
            "nodes": nodes_result,
            "edges": edges_result
        }

    def export_json(self) -> str:
        """Export the entire graph to JSON (Cytoscape.js compatible)."""
        with self._lock:
            nodes = [
                {"data": {"id": n, "label": self.graph.nodes[n].get("title", n), **self.graph.nodes[n]}}
                for n in self.graph.nodes()
            ]
            edges = [{"data": {"source": u, "target": v, **d}} for u, v, d in self.graph.edges(data=True)]

        return json.dumps({
            "nodes": nodes,
            "edges": edges
        })
