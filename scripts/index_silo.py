#!/usr/bin/env python3
"""
index_silo.py — Direct ChromaDB semantic indexer for MewVault silos.

Usage:
    python3 mewvault/scripts/index_silo.py --silo <silo> [--files <path,path,...>] [--full]

Collections:
    mewvault-shared  — all silos except career + learn
    mewvault-career  — career-studio only
    mewvault-learn   — learn-lab only (low priority)
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MEWVAULT_DIR = Path.home() / ".mewvault"
CHROMA_PATH = MEWVAULT_DIR / "chroma"
PENDING_QUEUE = MEWVAULT_DIR / "pending-index-queue.jsonl"

SILO_DIRS = {
    "wiki":     Path("/Users/Mohabbat/Jan/mewwiki"),
    "design":   Path("/Users/Mohabbat/Jan/design-studio"),
    "code":     Path("/Users/Mohabbat/Jan/software-projects"),
    "game":     Path("/Users/Mohabbat/Jan/game-lab"),
    "idea":     Path("/Users/Mohabbat/Jan/idea-hub"),
    "mewvault": Path("/Users/Mohabbat/Jan/mewvault"),
    "career":   Path("/Users/Mohabbat/Jan/career-studio"),
    "learn":    Path("/Users/Mohabbat/Jan/learn-lab"),
}

COLLECTION_MAP = {
    "career": "mewvault-career",
    "learn":  "mewvault-learn",
}

CODE_SILOS = {"code", "game", "mewvault"}

EXCLUDE_DIRS = {
    "node_modules", "dist", "build", ".next", ".svelte-kit",
    ".godot", "export", "graphify-out", ".git", "raw",
    "venv", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache",
    "mewvault.egg-info", "cache", "secrets", "bootstrap",
}

OLLAMA_URL = "http://localhost:11434/v1/embeddings"
OLLAMA_MODEL = "nomic-embed-text"
OLLAMA_TIMEOUT = 5
EMBED_BATCH = 20
MAX_CHUNK_CHARS = 512 * 4  # ~512 tokens


# ---------------------------------------------------------------------------
# Embedding via Ollama
# ---------------------------------------------------------------------------

def embed(texts: list[str]) -> list[list[float]] | None:
    """Call Ollama to embed a list of texts. Returns None on failure."""
    body = json.dumps({"model": OLLAMA_MODEL, "input": texts}).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as r:
            data = json.loads(r.read())
        return [d["embedding"] for d in data["data"]]
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_markdown(text: str, filepath: str) -> list[dict]:
    """Split markdown on ## / ### headings, max MAX_CHUNK_CHARS per chunk."""
    lines = text.splitlines(keepends=True)
    chunks: list[dict] = []
    current_heading = ""
    current_lines: list[str] = []

    def flush(heading, body_lines, idx):
        body = "".join(body_lines).strip()
        if not body:
            return
        # If still too long, slice it
        while body:
            piece = body[:MAX_CHUNK_CHARS]
            chunks.append({
                "text": (f"{heading}\n{piece}" if heading else piece).strip(),
                "heading": heading,
                "chunk_type": "heading",
                "chunk_index": len(chunks),
            })
            body = body[MAX_CHUNK_CHARS:]

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            flush(current_heading, current_lines, len(chunks))
            current_heading = stripped.rstrip()
            current_lines = []
        else:
            current_lines.append(line)

    flush(current_heading, current_lines, len(chunks))

    # Fallback: no headings found → whole file as one chunk
    if not chunks:
        piece = text.strip()[:MAX_CHUNK_CHARS]
        chunks.append({
            "text": piece,
            "heading": "",
            "chunk_type": "file",
            "chunk_index": 0,
        })

    return chunks


CODE_STARTERS = ("def ", "class ", "function ", "const ")


def chunk_code(text: str) -> list[dict]:
    """Split code on top-level symbol definitions, max MAX_CHUNK_CHARS per chunk."""
    lines = text.splitlines(keepends=True)
    chunks: list[dict] = []
    current_symbol = ""
    current_lines: list[str] = []

    def flush(symbol, body_lines):
        body = "".join(body_lines).strip()
        if not body:
            return
        while body:
            piece = body[:MAX_CHUNK_CHARS]
            chunks.append({
                "text": piece,
                "heading": symbol,
                "chunk_type": "symbol",
                "chunk_index": len(chunks),
            })
            body = body[MAX_CHUNK_CHARS:]

    for line in lines:
        # Top-level only: lines that start without indentation
        if line and not line[0].isspace():
            stripped = line.lstrip()
            if any(stripped.startswith(s) for s in CODE_STARTERS):
                flush(current_symbol, current_lines)
                current_symbol = stripped.split("(")[0].split(" ")[1] if " " in stripped else stripped.rstrip()
                current_lines = [line]
                continue
        current_lines.append(line)

    flush(current_symbol, current_lines)

    if not chunks:
        piece = text.strip()[:MAX_CHUNK_CHARS]
        chunks.append({
            "text": piece,
            "heading": "",
            "chunk_type": "file",
            "chunk_index": 0,
        })

    return chunks


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def collect_files(silo_dir: Path, silo: str) -> list[Path]:
    """Collect indexable files for a silo directory."""
    results: list[Path] = []
    exts = {".md"}
    if silo in CODE_SILOS:
        exts |= {".ts", ".py", ".gd"}

    for root, dirs, files in os.walk(silo_dir):
        # Prune excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        root_path = Path(root)
        if is_excluded(root_path.relative_to(silo_dir)):
            continue
        for fname in files:
            fpath = root_path / fname
            if fpath.suffix in exts:
                try:
                    rel = fpath.relative_to(silo_dir)
                    if not is_excluded(rel):
                        results.append(fpath)
                except ValueError:
                    pass
    return results


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def last_index_stamp_path(silo: str) -> Path:
    return MEWVAULT_DIR / f".last-index-{silo}"


