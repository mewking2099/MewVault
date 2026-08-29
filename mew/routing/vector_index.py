"""Stage 2 semantic retrieval — ChromaDB-backed node search.

Indexes graph nodes by label + source_file so blast_radius can find nodes
that keyword matching misses (e.g. 'auth_handler' when query says 'authentication').

Storage: ~/.mew/chroma/ — persistent embedded ChromaDB, one collection per project.
Project key derived from graph_path: two path segments above graphify-out/.

Graceful degradation: all public functions return empty/zero on any ChromaDB error.
Set MEW_NO_VECTOR=1 to disable entirely.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_CHROMA_DIR = Path.home() / ".mew" / "chroma"
_BATCH = 2000


def project_key(graph_path: Path) -> str:
    """Derive a stable ChromaDB collection name from graph_path.

    .../software-projects/dsaas/graphify-out/graph.json → software_projects_dsaas
    Collection names: 3–63 chars, alphanumeric + underscore.
    """
    project_root = graph_path.parent.parent
    parts = project_root.parts[-2:]
    raw = "_".join(parts)
    clean = re.sub(r"[^a-zA-Z0-9]", "_", raw).strip("_")
    clean = re.sub(r"_+", "_", clean)
    return clean[:63] or "default"


def build(graph_path: Path) -> tuple[int, str]:
    """Index all nodes from graph.json into ChromaDB.

    Returns (nodes_indexed, collection_name). Returns (0, '') on failure.
    Deletes and recreates the collection for a clean rebuild.
    """
    if os.environ.get("MEW_NO_VECTOR"):
        return 0, ""
    import json

    if not graph_path.exists():
        return 0, ""

    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception:
        return 0, ""

    nodes = data.get("nodes", [])
    if not nodes:
        return 0, ""

    try:
        import chromadb
        _CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
        name = project_key(graph_path)

        try:
            client.delete_collection(name)
        except Exception:
            pass
        collection = client.get_or_create_collection(name)

        ids, docs, metas = [], [], []
        for node in nodes:
            nid = node.get("id")
            if not nid:
                continue
            label    = node.get("label") or ""
            norm     = node.get("norm_label") or ""
            src_stem = Path(node.get("source_file") or "").stem
            ftype    = node.get("file_type") or ""
            doc = f"{label} {norm} {src_stem} {ftype}".strip()
            ids.append(nid)
            docs.append(doc or nid)
            metas.append({
                "source_file": node.get("source_file") or "",
                "file_type":   ftype,
                "community":   str(node.get("community") or ""),
            })

        for i in range(0, len(ids), _BATCH):
            collection.add(
                ids=ids[i:i + _BATCH],
                documents=docs[i:i + _BATCH],
                metadatas=metas[i:i + _BATCH],
            )

        return len(ids), name

    except Exception:
        return 0, ""


def search(query: str, graph_path: Path, n_results: int = 30) -> list[str]:
    """Return up to n_results node IDs semantically similar to query.

    Returns [] when MEW_NO_VECTOR is set, index not built, or on any error.
    """
    if os.environ.get("MEW_NO_VECTOR"):
        return []
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
        name = project_key(graph_path)
        collection = client.get_collection(name)
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )
        return results["ids"][0] if results["ids"] else []
    except Exception:
        return []


def stats(graph_path: Path) -> dict:
    """Return collection stats dict for display."""
    name = project_key(graph_path)
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
        col = client.get_collection(name)
        return {"collection": name, "count": col.count(), "status": "indexed"}
    except Exception:
        return {"collection": name, "count": 0, "status": "not indexed"}
