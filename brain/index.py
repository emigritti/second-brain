import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Tuple

CHROMA_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'store', 'chroma'))

class BrainIndex:
    def __init__(self):
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
        # We can use the default embedding function (all-MiniLM-L6-v2) for simplicity
        # or OpenAI/Anthropic if required. We'll use the default for local embedding.
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name="brain_documents",
            embedding_function=self.emb_fn
        )

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple character-based chunking."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])
            start += chunk_size - overlap
            
        return chunks

    def add_document(self, slug: str, text: str):
        """Chunk text, embed, and upsert to ChromaDB."""
        chunks = self._chunk_text(text)
        
        if not chunks:
            return
            
        ids = [f"{slug}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"slug": slug, "chunk_index": i} for i in range(len(chunks))]
        
        # Upsert automatically overwrites if IDs exist
        self.collection.upsert(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Vector similarity search.
        Returns a list of (slug, chunk_text, distance_score) tuples.
        """
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(limit, self.collection.count())
        )
        
        formatted_results = []
        
        if results['distances'] and results['distances'][0]:
            for i in range(len(results['distances'][0])):
                slug = results['metadatas'][0][i]['slug']
                text = results['documents'][0][i]
                score = results['distances'][0][i]  # Lower distance is better
                formatted_results.append((slug, text, score))
                
        return formatted_results

    def get_similar_documents(self, slug: str, min_similarity: float = 0.75, limit: int = 10) -> list[tuple[str, float]]:
        """
        Find documents semantically similar to the given slug.
        Returns [(other_slug, similarity_score)] sorted by similarity desc.
        Uses L2 distance from ChromaDB (all-MiniLM-L6-v2 outputs normalized vectors,
        so cosine_similarity = 1 - (l2_distance^2 / 2)).
        """
        if self.collection.count() < 2:
            return []

        # Get embeddings for all chunks of this slug
        own_chunks = self.collection.get(
            where={"slug": slug},
            include=["embeddings"]
        )
        if own_chunks["embeddings"] is None or len(own_chunks["embeddings"]) == 0:
            return []

        # Query for similar chunks across all docs, aggregate by document
        doc_scores: dict[str, float] = {}
        n_results = min(50, self.collection.count())

        for embedding in own_chunks["embeddings"]:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                other_slug = meta["slug"]
                if other_slug == slug:
                    continue
                # L2 distance to cosine similarity (valid for normalized vectors)
                similarity = max(0.0, 1.0 - (dist ** 2) / 2.0)
                if other_slug not in doc_scores or similarity > doc_scores[other_slug]:
                    doc_scores[other_slug] = similarity

        return sorted(
            [(s, score) for s, score in doc_scores.items() if score >= min_similarity],
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def rebuild(self, documents_dir: str):
        """Drop collection and re-embed all documents in the directory."""
        try:
            self.client.delete_collection("brain_documents")
        except Exception:
            pass # Doesn't exist yet
            
        self.collection = self.client.create_collection(
            name="brain_documents",
            embedding_function=self.emb_fn
        )
        
        if not os.path.exists(documents_dir):
            return
            
        for root, _, files in os.walk(documents_dir):
            for file in files:
                if file.endswith('.md'):
                    slug = os.path.splitext(file)[0]
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        self.add_document(slug, text)
                    except Exception as e:
                        print(f"Failed to embed {path}: {e}")