def read_last_stamp(silo: str) -> float:
    p = last_index_stamp_path(silo)
    try:
        return float(p.read_text().strip())
    except Exception:
        return 0.0


def write_last_stamp(silo: str) -> None:
    MEWVAULT_DIR.mkdir(parents=True, exist_ok=True)
    last_index_stamp_path(silo).write_text(str(time.time()))


# ---------------------------------------------------------------------------
# Queue fallback
# ---------------------------------------------------------------------------

def queue_for_later(silo: str, files: list[str]) -> None:
    """Append to pending queue when Ollama is offline."""
    MEWVAULT_DIR.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        "silo": silo,
        "files": files,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    with PENDING_QUEUE.open("a") as f:
        f.write(entry + "\n")


# ---------------------------------------------------------------------------
# Main indexing logic
# ---------------------------------------------------------------------------

def index_files(collection, silo: str, files: list[Path], silo_dir: Path) -> tuple[int, int]:
    """Index a list of files. Returns (chunks_indexed, files_indexed)."""
    ingested_at = datetime.now(timezone.utc).isoformat()
    chunks_total = 0
    files_total = 0

    # Build batch
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    for fpath in files:
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = str(fpath.relative_to(silo_dir))
        ext = fpath.suffix
        mtime = fpath.stat().st_mtime

        if ext == ".md":
            raw_chunks = chunk_markdown(text, str(fpath))
        elif ext in {".ts", ".py", ".gd"}:
            raw_chunks = chunk_code(text)
        else:
            continue

        for c in raw_chunks:
            doc_id = f"{silo}::{rel}::{c['chunk_index']}"
            ids.append(doc_id)
            texts.append(c["text"])
            metadatas.append({
                "silo": silo,
                "path": rel,
                "ext": ext,
                "chunk_index": c["chunk_index"],
                "chunk_type": c["chunk_type"],
                "heading": c.get("heading", ""),
                "mtime": mtime,
                "ingested_at": ingested_at,
            })

        files_total += 1

    if not ids:
        return 0, 0

    # Batch embed
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch_texts = texts[i:i + EMBED_BATCH]
        batch_embs = embed(batch_texts)
        if batch_embs is None:
            return None, None  # Signal: Ollama offline
        all_embeddings.extend(batch_embs)

    # Upsert into ChromaDB in safe batches (max 5000 per call)
    UPSERT_BATCH = 5000
    for i in range(0, len(ids), UPSERT_BATCH):
        collection.upsert(
            ids=ids[i:i + UPSERT_BATCH],
            documents=texts[i:i + UPSERT_BATCH],
            embeddings=all_embeddings[i:i + UPSERT_BATCH],
            metadatas=metadatas[i:i + UPSERT_BATCH],
        )
    chunks_total = len(ids)
    return chunks_total, files_total


def main() -> None:
    parser = argparse.ArgumentParser(description="MewVault semantic indexer")
    parser.add_argument("--silo", required=True, choices=list(SILO_DIRS.keys()))
    parser.add_argument("--files", default="", help="Comma-separated absolute paths to index")
    parser.add_argument("--full", action="store_true", help="Delete silo docs and reindex all")
    args = parser.parse_args()

    silo = args.silo
    silo_dir = SILO_DIRS[silo]

    if not silo_dir.exists():
        print(f"indexed 0 chunks from 0 files (silo: {silo}) — directory not found")
        sys.exit(0)

    # Determine collection name
    collection_name = COLLECTION_MAP.get(silo, "mewvault-shared")

    # Import chromadb (graceful missing)
    try:
        import chromadb  # type: ignore
    except ImportError:
        print(f"indexed 0 chunks from 0 files (silo: {silo}) — chromadb not installed")
        sys.exit(0)

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # --full: delete all docs for this silo then reindex
    if args.full:
        try:
            existing = collection.get(where={"silo": silo}, include=[])
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

    # Determine files to index
    if args.files:
        target_files = [Path(p.strip()) for p in args.files.split(",") if p.strip()]
    else:
        last_stamp = read_last_stamp(silo) if not args.full else 0.0
        all_files = collect_files(silo_dir, silo)
        if last_stamp > 0:
            target_files = [f for f in all_files if f.stat().st_mtime > last_stamp]
        else:
            target_files = all_files

    if not target_files:
        print(f"indexed 0 chunks from 0 files (silo: {silo}) — nothing new")
        if not args.files:
            write_last_stamp(silo)
        sys.exit(0)

    # Index
    chunks, files = index_files(collection, silo, target_files, silo_dir)

    if chunks is None:
        # Ollama offline — queue for later
        queue_for_later(silo, [str(f) for f in target_files])
        print(f"indexed 0 chunks from 0 files (silo: {silo}) — Ollama offline, queued {len(target_files)} files")
        sys.exit(0)

    if not args.files:
        write_last_stamp(silo)

    print(f"indexed {chunks} chunks from {files} files (silo: {silo})")


if __name__ == "__main__":
    main()
