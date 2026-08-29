"""mew ledger — query and inspect the dispatch ledger."""
from __future__ import annotations

import json
from pathlib import Path

from mew.ledger import db as ledger_db
from mew.workspace import find_workspace_root


def run_ledger(args) -> None:
    action = getattr(args, "ledger_action", "tail")
    root = find_workspace_root()
    conn = ledger_db.connect(root)
    ledger_db.init(conn)

    if action == "migrate":
        _migrate(conn)
    elif action == "tail":
        _tail(conn, getattr(args, "n", 20))
    elif action == "show":
        _show(conn, args.dispatch_ts)
    elif action == "stats":
        _stats(conn)
    elif action == "update-radius":
        ledger_db.update_actual_radius(conn, args.dispatch_ts, args.count)
        print(f"ledger: set actual_radius={args.count} for dispatch_ts={args.dispatch_ts}")
    else:
        print(f"Unknown ledger action: {action}")


# ── actions ───────────────────────────────────────────────────────────────────

def _migrate(conn) -> None:
    epoch = ledger_db.current_epoch(conn)
    new_epoch = ledger_db.bump_epoch(conn, description="manual migration")
    print(f"ledger: epoch {epoch} → {new_epoch}")


def _tail(conn, n: int) -> None:
    rows = conn.execute(
        """
        SELECT dispatch_ts, agent, model_actually_run, outcome_class,
               tokens_in, tokens_out, substr(task_text, 1, 60)
        FROM dispatch
        ORDER BY dispatch_ts DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()

    if not rows:
        print("ledger: no dispatch rows yet")
        return

    header = f"{'ts':28} {'agent':25} {'model':28} {'outcome':10} {'in':>6} {'out':>6}  task"
    print(header)
    print("-" * len(header))
    for ts, agent, model, outcome, tin, tout, task in rows:
        agent = (agent or "?")[:25]
        model = (model or "?")[:28]
        outcome = (outcome or "?")[:10]
        tin = str(tin or "")
        tout = str(tout or "")
        task = (task or "").replace("\n", " ")
        print(f"{ts:28} {agent:25} {model:28} {outcome:10} {tin:>6} {tout:>6}  {task}")


def _show(conn, dispatch_ts: str) -> None:
    row = conn.execute(
        "SELECT * FROM dispatch WHERE dispatch_ts = ?", (dispatch_ts,)
    ).fetchone()
    if not row:
        print(f"ledger: no row found for ts={dispatch_ts}")
        return
    cols = [d[0] for d in conn.execute("SELECT * FROM dispatch LIMIT 0").description]
    for col, val in zip(cols, row):
        print(f"  {col:<25} {val}")


def _stats(conn) -> None:
    epoch = ledger_db.current_epoch(conn)
    total = conn.execute("SELECT COUNT(*) FROM dispatch").fetchone()[0]
    by_agent = conn.execute(
        "SELECT agent, COUNT(*) FROM dispatch GROUP BY agent ORDER BY COUNT(*) DESC"
    ).fetchall()
    by_outcome = conn.execute(
        "SELECT outcome_class, COUNT(*) FROM dispatch GROUP BY outcome_class"
    ).fetchall()
    ticks = conn.execute("SELECT COUNT(*) FROM loop_tick").fetchone()[0]

    print(f"ledger stats  (epoch {epoch})")
    print(f"  dispatches   : {total}")
    print(f"  loop ticks   : {ticks}")
    print()
    print("  by agent:")
    for agent, cnt in by_agent:
        print(f"    {(agent or '?'):<30} {cnt}")
    print()
    print("  by outcome:")
    for outcome, cnt in by_outcome:
        print(f"    {(outcome or 'unknown'):<20} {cnt}")
