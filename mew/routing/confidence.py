"""Per-silo graph confidence scorer.

Reads graphify-out/graph.json (if present) and produces a confidence bucket.
Writes graphify-out/confidence.json with the scored result.

Inputs: node count, edge density, recency of last graphify update, orphan ratio.
Buckets: high | medium | low | insufficient
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


CONFIDENCE_LEVELS = ("high", "medium", "low", "insufficient")


def score_silo(silo_root: Path) -> dict:
    """Score one silo's graphify-out/ and return a confidence record."""
    graph_path = silo_root / "graphify-out" / "graph.json"

    if not graph_path.exists():
        return _record(silo_root.name, "insufficient", 0, 0, 0.0, 1.0, None,
                       "no graph.json — run graphify build .")

    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return _record(silo_root.name, "insufficient", 0, 0, 0.0, 1.0, None,
                       f"graph.json unreadable: {e}")

    nodes = data.get("nodes", [])
    edges = data.get("links", data.get("edges", []))
    node_count = len(nodes)
    edge_count = len(edges)

    if node_count < 5:
        return _record(silo_root.name, "insufficient", node_count, edge_count,
                       0.0, 1.0, _mtime(graph_path), "too few nodes")

    # Edge density: edges / (n*(n-1)/2) — cap denominator to avoid overflow
    max_possible = node_count * (node_count - 1) / 2
    edge_density = edge_count / max_possible if max_possible > 0 else 0.0

    # Orphan ratio: nodes with no edges
    connected = set()
    for e in edges:
        connected.add(e.get("source"))
        connected.add(e.get("target"))
    orphans = sum(1 for n in nodes if n.get("id") not in connected)
    orphan_ratio = orphans / node_count if node_count > 0 else 1.0

    # Recency: hours since last graphify update (stale > 24h is penalised)
    mtime = _mtime(graph_path)
    age_hours = _age_hours(graph_path)

    bucket = _bucket(node_count, edge_density, orphan_ratio, age_hours)
    reason = _reason(node_count, edge_density, orphan_ratio, age_hours)

    return _record(silo_root.name, bucket, node_count, edge_count,
                   edge_density, orphan_ratio, mtime, reason)


def score_and_write(workspace_root: Path, silo_name: str | None = None) -> dict[str, dict]:
    """Score silos and write graphify-out/confidence.json under each silo root."""
    silo_dirs = _find_silo_dirs(workspace_root, silo_name)
    results: dict[str, dict] = {}

    for silo_root in silo_dirs:
        record = score_silo(silo_root)
        results[record["silo"]] = record
        out_dir = silo_root / "graphify-out"
        if out_dir.exists():
            out_path = out_dir / "confidence.json"
            out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    return results


# ── internals ─────────────────────────────────────────────────────────────────

def _bucket(node_count: int, edge_density: float, orphan_ratio: float, age_hours: float) -> str:
    if node_count < 5:
        return "insufficient"
    if edge_density == 0.0:
        # Nodes parsed but no relationship edges — graph is structurally incomplete
        return "low" if node_count >= 100 else "insufficient"
    if orphan_ratio > 0.8 or age_hours > 168:  # >80% orphans or >1 week stale
        return "low"
    if edge_density >= 0.05 and orphan_ratio < 0.3 and age_hours < 48:
        return "high"
    return "medium"


def _reason(node_count: int, edge_density: float, orphan_ratio: float, age_hours: float) -> str:
    parts = []
    if edge_density == 0.0:
        parts.append("no edges (run graphify build . to build relationships)")
    elif edge_density < 0.01:
        parts.append(f"sparse edges (density={edge_density:.4f})")
    if orphan_ratio > 0.5:
        parts.append(f"high orphan ratio ({orphan_ratio:.0%})")
    if age_hours > 168:
        parts.append(f"stale graph ({age_hours:.0f}h old)")
    elif age_hours > 48:
        parts.append(f"graph is {age_hours:.0f}h old (consider refreshing)")
    return "; ".join(parts) if parts else "ok"


def _record(silo: str, bucket: str, node_count: int, edge_count: int,
            edge_density: float, orphan_ratio: float, mtime: str | None,
            reason: str) -> dict:
    return {
        "silo": silo,
        "bucket": bucket,
        "node_count": node_count,
        "edge_count": edge_count,
        "edge_density": round(edge_density, 6),
        "orphan_ratio": round(orphan_ratio, 4),
        "graph_updated_at": mtime,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }


def _mtime(path: Path) -> str | None:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _age_hours(path: Path) -> float:
    try:
        return (time.time() - path.stat().st_mtime) / 3600
    except OSError:
        return float("inf")


_SILO_NAMES = {
    "software-projects", "game-lab", "design-studio",
    "wiki", "career-studio", "learn-lab", "idea-hub", "mewvault",
}


def _find_silo_dirs(workspace_root: Path, silo_name: str | None) -> list[Path]:
    if silo_name:
        candidates = [workspace_root / silo_name]
    else:
        candidates = [workspace_root / s for s in _SILO_NAMES]

    return [p for p in candidates if (p / "graphify-out").exists()]
