"""
Ingest software-projects/ and game-lab/ source files into doobidoo.

Usage:
    python scripts/ingest_code.py
"""

import asyncio
import os
from pathlib import Path

WORKSPACE = Path("/Users/Mohabbat/Jan")
CODE_ROOTS = [
    WORKSPACE / "software-projects",
    WORKSPACE / "game-lab",
]

INCLUDE_EXTENSIONS = {".ts", ".tsx", ".js", ".py", ".gd", ".cs", ".md"}
EXCLUDE_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".next", "coverage", ".turbo"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

os.environ.setdefault("MCP_MEMORY_SQLITE_PATH", str(Path.home() / ".mewvault/chroma-wiki/memory.db"))
os.environ.setdefault("MCP_EXTERNAL_EMBEDDING_URL", "http://localhost:11434/v1/embeddings")
os.environ.setdefault("MCP_EXTERNAL_EMBEDDING_MODEL", "nomic-embed-text")
os.environ.setdefault("MCP_MEMORY_BACKUPS_PATH", str(Path.home() / ".mewvault/chroma-wiki-backups"))


def collect_files():
    files = []
    for root in CODE_ROOTS:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if any(part in EXCLUDE_DIRS for part in f.parts):
                continue
            if f.name in SKIP_FILES:
                continue
            if f.suffix in INCLUDE_EXTENSIONS:
                files.append(f)
    return sorted(files)


def derive_tags(file_path: Path) -> list[str]:
    # Determine silo
    rel = file_path.relative_to(WORKSPACE)
    parts = list(rel.parts)
    silo = "code" if str(rel).startswith("software-projects") else "game"
    project = parts[1] if len(parts) > 1 else "unknown"
    # Sub-area (wiki, src, packages, etc.)
    area = parts[2] if len(parts) > 2 else ""
    ext = file_path.suffix.lstrip(".")

    tags = [silo, project, ext]
    if area:
        tags.append(area.lower().replace("-", "_"))
    tags.append("code-index")
    return tags


async def _text_chunks(file_path: Path, chunk_size: int = 1000, overlap: int = 200):
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return
    i, idx = 0, 0
    while i < len(text):
        yield text[i:i + chunk_size], idx
        i += chunk_size - overlap
        idx += 1


async def _normalize(chunks_iter, is_loader: bool):
    """Yield (content, chunk_index) from either loader chunks or raw text tuples."""
    if is_loader:
        async for chunk in chunks_iter:
            yield chunk.content, chunk.chunk_index
    else:
        async for content, idx in chunks_iter:
            yield content, idx


async def main():
    from mcp_memory_service.storage.factory import create_storage_instance
    from mcp_memory_service.services import MemoryService
    from mcp_memory_service.ingestion import get_loader_for_file

    db_path = os.environ["MCP_MEMORY_SQLITE_PATH"]
    print(f"Database: {db_path}")

    storage = await create_storage_instance(db_path)
    service = MemoryService(storage)

    files = collect_files()
    print(f"Found {len(files)} files to ingest\n")

    total_chunks = 0
    skipped = 0

    for file_path in files:
        rel = file_path.relative_to(WORKSPACE)
        loader = get_loader_for_file(file_path)
        tags = derive_tags(file_path)
        file_chunks = 0

        try:
            if loader is not None:
                # Use the registered loader (handles .md, .txt, etc.)
                chunks_iter = loader.extract_chunks(file_path)
            else:
                # Fallback: chunk source code files manually (1000-char chunks, 200 overlap)
                chunks_iter = _text_chunks(file_path)

            async for content, chunk_idx in _normalize(chunks_iter, loader is not None):
                if not content.strip():
                    continue
                metadata = {
                    "source_file": str(rel),
                    "chunk_index": chunk_idx,
                    "silo": tags[0],
                    "project": tags[1],
                }
                await service.store_memory(
                    content=content,
                    tags=tags,
                    memory_type="observation",
                    metadata=metadata,
                )
                file_chunks += 1
                total_chunks += 1
        except Exception as e:
            print(f"  [err] {rel}: {e}")
            skipped += 1
            continue

        status = "ok" if file_chunks else "empty"
        print(f"  [{status}] {rel}  ({file_chunks} chunk{'s' if file_chunks != 1 else ''})")

    print(f"\nDone. {total_chunks} chunks stored, {skipped} files skipped.")


if __name__ == "__main__":
    asyncio.run(main())
