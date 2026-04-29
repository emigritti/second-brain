from typing import List
from brain import llm

_SYSTEM = (
    "You are an expert knowledge management assistant that helps build an "
    "Obsidian-style Zettelkasten. Your task is to take a Markdown document and "
    "inject [[wikilinks]] referencing other existing documents in the knowledge "
    "base where conceptually relevant. Only link to exact concepts or highly "
    "relevant topics from the provided list of existing documents. Do not change "
    "the meaning or overall structure of the text. Just wrap relevant phrases in "
    "[[ ]]. Return the entire updated Markdown text."
)


def inject_wikilinks(slug: str, markdown_text: str, existing_slugs: List[str]) -> str:
    """
    Inject [[wikilinks]] into a document referencing other slugs in the brain.
    Delegates to the configured LLM backend (Anthropic or Ollama).
    """
    if not existing_slugs:
        return markdown_text

    try:
        updated = llm.chat(
            task="linker",
            system=_SYSTEM,
            user=(
                f"Existing document slugs in the knowledge base:\n"
                f"{', '.join(existing_slugs)}\n\n"
                f"Please inject [[wikilinks]] into the following text "
                f"(do not link to the document itself, '{slug}'):\n\n"
                f"{markdown_text}"
            ),
            max_tokens=4096,
        )
        # Safety check: if the model returns something truncated, keep the original
        if len(updated) < len(markdown_text) * 0.5:
            return markdown_text
        return updated
    except Exception as e:
        print(f"Failed to inject wikilinks: {e}")
        return markdown_text
