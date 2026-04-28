import os
from anthropic import Anthropic
from typing import Tuple, List

from brain.search import BrainSearch

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

QUERY_CONFIDENCE_THRESHOLD = 0.72

class QueryEngine:
    def __init__(self, search: BrainSearch):
        self.search = search

    def _format_context(self, search_results: List[Tuple[str, str, float]]) -> str:
        context = ""
        for i, (slug, text, _) in enumerate(search_results):
            context += f"\n--- Source [{i+1}]: {slug} ---\n{text}\n"
        return context

    def query(self, question: str) -> Tuple[str, List[str]]:
        """
        Answers a natural language question.
        Returns the answer string and a list of cited slugs.
        """
        # Gather context
        results = self.search.hybrid_search(question, limit=5)
        
        if not results:
            return "I couldn't find any relevant information in your Second Brain to answer that.", []
            
        # Compute confidence (average of top 3 scores)
        top_scores = [score for _, _, score in results[:3]]
        avg_confidence = sum(top_scores) / len(top_scores) if top_scores else 0
        
        context_text = self._format_context(results)
        cited_slugs = list(set([slug for slug, _, _ in results]))
        
        print(f"Query Confidence: {avg_confidence:.2f}")
        
        try:
            if avg_confidence >= QUERY_CONFIDENCE_THRESHOLD:
                # High confidence: answer strictly from context using Haiku (faster, cheaper)
                print("High confidence. Using Haiku to summarize context.")
                response = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=1024,
                    system="You are an AI assistant answering questions based STRICTLY on the provided context. "
                           "If the answer is not in the context, say 'I cannot answer this based on the current context.' "
                           "Cite sources using [1], [2], etc., corresponding to the Source IDs.",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Context:\n{context_text}\n\nQuestion: {question}"
                        }
                    ]
                )
            else:
                # Low confidence: escalate to Sonnet for deeper reasoning
                print("Low confidence. Escalating to Sonnet for deep reasoning.")
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    system="You are an expert AI assistant. The user is asking a question about their knowledge base. "
                           "The provided context might be loosely related or incomplete. "
                           "Use the context to the best of your ability to infer the answer, "
                           "and apply your general knowledge to fill in gaps if safe to do so. "
                           "Cite sources using [1], [2] when referencing the context.",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Context snippets from my knowledge base:\n{context_text}\n\nQuestion: {question}"
                        }
                    ]
                )
                
            answer = response.content[0].text.strip() if response.content else ""
            return answer, cited_slugs
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "Sorry, I encountered an error while trying to answer your question.", cited_slugs
