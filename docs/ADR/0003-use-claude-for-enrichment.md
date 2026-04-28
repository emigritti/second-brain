# ADR 0003: Use Claude for Enrichment

## Context
The ingestion pipeline requires several intelligent steps: describing images, categorizing text into a taxonomy, linking concepts via wikilinks, and answering questions.

## Decision
We decided to use the Anthropic Claude API for all intelligent operations, specifically routing between `claude-3-5-haiku` and `claude-3-5-sonnet` depending on the task's complexity.

## Rationale
1. **Cost and Speed**: `claude-3-5-haiku-latest` is extremely fast and inexpensive, making it perfect for high-volume tasks during ingestion, such as image descriptions (`vision.py`) and basic categorization (`tagger.py`), as well as high-confidence context summarization (`query.py`).
2. **Deep Reasoning**: `claude-3-5-sonnet-latest` provides state-of-the-art reasoning, which is necessary for complex tasks like determining semantic relationships to inject `[[wikilinks]]` (`linker.py`) and answering low-confidence, complex queries (`query.py`).
3. **Ecosystem**: Using Anthropic's models aligns perfectly with the goal of exposing the system as an MCP server to be consumed by Claude Desktop.

## Consequences
- **Positive**: High quality, fast, and cost-effective AI enrichment.
- **Negative**: The system requires an active internet connection and an `ANTHROPIC_API_KEY` to function, making it slightly less "local-first" than a system running a local open-weights model like Llama 3.
