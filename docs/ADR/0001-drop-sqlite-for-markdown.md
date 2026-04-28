# ADR 0001: Drop SQLite for Markdown Source of Truth

## Context
The initial `PLAN.md` proposed using an SQLite database (`brain.db`) with `documents` and `edges` tables to store the knowledge graph and document metadata. 

## Decision
We decided to entirely remove the SQLite dependency. Instead, the `NetworkX` graph is built entirely in memory on startup by dynamically parsing all `.md` files in the `store/documents/` directory.

## Rationale
1. **Obsidian Compatibility**: To truly embrace the "Obsidian way", the plain text Markdown files must be the absolute single source of truth.
2. **Portability**: Users should not have their data locked inside an SQLite table. They should be able to zip the `store/documents/` folder and open it in Obsidian, Logseq, or any other Markdown editor without losing the structure.
3. **Simplicity**: Removes the need for database migrations, schema management, and complex synchronization logic between the database and the file system.

## Consequences
- **Positive**: Complete portability and alignment with local-first Markdown principles.
- **Negative**: Startup time may increase slightly as the knowledge base grows to thousands of files, since every file must be read to construct the graph. (This can be mitigated with a file cache later if needed).
