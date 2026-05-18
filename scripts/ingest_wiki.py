"""
Ingest mewwiki markdown notes into doobidoo (mcp-memory-service / SQLite-vec).

Usage:
    MCP_MEMORY_SQLITE_PATH=~/.mewvault/chroma-wiki/memory.db \
    MCP_EXTERNAL_EMBEDDING_URL=http://localhost:11434/v1/embeddings \
    MCP_EXTERNAL_EMBEDDING_MODEL=nomic-embed-text \
    python scripts/ingest_wiki.py
"""

import asyncio
import os
import sys
from pathlib import Path

WIKI_ROOT = Path("/Users/Mohabbat/Jan/mewwiki")

# Set env vars before importing config-dependent modules
os.environ.setdefault("MCP_MEMORY_SQLITE_PATH", str(Path.home() / ".mewvault/chroma-wiki/memory.db"))
os.environ.setdefault("MCP_EXTERNAL_EMBEDDING_URL", "http://localhost:11434/v1/embeddings")
os.environ.setdefault("MCP_EXTERNAL_EMBEDDING_MODEL", "nomic-embed-text")
os.environ.setdefault("MCP_MEMORY_BACKUPS_PATH", str(Path.home() / ".mewvault/chroma-wiki-backups"))


async def main():
    from mcp_memory_service.storage.factory import create_storage_instance
    from mcp_memory_service.services import MemoryService
    from mcp_memory_service.ingestion import get_loader_for_file

    db_path = os.environ["MCP_MEMORY_SQLITE_PATH"]
    print(f"Database: {db_path}")

    storage = await create_storage_instance(db_path)
    service = MemoryService(storage)

    md_files = sorted(WIKI_ROOT.rglob("*.md"))
    print(f"Found {len(md_files)} notes to ingest\n")

    total_chunks = 0
    skipped = 0

    for md_file in md_files:
        rel = md_file.relative_to(WIKI_ROOT)
        loader = get_loader_for_file(md_file)
        if loader is None:
            print(f"  [skip] no loader for {rel}")
            skipped += 1
            continue

        # Derive tags from path segments (folder names + filename stem)
        parts = list(rel.parts)
        tags = [p.lower().replace(" ", "-") for p in parts[:-1]]  # folder segments
        tags.append(rel.stem.lower().replace(" ", "-"))             # filename stem
        tags.append("wiki")

        file_chunks = 0
        async for chunk in loader.extract_chunks(md_file):
            if not chunk.content.strip():
                continue
            metadata = {
                "source_file": str(rel),
                "chunk_index": chunk.chunk_index,
            }
            result = await service.store_memory(
                content=chunk.content,
                tags=tags,
                memory_type="wiki-note",
                metadata=metadata,
            )
            file_chunks += 1
            total_chunks += 1

        status = "ok" if file_chunks else "empty"
        print(f"  [{status}] {rel}  ({file_chunks} chunk{'s' if file_chunks != 1 else ''})")

    print(f"\nDone. {total_chunks} chunks stored, {skipped} files skipped.")


if __name__ == "__main__":
    asyncio.run(main())
