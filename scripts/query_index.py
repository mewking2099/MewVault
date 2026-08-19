#!/usr/bin/env python3
"""
query_index.py — CLI fallback semantic query when MCP offline.

Usage:
    python3 mewvault/scripts/query_index.py --silo <silo|any|career> --q "<query>" [--n 5]

    --silo any     → queries mewvault-shared (never mewvault-career)
    --silo career  → queries mewvault-career
    --silo <other> → queries mewvault-shared filtered by silo
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

CHROMA_PATH = Path.home() / ".mewvault" / "chroma"
OLLAMA_URL = "http://localhost:11434/v1/embeddings"
OLLAMA_MODEL = "nomic-embed-text"
OLLAMA_TIMEOUT = 5

COLLECTION_MAP = {
    "career": "mewvault-career",
    "learn":  "mewvault-learn",
}


def embed_query(text: str) -> list[float] | None:
    body = json.dumps({"model": OLLAMA_MODEL, "input": [text]}).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as r:
            data = json.loads(r.read())
        return data["data"][0]["embedding"]
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="MewVault semantic query CLI")
    parser.add_argument("--silo", required=True, help="Silo name or 'any'")
    parser.add_argument("--q", required=True, dest="query", help="Query text")
    parser.add_argument("--n", type=int, default=5, help="Number of results")
    args = parser.parse_args()

    if not CHROMA_PATH.exists():
        print("[semantic search offline — ChromaDB store not found]")
        sys.exit(0)

    try:
        import chromadb  # type: ignore
    except ImportError:
        print("[semantic search offline — chromadb not installed]")
        sys.exit(0)

    # Embed query
    embedding = embed_query(args.query)
    if embedding is None:
        print("[semantic search offline — Ollama not running]")
        sys.exit(0)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    silo = args.silo.lower()

    # Determine collection and where-filter
    collection_name = COLLECTION_MAP.get(silo, "mewvault-shared")
    where_filter = None
    if silo not in ("any", "career", "learn") and collection_name == "mewvault-shared":
        where_filter = {"silo": silo}

    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        print(f"[semantic search offline — collection '{collection_name}' not found]")
        sys.exit(0)

    query_kwargs: dict = {
        "query_embeddings": [embedding],
        "n_results": args.n,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        query_kwargs["where"] = where_filter

    try:
        results = collection.query(**query_kwargs)
    except Exception as exc:
        print(f"[semantic search error — {exc}]")
        sys.exit(0)

    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    if not docs:
        print("[no results found]")
        sys.exit(0)

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        doc_id = f"{meta.get('silo', '?')}::{meta.get('path', '?')}::{meta.get('chunk_index', '?')}"
        # ChromaDB cosine distance → similarity score (1 - distance for cosine space)
        score = round(1.0 - dist, 4)
        heading = meta.get("heading", "").strip()
        # Print heading if available, else first line of doc
        preview_header = heading if heading else (doc.splitlines()[0] if doc else "")
        preview_body = doc[:300].strip()
        print(f"[{i}] {doc_id} (score: {score})")
        if preview_header:
            print(f"    {preview_header}")
        print(f"    {preview_body}")
        print()


if __name__ == "__main__":
    main()
