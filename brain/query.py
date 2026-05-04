import os
from anthropic import Anthropic
from typing import Tuple, List, Union

from brain.search import BrainSearch
from brain import llm

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

    def query(self, question: str, allow_escalation: bool = False) -> tuple | dict:
        """
        Answers a natural language question.
        Returns a tuple (answer, sources) or a dict {"needs_escalation": True, ...}
        when escalation requires user approval.
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

        config = llm.load_config()
        query_escalation_enabled = config.get("query_escalation_enabled", True)
        anthropic_require_approval = config.get("anthropic_require_approval", False)

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
                answer = response.content[0].text.strip() if response.content else ""
                return answer, cited_slugs
            else:
                # Low confidence path: check escalation controls before calling Sonnet
                local_answer = (
                    "I found some related information but my confidence is low. "
                    "Consider escalating to Claude for a more thorough answer."
                )

                if not query_escalation_enabled:
                    print("Escalation disabled. Returning local answer.")
                    return local_answer, cited_slugs

                if anthropic_require_approval and not allow_escalation:
                    print("Escalation requires approval. Returning needs_escalation response.")
                    return {
                        "needs_escalation": True,
                        "local_answer": local_answer,
                        "confidence": avg_confidence,
                        "sources": cited_slugs,
                    }

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
