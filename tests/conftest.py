"""
Stub heavy optional dependencies so tests can run without a full
Docker environment. chromadb, networkx, rank_bm25, and the chromadb
embedding helper are replaced with MagicMock at import time.
"""
import sys
from unittest.mock import MagicMock

_STUBS = [
    "chromadb",
    "chromadb.utils",
    "chromadb.utils.embedding_functions",
    "networkx",
    "rank_bm25",
    "frontmatter",
    "mcp",
    "mcp.server",
    "mcp.server.fastmcp",
]

for _mod in _STUBS:
    sys.modules.setdefault(_mod, MagicMock())
