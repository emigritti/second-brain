import os
import json
import re
from anthropic import Anthropic
from typing import List

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def extract_tags(markdown_text: str, existing_tags: List[str] = None) -> List[str]:
    """
    Extract or generate tags for a markdown document.
    If tags already exist in frontmatter, returns them directly to save API calls.
    Otherwise, uses Claude API to suggest tags.
    
    Args:
        markdown_text: The full text of the document.
        existing_tags: List of tags already present in the frontmatter.
        
    Returns:
        List of generated or existing tags.
    """
    if existing_tags and len(existing_tags) > 0:
        return existing_tags
        
    try:
        # Ask Claude to generate a JSON array of 3-7 tags
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=150,
            system="You are an expert taxonomy and tagging system. Read the provided document and return a JSON array of 3 to 7 relevant tags (lowercase, hyphenated if multiple words). Do not include any other text, only the JSON array.",
            messages=[
                {
                    "role": "user",
                    "content": f"Document text:\n\n{markdown_text[:4000]}...\n\nExtract tags:"
                }
            ]
        )
        
        if not response.content:
            return []

        # Strip optional markdown code fences (```json ... ``` or ``` ... ```)
        response_text = response.content[0].text.strip()
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text).strip()

        tags = json.loads(response_text)
        
        if isinstance(tags, list):
            return tags
        return []
        
    except Exception as e:
        print(f"Failed to generate tags: {e}")
        return []
