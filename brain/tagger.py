import json
import re
from typing import List
from brain import llm

_SYSTEM = (
    "You are an expert taxonomy and tagging system. Read the provided document "
    "and return a JSON array of 3 to 7 relevant tags (lowercase, hyphenated if "
    "multiple words). Do not include any other text, only the JSON array."
)


def extract_tags(markdown_text: str, existing_tags: List[str] = None) -> List[str]:
    """
    Extract or generate tags for a markdown document.
    If tags already exist in frontmatter, returns them directly to save API calls.
    Otherwise, calls the configured LLM backend (Anthropic or Ollama).
    """
    if existing_tags:
        return existing_tags

    try:
        raw = llm.chat(
            task="tagger",
            system=_SYSTEM,
            user=f"Document text:\n\n{markdown_text[:4000]}...\n\nExtract tags:",
            max_tokens=150,
        )
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw).strip()
        tags = json.loads(raw)
        return tags if isinstance(tags, list) else []
    except Exception as e:
        print(f"Failed to generate tags: {e}")
        return []
