# ADR 0002: Defer Automated Testing

## Context
Phase 5 of the original `PLAN.md` outlined an extensive `pytest` suite for the parser, tagger, graph, search, query, and server components.

## Decision
We decided to defer the creation of the automated test suite until the very end of the project, focusing first on building out the core functionality and the Web UI.

## Rationale
1. **Prototyping Velocity**: The core logic required significant experimentation (e.g., tweaking LLM prompts for tagging and linking, handling large PDFs). Writing tests first (TDD) would have slowed down the rapid prototyping phase.
2. **Visual Feedback**: The user requested a functional, visually appealing UI. Getting the app running to manually verify the ingestion pipeline and UI provided more immediate value than automated unit tests early on.

## Consequences
- **Positive**: We were able to deliver a fully functional, end-to-end application much faster.
- **Negative**: The lack of tests during early development required manual verification of the pipeline. (Mitigated by eventually writing the tests in Phase 5).
