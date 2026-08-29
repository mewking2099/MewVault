"""mew loop — instrumented loop primitives (Phase 4).

Sub-commands:
  start <loop_type> --task TEXT [--context KEY=VALUE ...]
      Open a new loop. Writes tick 0. Prints loop_id.
  tick <loop_id> --output TEXT | --output-file PATH [--dispatch-ts TEXT]
      Record next tick. Checks predicate + livelock. Prints status.
  status [<loop_id>]
      Show tick history and current state.
  list
      Show all active (non-terminated) loops.

Loop types (fixed — Phase 4 ships only these four):
  spec_build_verify | plan_approve_execute | idea_lifecycle | wrap_prime
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mew.workspace import find_workspace_root
from mew.ledger import db as ledger_db
from mew.loops import predicates, livelock, caps as caps_mod
from mew.commands.dispatch import _read_active_project


def run_loop(args) -> None:
    workspace_root = find_workspace_root()
    action = getattr(args, "loop_action", None)

    if action == "start":
        _start(args, workspace_root)
    elif action == "tick":
        _tick(args, workspace_root)
    elif action == "status":
        _status(args, workspace_root)
    elif action == "list":
        _list(workspace_root)
    else:
        print("mew loop: sub-commands: start | tick | status | list", file=sys.stderr)
        sys.exit(1)


# ── start ─────────────────────────────────────────────────────────────────────

def _start(args, workspace_root: Path) -> None:
    loop_type = args.loop_type
    if loop_type not in predicates.LOOP_TYPES:
        print(
            f"loop start: unknown loop_type '{loop_type}'. "
            f"Valid: {', '.join(sorted(predicates.LOOP_TYPES))}",
            file=sys.stderr,
        )
        sys.exit(1)

    task = (getattr(args, "task", None) or "").strip()
    ctx_overrides = _parse_ctx(getattr(args, "ctx", []) or [])

    loop_id = str(uuid.uuid4())
    ctx = _default_ctx(loop_type, workspace_root, ctx_overrides)
    is_met, reason, state = predicates.evaluate(loop_type, ctx)

    caps = caps_mod.load()
    max_t = caps_mod.max_ticks(loop_type, caps)

    conn = ledger_db.connect(workspace_root)
    ledger_db.init(conn)

    ledger_db.write_loop_tick(
        conn,
        loop_id=loop_id,
        tick_n=0,
        loop_type=loop_type,
        predicate_state=json.dumps(state),
        content_hash=None,
        no_progress_streak=0,
        terminated_reason="predicate_met" if is_met else None,
        tick_ts=_now(),
    )

    print(f"loop started")
    print(f"  loop_id    : {loop_id}")
    print(f"  loop_type  : {loop_type}")
    print(f"  max_ticks  : {max_t}  (max_no_progress={caps_mod.max_no_progress(caps)})")
    print(f"  tick 0     : predicate={'MET' if is_met else 'not met'} — {reason}")
    if is_met:
        print(f"  (predicate already met at tick 0 — loop complete)")
    else:
        print(f"  Run tick 1: mew loop tick {loop_id} --output '<output text>'")


# ── tick ──────────────────────────────────────────────────────────────────────

def _tick(args, workspace_root: Path) -> None:
    loop_id = args.loop_id

    conn = ledger_db.connect(workspace_root)
    ledger_db.init(conn)

    # Check loop exists and is not already terminated
    last_tick = conn.execute(
        "SELECT tick_n, terminated_reason, loop_type FROM loop_tick "
        "WHERE loop_id = ? ORDER BY tick_n DESC LIMIT 1",
        (loop_id,),
    ).fetchone()

    if not last_tick:
        print(f"loop tick: loop_id {loop_id!r} not found — use `mew loop start` first", file=sys.stderr)
        sys.exit(1)

    tick_n, prev_terminated, loop_type = last_tick
    if prev_terminated:
        print(f"loop tick: loop {loop_id!r} already terminated ({prev_terminated})", file=sys.stderr)
        sys.exit(1)

    next_tick_n = tick_n + 1

    # Caps check
    caps = caps_mod.load()
    max_t = caps_mod.max_ticks(loop_type, caps)
    if next_tick_n >= max_t:
        terminated_reason = "max_ticks"
        _write_tick_and_report(
            conn, loop_id, next_tick_n, loop_type,
            content_hash=None, streak=0,
            predicate_state={}, terminated_reason=terminated_reason,
            dispatch_ts=getattr(args, "dispatch_ts", None),
        )
        print(f"loop tick {next_tick_n}: TERMINATED — max_ticks={max_t} reached")
        print(f"  Hint: increase cap in ~/.mew/loop-caps.yaml if more ticks are needed.")
        return

    # Output content hash
    output = _read_output(args)
    content_hash = _hash(output) if output else None

    # Livelock check
    max_np = caps_mod.max_no_progress(caps)
    is_livelock, streak, ll_reason = livelock.check(
        conn, loop_id, content_hash, max_no_progress=max_np
    )

    if is_livelock:
        terminated_reason = "no_progress_cap"
        _write_tick_and_report(
            conn, loop_id, next_tick_n, loop_type,
            content_hash=content_hash, streak=streak,
            predicate_state={}, terminated_reason=terminated_reason,
            dispatch_ts=getattr(args, "dispatch_ts", None),
        )
        print(livelock.escalation_message(loop_id, next_tick_n, content_hash or "", streak))
        return

    # Predicate check
    ctx_overrides = _parse_ctx(getattr(args, "ctx", []) or [])
    ctx = _default_ctx(loop_type, workspace_root, ctx_overrides)
    is_met, reason, state = predicates.evaluate(loop_type, ctx)

    terminated_reason = "predicate_met" if is_met else None
    dispatch_ts = getattr(args, "dispatch_ts", None)

    _write_tick_and_report(
        conn, loop_id, next_tick_n, loop_type,
        content_hash=content_hash, streak=streak,
        predicate_state=state, terminated_reason=terminated_reason,
        dispatch_ts=dispatch_ts,
    )

    if is_met:
        print(f"loop tick {next_tick_n}: TERMINATED — predicate_met")
        print(f"  {reason}")
        # Wrap_prime: inject provenance brief
        if loop_type == "wrap_prime":
            _inject_provenance_brief(ctx, loop_id, next_tick_n, workspace_root)
    else:
        print(f"loop tick {next_tick_n}: ongoing — {reason}")
        print(f"  content_hash={content_hash}  no_progress_streak={streak}")
        print(f"  Next: mew loop tick {loop_id} --output '<output>'")

    # Deferred-if-locked hint (§Phase 4 concurrency)
    if getattr(args, "defer_if_locked", False):
        lock = _read_active_project(workspace_root)
        if lock:
            print(f"  (tick deferred — project lock active: {lock}; logged)")


# ── status ────────────────────────────────────────────────────────────────────

def _status(args, workspace_root: Path) -> None:
    loop_id = getattr(args, "loop_id", None)
    conn = ledger_db.connect(workspace_root)
    ledger_db.init(conn)

    if loop_id:
        ticks = conn.execute(
            "SELECT tick_n, loop_type, content_hash, no_progress_streak, "
            "terminated_reason, tick_ts, predicate_state "
            "FROM loop_tick WHERE loop_id = ? ORDER BY tick_n",
            (loop_id,),
        ).fetchall()
        if not ticks:
            print(f"loop status: {loop_id!r} not found")
            return
        print(f"loop {loop_id}")
        for row in ticks:
            tick_n, ltype, chash, streak, term, ts, pstate = row
            status = f"TERMINATED({term})" if term else "ongoing"
            print(f"  tick {tick_n:>3}  {status:<30}  hash={chash or 'n/a'}  streak={streak or 0}")
        if ticks[-1][4]:
            print(f"  final state: {ticks[-1][6] or '{}'}")
    else:
        _list(workspace_root, conn=conn)


# ── list ──────────────────────────────────────────────────────────────────────

def _list(workspace_root: Path, conn=None) -> None:
    if conn is None:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)

    rows = conn.execute(
        """
        SELECT loop_id, loop_type,
               MAX(tick_n) as last_tick,
               MAX(CASE WHEN terminated_reason IS NOT NULL THEN terminated_reason END) as term,
               MAX(tick_ts) as last_ts
        FROM loop_tick
        GROUP BY loop_id
        ORDER BY last_ts DESC
        LIMIT 30
        """
    ).fetchall()

    if not rows:
        print("no loops recorded yet")
        return

    print(f"{'loop_id':<38} {'type':<22} {'ticks':>5} {'status':<20} {'last_ts'}")
    print("-" * 110)
    for loop_id, ltype, last_tick, term, last_ts in rows:
        status = f"TERMINATED({term})" if term else "ongoing"
        print(f"{loop_id:<38} {(ltype or '?'):<22} {last_tick:>5}  {status:<20} {last_ts or ''}")


# ── wrap_prime provenance brief injection ─────────────────────────────────────

def _inject_provenance_brief(ctx: dict, loop_id: str, tick_n: int,
                              workspace_root: Path) -> None:
    brief_path = ctx.get("brief_file")
    if not brief_path:
        return
    brief = Path(brief_path)
    if not brief.exists():
        return
    provenance_header = (
        f"<!-- provenance: loop_id={loop_id}, tick={tick_n}, "
        f"generated={_now()}, "
        f"advisory=true, "
        f"note=contradiction-check against MASTER_SPEC required before use -->\n"
    )
    original = brief.read_text(encoding="utf-8")
    if "<!-- provenance:" not in original:
        brief.write_text(provenance_header + original, encoding="utf-8")
        print(f"  provenance injected into {brief}")


# ── helpers ───────────────────────────────────────────────────────────────────

def _write_tick_and_report(conn, loop_id, tick_n, loop_type,
                            content_hash, streak, predicate_state,
                            terminated_reason, dispatch_ts):
    ledger_db.write_loop_tick(
        conn,
        loop_id=loop_id,
        tick_n=tick_n,
        loop_type=loop_type,
        predicate_state=json.dumps(predicate_state) if predicate_state else None,
        content_hash=content_hash,
        no_progress_streak=streak,
        terminated_reason=terminated_reason,
        tick_ts=_now(),
        dispatch_ts=dispatch_ts,
    )


def _default_ctx(loop_type: str, workspace_root: Path, overrides: dict) -> dict:
    """Build a default context dict for the given loop type from the workspace."""
    ctx: dict = {}
    project_lock = _read_active_project(workspace_root)
    project_root = Path(project_lock) if project_lock else workspace_root

    if loop_type == "spec_build_verify":
        ctx.setdefault("spec_file", project_root / "proposals" / "spec.md")
        ctx.setdefault("tests_pass_marker", project_root / ".tests-pass")

    elif loop_type == "plan_approve_execute":
        ctx.setdefault("project_status_file", project_root / "Project_Status.md")
        ctx.setdefault("plan_file", project_root / "proposals" / "active" / "plan.md")

    elif loop_type == "idea_lifecycle":
        # Expect overrides to supply idea_status_file
        ctx.setdefault("idea_status_file", None)

    elif loop_type == "wrap_prime":
        ctx.setdefault("log_file", project_root / "log.md")
        ctx.setdefault("brief_file", workspace_root / "mewvault" / "wiki" / "_next-session-brief.md")
        ctx.setdefault("session_start_ts", time.time() - 7200)  # 2h ago as fallback

    ctx.update(overrides)
    return ctx


def _parse_ctx(pairs: list[str]) -> dict:
    """Parse KEY=VALUE pairs from --ctx arguments."""
    result = {}
    for pair in pairs:
        if "=" in pair:
            k, v = pair.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def _read_output(args) -> str | None:
    output_file = getattr(args, "output_file", None)
    output_text = getattr(args, "output", None)
    if output_file:
        p = Path(output_file)
        return p.read_text(encoding="utf-8") if p.exists() else None
    return output_text


def _hash(text: str) -> str:
    return hashlib.sha256(text[:4096].encode("utf-8")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
