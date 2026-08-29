"""Graph-based complexity scorer (Phase 3).

Inputs (from graph neighborhood nodes):
  file_count       — distinct source files touched → breadth
  community_span   — distinct community IDs → cross-module coupling
  type_diversity   — distinct file_type values (code/document/rationale) → nature mix

Score = file_count × log2(community_span + 1) × type_diversity_factor
Buckets: simple | moderate | complex

When the graph is empty, falls back to keyword-based complexity from heuristics.py.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from mew.routing.blast_radius import find_seed_nodes, expand_neighborhood


def compute(graph_path: Path, task_text: str, neighborhood: set[str] | None = None) -> tuple[float, str]:
    """Return (score, bucket) for the task's neighborhood nodes."""
    if not graph_path.exists():
        return 0.0, "unknown"

    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0.0, "unknown"

    nodes: list[dict] = data.get("nodes", [])
    edges: list[dict] = data.get("links", data.get("edges", []))

    if neighborhood is None:
        seeds = find_seed_nodes(nodes, task_text)
        neighborhood = expand_neighborhood(nodes, edges, seeds, hops=2)

    if not neighborhood:
        return 0.0, "simple"

    # Filter to neighborhood nodes
    neighborhood_nodes = [n for n in nodes if n.get("id") in neighborhood]

    file_count = len({n.get("source_file") for n in neighborhood_nodes if n.get("source_file")})
    community_span = len({n.get("community") for n in neighborhood_nodes if n.get("community") is not None})
    type_diversity = len({n.get("file_type") for n in neighborhood_nodes if n.get("file_type")})

    # score: breadth × coupling × type factor
    score = file_count * math.log2(community_span + 1) * max(type_diversity, 1)
    bucket = _bucket(score, file_count)
    return round(score, 2), bucket


def _bucket(score: float, file_count: int) -> str:
    # File count alone overrides when score is underweighted by missing edges
    if file_count > 15 or score > 20:
        return "complex"
    if file_count > 5 or score > 5:
        return "moderate"
    return "simple"
