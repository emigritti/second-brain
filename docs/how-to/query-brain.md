# How to Query the Brain

There are two primary ways to ask your Second Brain questions:

## 1. The Terminal Web UI
1. Start the application by running `python -m brain.app`.
2. Open your browser to `http://localhost:8000/`.
3. You will see a retro terminal interface. Type your question into the prompt at the bottom and hit `Enter`.
4. The system will stream the answer back to you, followed by a list of clickable document citations used to generate the answer.

## 2. Via MCP (Claude Desktop)
If you have configured your Second Brain as an MCP server in your Claude Desktop configuration:
1. Open Claude Desktop.
2. Ask Claude a question about your knowledge base (e.g., "Use my Second Brain to find information about [Topic]").
3. Claude will automatically invoke the `search` and `get_document` tools exposed by the `mcp.py` server to find the answer and summarize it for you natively in the chat interface.
