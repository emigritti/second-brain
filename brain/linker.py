import os
from anthropic import Anthropic
from typing import List

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def inject_wikilinks(slug: str, markdown_text: str, existing_slugs: List[str]) -> str:
    """
    Use Claude API to intelligently suggest and inject [[wikilinks]] into the document.
    
    Args:
        slug: The document's own slug.
        markdown_text: The full text of the document.
        existing_slugs: A list of all other document slugs in the brain to link to.
        
    Returns:
        The updated markdown text with [[wikilinks]] injected.
    """
    if not existing_slugs:
        return markdown_text
        
    try:
        # We use Claude Sonnet for reasoning about links
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=4096,
            system="You are an expert knowledge management assistant that helps build an Obsidian-style Zettelkasten. "
                   "Your task is to take a Markdown document and inject [[wikilinks]] referencing other existing documents "
                   "in the knowledge base where conceptually relevant. "
                   "Only link to exact concepts or highly relevant topics from the provided list of existing documents. "
                   "Do not change the meaning or overall structure of the text. Just wrap relevant phrases in [[ ]]. "
                   "Return the entire updated Markdown text.",
            messages=[
                {
                    "role": "user",
                    "content": f"Existing document slugs in the knowledge base:\n{', '.join(existing_slugs)}\n\n"
                               f"Please inject [[wikilinks]] into the following text (do not link to the document itself, '{slug}'):\n\n"
                               f"{markdown_text}"
                }
            ]
        )
        
        updated_text = response.content[0].text.strip() if response.content else ""
        
        # Safety check: if Claude returns nothing or errors out with a tiny string, don't overwrite
        if len(updated_text) < len(markdown_text) * 0.5:
            return markdown_text
            
        return updated_text
        
    except Exception as e:
        print(f"Failed to inject wikilinks: {e}")
        return markdown_text
