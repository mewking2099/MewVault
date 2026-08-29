"""mew route — shadow-mode prediction and baseline reporting (Phase 2).

Sub-commands:
  --dry-run <task>   Predict agent/model/silo/buckets. Log to ledger. Never dispatch.
  baseline           Mis-routing rate report from paired dry-run + actual dispatch rows.
  status             Current per-silo graph confidence and prediction coverage.
  confidence         Re-score graphify-out/ and write confidence.json for each silo.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

from mew.workspace import find_workspace_root
from mew.ledger import db as ledger_db
from mew.routing import heuristics
from mew.routing import confidence as conf_mod
from mew.routing import blast_radius as blast_radius_mod
from mew.routing import complexity as complexity_mod
from mew.routing import capability as capability_mod
from mew.commands.dispatch import _detect_silo, _read_active_project, _read_confidence_bucket, _project_graph_path


def run_route(args) -> None:
    workspace_root = find_workspace_root()
    action = getattr(args, "route_action", None)

    if action == "dry-run":
        _dry_run(args, workspace_root)
    elif action == "baseline":
        _baseline(workspace_root)
    elif action == "status":
        _status(workspace_root)
    elif action == "confidence":
        _confidence(workspace_root, getattr(args, "silo", None))
    elif action == "drift":
        _drift(workspace_root, getattr(args, "n", 20))
    elif action == "capability":
        _capability(workspace_root)
    else:
        print("mew route: sub-commands: dry-run <task> | baseline | status | confidence | drift | capability",
              file=sys.stderr)
        sys.exit(1)


# ── dry-run ───────────────────────────────────────────────────────────────────

def _dry_run(args, workspace_root: Path) -> None:
    task = (getattr(args, "task", None) or "").strip()
    if not task:
        print("route dry-run: task is empty", file=sys.stderr)
        sys.exit(1)

    silo = _detect_silo(workspace_root) or "unknown"
    project_lock = _read_active_project(workspace_root)

    # Phase 3: graph-aware blast-radius + complexity; fall back to keyword buckets
    graph_path = _project_graph_path(workspace_root, silo, project_lock)
    confidence_bucket = _read_confidence_bucket(workspace_root, silo, project_lock)

    if graph_path.exists():
        radius_count, radius_bucket = blast_radius_mod.compute(graph_path, task)
        complexity_score, complexity_bucket = complexity_mod.compute(graph_path, task)
        radius_source = "graph"
    else:
        radius_count = 0
        radius_bucket = heuristics.predict_blast_radius(task)
        complexity_score = 0.0
        complexity_bucket = heuristics.predict_complexity(task)
        radius_source = "keyword"

    # Keyword agent prediction + capability refinement (within same task class)
    kw_agent = heuristics.predict_agent(task)
    cap_agent = capability_mod.best_agent_for(
        node_types={"code"},  # default; graph node types would refine this
        task_class=_task_class_from_agent(kw_agent),
        radius_bucket=radius_bucket,
        complexity_bucket=complexity_bucket,
    )
    agent = cap_agent if cap_agent else kw_agent
    model = heuristics.predict_model(agent)

    # Explicit low-confidence fallback message (per Phase 3 acceptance criteria)
    if confidence_bucket in ("low", "insufficient"):
        print(f"[router] graph confidence {confidence_bucket}, using default routing ({agent})")
    else:
        print(f"[router suggests]")
    print(f"  agent          : {agent}")
    print(f"  model          : {model}")
    print(f"  silo           : {silo}")
    print(f"  confidence     : {confidence_bucket}")
    print(f"  blast-radius   : {radius_bucket}  ({radius_count} nodes, source={radius_source})")
    print(f"  complexity     : {complexity_bucket}  (score={complexity_score:.1f})")
    print(f"  (dry-run — prediction only, nothing dispatched)")

    # Log to ledger
    try:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)
        task_hash = ledger_db.write_route_prediction(
            conn,
            task_text=task,
            predicted_agent=agent,
            predicted_model=model,
            predicted_silo=silo,
            blast_radius_bucket=radius_bucket,
            complexity_bucket=complexity_bucket,
        )
        if task_hash:
            print(f"  task_hash      : {task_hash}  (logged — will reconcile on actual dispatch)")
    except Exception as e:
        print(f"route: ledger write failed: {e}", file=sys.stderr)


# ── baseline ──────────────────────────────────────────────────────────────────

def _baseline(workspace_root: Path) -> None:
    try:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)
    except Exception as e:
        print(f"route baseline: cannot open ledger: {e}", file=sys.stderr)
        sys.exit(1)

    total = conn.execute("SELECT COUNT(*) FROM route_prediction").fetchone()[0]
    reconciled = conn.execute(
        "SELECT COUNT(*) FROM route_prediction WHERE actual_dispatch_ts IS NOT NULL"
    ).fetchone()[0]
    agent_diverge = conn.execute(
        "SELECT COUNT(*) FROM route_prediction WHERE agent_diverged = 1"
    ).fetchone()[0]
    model_diverge = conn.execute(
        "SELECT COUNT(*) FROM route_prediction WHERE model_diverged = 1"
    ).fetchone()[0]

    if reconciled == 0:
        print("route baseline: no reconciled predictions yet.")
        print(f"  Total dry-run predictions : {total}")
        print(f"  Reconciled (actual fired) : {reconciled}")
        print(f"  Need 100 reconciled pairs for a valid baseline report.")
        return

    agent_rate = agent_diverge / reconciled * 100
    model_rate = model_diverge / reconciled * 100

    print(f"route baseline  ({reconciled} reconciled pairs of {total} predictions)")
    print(f"  agent divergence  : {agent_diverge}/{reconciled}  ({agent_rate:.1f}%)")
    print(f"  model divergence  : {model_diverge}/{reconciled}  ({model_rate:.1f}%)")

    # Break down by silo
    silo_rows = conn.execute(
        """
        SELECT predicted_silo,
               COUNT(*) as n,
               SUM(agent_diverged) as ag_div
        FROM route_prediction
        WHERE actual_dispatch_ts IS NOT NULL
        GROUP BY predicted_silo
        ORDER BY n DESC
        """
    ).fetchall()
    if silo_rows:
        print()
        print("  by silo:")
        for silo, n, ag in silo_rows:
            rate = (ag or 0) / n * 100
            print(f"    {(silo or 'unknown'):<25} {n:>4} pairs   agent divergence {rate:.1f}%")

    # Break down by blast-radius bucket
    radius_rows = conn.execute(
        """
        SELECT blast_radius_bucket,
               COUNT(*) as n,
               SUM(agent_diverged) as ag_div
        FROM route_prediction
        WHERE actual_dispatch_ts IS NOT NULL
        GROUP BY blast_radius_bucket
        """
    ).fetchall()
    if radius_rows:
        print()
        print("  by blast-radius bucket:")
        for bucket, n, ag in radius_rows:
            rate = (ag or 0) / n * 100
            print(f"    {(bucket or 'unknown'):<10} {n:>4} pairs   agent divergence {rate:.1f}%")

    if reconciled < 100:
        print()
        print(f"  NOTE: {reconciled} reconciled pairs < 100 threshold — "
              "results are indicative only.")


# ── status ────────────────────────────────────────────────────────────────────

def _status(workspace_root: Path) -> None:
    # Prediction coverage
    try:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)
        total_pred = conn.execute("SELECT COUNT(*) FROM route_prediction").fetchone()[0]
        reconciled = conn.execute(
            "SELECT COUNT(*) FROM route_prediction WHERE actual_dispatch_ts IS NOT NULL"
        ).fetchone()[0]
        total_dispatch = conn.execute("SELECT COUNT(*) FROM dispatch").fetchone()[0]
    except Exception:
        total_pred = reconciled = total_dispatch = 0

    print("mew route status")
    print(f"  dispatches total    : {total_dispatch}")
    print(f"  dry-run predictions : {total_pred}")
    print(f"  reconciled pairs    : {reconciled}")
    print()

    # Per-silo confidence
    conf_files = list(workspace_root.glob("*/graphify-out/confidence.json"))
    if not conf_files:
        print("  no confidence.json found — run: mew route confidence")
        return

    print("  silo confidence:")
    for cf in sorted(conf_files):
        try:
            rec = json.loads(cf.read_text())
            silo   = rec.get("silo", cf.parent.parent.name)
            bucket = rec.get("bucket", "?")
            nodes  = rec.get("node_count", 0)
            edges  = rec.get("edge_count", 0)
            reason = rec.get("reason", "")
            print(f"    {silo:<25} {bucket:<12} nodes={nodes:>5}  edges={edges:>5}  {reason}")
        except Exception:
            print(f"    {cf}: unreadable")


# ── confidence scoring ────────────────────────────────────────────────────────

def _confidence(workspace_root: Path, silo_name: str | None) -> None:
    results = conf_mod.score_and_write(workspace_root, silo_name)
    if not results:
        print("route confidence: no graphify-out/ directories found")
        return
    for silo, rec in sorted(results.items()):
        bucket = rec["bucket"]
        nodes  = rec["node_count"]
        edges  = rec["edge_count"]
        reason = rec["reason"]
        print(f"{silo:<25} {bucket:<12} nodes={nodes:>5}  edges={edges:>5}  {reason}")


# ── drift report (Phase 3) ────────────────────────────────────────────────────

def _drift(workspace_root: Path, n: int) -> None:
    try:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)
    except Exception as e:
        print(f"route drift: cannot open ledger: {e}", file=sys.stderr)
        sys.exit(1)

    # Dispatches that have both predicted_radius and actual_radius
    paired = conn.execute(
        """
        SELECT dispatch_ts, agent, predicted_radius, actual_radius,
               abs(actual_radius - predicted_radius) as delta
        FROM dispatch
        WHERE predicted_radius IS NOT NULL AND actual_radius IS NOT NULL
        ORDER BY dispatch_ts DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()

    total_paired = conn.execute(
        "SELECT COUNT(*) FROM dispatch WHERE predicted_radius IS NOT NULL AND actual_radius IS NOT NULL"
    ).fetchone()[0]
    total_pred = conn.execute(
        "SELECT COUNT(*) FROM dispatch WHERE predicted_radius IS NOT NULL"
    ).fetchone()[0]

    print(f"route drift  ({total_paired} paired of {total_pred} with predicted_radius)")
    if not paired:
        print("  No reconciled radius pairs yet.")
        print("  To populate actual_radius: mew ledger update-radius <dispatch_ts> <count>")
        return

    avg_delta = sum(r[4] for r in paired) / len(paired)
    print(f"  avg |actual - predicted| : {avg_delta:.1f} nodes")
    print()
    header = f"{'dispatch_ts':28} {'agent':25} {'predicted':>10} {'actual':>8} {'delta':>6}"
    print(header)
    print("-" * len(header))
    for ts, agent, pred, actual, delta in paired:
        print(f"{ts:28} {(agent or '?'):25} {pred:>10} {actual:>8} {delta:>6}")


# ── capability management (Phase 3 §A-2) ─────────────────────────────────────

def _capability(workspace_root: Path) -> None:
    from mew.ledger import db as ledger_db
    try:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)
        epoch = ledger_db.current_epoch(conn)
    except Exception:
        epoch = 1

    silo_dirs = [d for d in workspace_root.iterdir()
                 if d.is_dir() and (d / "graphify-out").exists()]
    if not silo_dirs:
        print("route capability: no graphify-out/ silos found")
        return

    for silo_root in sorted(silo_dirs):
        out_path = capability_mod.write_capability_edges(silo_root, epoch)
        print(f"  wrote: {out_path.relative_to(workspace_root)}")

    print()
    print(f"  agents in registry: {list(capability_mod.REGISTRY.keys())}")
    print(f"  graph_epoch        : {epoch}")
    print("  (§A-2 note: pending integration into graph.json — see capability-edges.json)")


# ── helpers ───────────────────────────────────────────────────────────────────

def _task_class_from_agent(agent: str) -> str:
    if "reviewer" in agent or "critic" in agent:
        return "review"
    return "implement"
