from typing import List, Tuple, Dict
from rank_bm25 import BM25Okapi
from brain.index import BrainIndex
from brain.graph import BrainGraph

class BrainSearch:
    def __init__(self, index: BrainIndex, graph: BrainGraph):
        self.index = index
        self.graph = graph

    def _get_all_chunks(self) -> List[Dict]:
        """Fetch all chunks from ChromaDB for BM25 ranking."""
        try:
            # get() without arguments returns all items
            all_data = self.index.collection.get(include=['documents', 'metadatas'])
            chunks = []
            if all_data['documents']:
                for i in range(len(all_data['documents'])):
                    chunks.append({
                        'id': all_data['ids'][i],
                        'text': all_data['documents'][i],
                        'slug': all_data['metadatas'][i]['slug']
                    })
            return chunks
        except Exception:
            return []

    def hybrid_search(self, query: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Perform hybrid search using BM25, Vector Search, and Graph Traversal.
        Returns a list of (slug, chunk_text, final_score)
        """
        all_chunks = self._get_all_chunks()
        if not all_chunks:
            return []

        # 1. BM25 Pass
        tokenized_corpus = [chunk['text'].lower().split() for chunk in all_chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores (0 to 1 range approx)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
        
        # 2. Vector Similarity Pass
        # Get more than limit to ensure we have good overlap
        vector_results = self.index.query(query, limit=limit * 2)
        
        # Convert vector results to a dictionary for easy lookup
        # Chroma distance is often L2 or Cosine. Lower is better, but we need higher=better.
        # Let's invert it: max_distance - distance (or simply 1 / (1 + distance))
        vector_scores = {}
        for slug, text, distance in vector_results:
            # Simple inversion, assuming distance >= 0
            vector_scores[(slug, text)] = 1.0 / (1.0 + distance)

        # 3. Merge Scores (Reciprocal Rank Fusion or Simple Linear Combination)
        combined_scores = []
        for i, chunk in enumerate(all_chunks):
            bm25_score = bm25_scores[i] / max_bm25
            vec_score = vector_scores.get((chunk['slug'], chunk['text']), 0.0)
            
            # Combine them (weight vector search slightly higher)
            final_score = (bm25_score * 0.4) + (vec_score * 0.6)
            
            if final_score > 0:
                combined_scores.append((chunk['slug'], chunk['text'], final_score))

        # Sort by final score
        combined_scores.sort(key=lambda x: x[2], reverse=True)
        top_results = combined_scores[:limit]
        
        # 4. Graph Traversal Boost
        # We boost chunks that belong to documents directly linked to our top hits
        top_slugs = [slug for slug, _, _ in top_results]
        boosted_results = []
        
        for slug, text, score in top_results:
            # Check if this node is well-connected to other top hits
            neighbors = self.graph.get_neighbors(slug, hops=1)
            neighbor_slugs = [n['id'] for n in neighbors['nodes']]
            
            # If a top result is linked to other top results, boost its score
            overlap = set(top_slugs).intersection(set(neighbor_slugs))
            graph_boost = len(overlap) * 0.1  # 10% boost per related top hit
            
            boosted_score = score + (score * graph_boost)
            boosted_results.append((slug, text, boosted_score))

        # Final sort
        boosted_results.sort(key=lambda x: x[2], reverse=True)
        return boosted_results[:limit]
