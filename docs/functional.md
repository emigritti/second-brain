# Functional Overview

Second Brain provides several key functionalities designed to automate the process of personal knowledge management.

## 1. Automated Document Ingestion
Users can drop a PDF into the system, and the application will automatically:
- Convert it to Markdown.
- Extract images and write descriptions for them using Vision AI.
- Generate a taxonomy of tags for the document.
- Intelligently link the new document to previously existing documents in the brain using `[[wikilinks]]`.

## 2. Directory Watchdog
The system monitors the `raw/` directory in the background. If a user downloads a PDF from their browser directly into this folder, the system detects the new file and immediately runs it through the automated ingestion pipeline without requiring user interaction.

## 3. Hybrid Search
Users can search for concepts across their knowledge base. The search doesn't just look for exact words; it looks for meaning (Vector Search) and prioritizes documents that are highly connected to other relevant documents in the graph (Graph Boost).

## 4. Confidence-Based Q&A
Users can ask natural language questions in the terminal interface. The system retrieves relevant documents and calculates a confidence score. If it finds the exact answer, it quickly summarizes it. If the answer is vague or requires synthesizing multiple unconnected concepts, it escalates to a highly capable reasoning model (Claude Sonnet) to figure it out.

## 5. Visual Knowledge Graph
The system provides an interactive Cytoscape graph. Users can visually explore how their documents are connected, view clusters of information, and click on nodes to jump straight into the raw document viewer.

## 6. MCP (Model Context Protocol) Integration
The brain can be exposed as an MCP server. This allows external clients (like Claude Desktop) to invoke the brain's tools, read its graph, and search its vectors directly from their native chat interfaces.
