"""Graph-neighborhood blast-radius predictor (Phase 3).

Two-step:
1. find_seed_nodes — keyword match against node labels / source_file in the graph
2. expand_neighborhood — BFS up to `hops` from seed nodes via edge traversal
Result: (node_count, bucket)

When the graph has no edges (current state), expansion returns seed nodes only
(effectively 0-hop). Bucket is still computed; confidence.json signals the gap.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


_BUCKET_THRESHOLDS = {"small": 5, "medium": 20}  # inclusive upper bounds


def compute(graph_path: Path, task_text: str, hops: int = 2) -> tuple[int, str]:
    """Return (neighborhood_size, bucket) for the task against the graph."""
    if not graph_path.exists():
        return 0, "unknown"

    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0, "unknown"

    nodes: list[dict] = data.get("nodes", [])
    edges: list[dict] = data.get("links", data.get("edges", []))

    # Stage 1: keyword BFS
    seeds = find_seed_nodes(nodes, task_text)
    neighborhood = expand_neighborhood(nodes, edges, seeds, hops)

    # Stage 2: semantic expansion — union ChromaDB results with BFS neighborhood
    from mew.routing import vector_index
    semantic_ids = vector_index.search(task_text, graph_path)
    neighborhood |= set(semantic_ids)

    count = len(neighborhood)
    return count, _bucket(count)


def find_seed_nodes(nodes: list[dict], task_text: str) -> set[str]:
    """Match task keywords against node norm_label and source_file basename."""
    keywords = _extract_keywords(task_text)
    if not keywords:
        return set()

    matched: set[str] = set()
    for node in nodes:
        label = (node.get("norm_label") or "").lower()
        src = Path(node.get("source_file") or "").stem.lower()
        nid = node.get("id")
        if not nid:
            continue
        for kw in keywords:
            if kw in label or kw in src:
                matched.add(nid)
                break
    return matched


def expand_neighborhood(nodes: list[dict], edges: list[dict],
                        seeds: set[str], hops: int) -> set[str]:
    """BFS from seed node IDs up to `hops` traversals over edges."""
    if not edges:
        return set(seeds)

    # Build adjacency (undirected)
    adj: dict[str, set[str]] = {}
    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src and tgt:
            adj.setdefault(src, set()).add(tgt)
            adj.setdefault(tgt, set()).add(src)

    visited = set(seeds)
    frontier = set(seeds)
    for _ in range(hops):
        next_frontier: set[str] = set()
        for nid in frontier:
            for neighbor in adj.get(nid, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
        if not frontier:
            break
    return visited


def _extract_keywords(task_text: str) -> list[str]:
    """Extract lowercase alphanum tokens ≥4 chars, excluding stop words."""
    _STOP = {
        "this", "that", "with", "from", "have", "will", "your", "they",
        "what", "when", "where", "which", "there", "their", "about",
        "more", "also", "into", "some", "would", "could", "should",
        "please", "make", "just", "like", "then", "than", "here",
        "been", "does", "need", "want", "find", "look",
    }
    tokens = re.findall(r"[a-z][a-z0-9_]{3,}", task_text.lower())
    return [t for t in tokens if t not in _STOP]


def _bucket(count: int) -> str:
    if count <= _BUCKET_THRESHOLDS["small"]:
        return "small"
    if count <= _BUCKET_THRESHOLDS["medium"]:
        return "medium"
    return "large"
