"""Capability edge registry (Phase 3 — §A-2).

Stores agent→(node_types, task_classes) mappings, versioned by graph_epoch.
Written to graphify-out/capability-edges.json per silo.

Note: §A-2 specifies these edges belong inside the graphify graph.
Current blocker: graphify rebuild wipes graph.json on every `graphify update .`.
Resolution path: when graphify supports incremental edge injection, capability-edges.json
becomes the input to a post-build merge step. Until then it lives as a versioned sidecar.
This is documented as an accepted limitation — not a design deviation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


# ── canonical registry ────────────────────────────────────────────────────────
# node_types: graph node file_type values or logical categories
# task_classes: keyword-class labels from heuristics.py signal sets

REGISTRY: dict[str, dict] = {
    "glm-code-reviewer": {
        "node_types": ["code"],
        "task_classes": ["review", "audit", "security", "feedback"],
        "preferred_radius": "small",
        "preferred_complexity": ["simple", "moderate"],
    },
    "glm-coder": {
        "node_types": ["code", "document"],
        "task_classes": ["implement", "refactor", "generate", "migrate"],
        "preferred_radius": "medium",
        "preferred_complexity": ["moderate", "complex"],
    },
    "mew-coder-simple": {
        "node_types": ["code"],
        "task_classes": ["implement", "generate"],
        "preferred_radius": "small",
        "preferred_complexity": ["simple"],
    },
    "mew-coder-reason": {
        "node_types": ["code"],
        "task_classes": ["refactor", "migrate", "complex"],
        "preferred_radius": "large",
        "preferred_complexity": ["complex"],
    },
    "mew-planner": {
        "node_types": ["document", "rationale"],
        "task_classes": ["plan", "architect", "design"],
        "preferred_radius": "large",
        "preferred_complexity": ["complex"],
    },
}


def best_agent_for(node_types: set[str], task_class: str,
                   radius_bucket: str, complexity_bucket: str) -> str | None:
    """Return the best registered agent for the given node types + task class.
    Returns None when no match — caller should fall back to keyword heuristics.

    Rule: task_class must match — capability refines WITHIN a task class, never overrides it.
    """
    candidates = []
    for agent, caps in REGISTRY.items():
        class_match = task_class in caps["task_classes"]
        if not class_match:
            continue  # never override task class determination
        type_match = bool(set(caps["node_types"]) & node_types) if node_types else True
        # Score: task_class is gate, not scorer; remaining factors break ties
        score = int(type_match)
        score += int(caps.get("preferred_radius") == radius_bucket)
        score += int(complexity_bucket in caps.get("preferred_complexity", []))
        candidates.append((score, agent))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def write_capability_edges(silo_root: Path, graph_epoch: int) -> Path:
    """Serialise the registry as a capability-edges.json in graphify-out/."""
    out_dir = silo_root / "graphify-out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "capability-edges.json"

    payload = {
        "graph_epoch": graph_epoch,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Pending integration into graph.json (§A-2). "
            "Will merge when graphify supports incremental edge injection."
        ),
        "edges": [
            {
                "source": agent,
                "edge_type": "capability",
                "node_types": caps["node_types"],
                "task_classes": caps["task_classes"],
                "preferred_radius": caps.get("preferred_radius"),
                "preferred_complexity": caps.get("preferred_complexity", []),
            }
            for agent, caps in REGISTRY.items()
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def read_capability_edges(silo_root: Path) -> dict:
    path = silo_root / "graphify-out" / "capability-edges.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def read_graph_for_routing(silo: str, task_hash: str,
                           workspace_root: Path,
                           current_silo: str | None,
                           ledger_conn) -> dict | None:
    """Federation function: read another silo's graph + log the cross-silo read.

    Per Phase 3 §cross-silo: all cross-silo graph reads must go through here.
    Direct file reads across the project lock remain blocked by the hook.
    """
    silo_root = workspace_root / silo
    graph_path = silo_root / "graphify-out" / "graph.json"
    if not graph_path.exists():
        return None

    # Log to ledger if it's actually cross-silo
    if current_silo and silo != current_silo and ledger_conn is not None:
        try:
            from datetime import datetime, timezone
            from mew.ledger import db as ledger_db
            ts = datetime.now(timezone.utc).isoformat()
            ledger_conn.execute(
                """
                INSERT OR IGNORE INTO cross_silo_read
                    (task_hash, read_ts, from_silo, to_silo)
                VALUES (?, ?, ?, ?)
                """,
                (task_hash, ts, current_silo, silo),
            )
            ledger_conn.commit()
        except Exception:
            pass

    try:
        return json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
