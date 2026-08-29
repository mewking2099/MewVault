"""Livelock detector for instrumented loops (Phase 4).

Two-part check:
  1. Content-hash streak: if content_hash matches any of the last N ticks → no_progress
  2. Graph-cycle prefilter: loop_tick → dispatch → loop_tick cycle in ledger
     (cycle alone is not livelock; cycle + no-progress is — per §A-1)

Result: (is_livelock, no_progress_streak, reason)
"""
from __future__ import annotations

import sqlite3


def check(
    conn: sqlite3.Connection,
    loop_id: str,
    content_hash: str | None,
    max_no_progress: int = 3,
) -> tuple[bool, int, str]:
    """Return (is_livelock, updated_no_progress_streak, reason).

    Updates the streak but does NOT write to the DB — caller writes the tick row.
    """
    ticks = _fetch_recent_ticks(conn, loop_id, n=max_no_progress + 1)

    # Compute no_progress_streak
    if not ticks or content_hash is None:
        streak = 0
    else:
        # Streak = count of consecutive trailing ticks with same content_hash
        streak = 0
        for tick in ticks:  # ordered newest → oldest
            if tick["content_hash"] == content_hash:
                streak += 1
            else:
                break

    if streak >= max_no_progress:
        reason = (
            f"no_progress_streak={streak} ≥ max_no_progress={max_no_progress} "
            f"(content_hash={content_hash!r} repeated)"
        )
        # Check for graph cycle too — if both present, it's definitive livelock
        has_cycle = _detect_graph_cycle(conn, loop_id)
        if has_cycle:
            reason += "; graph cycle detected in loop_tick→dispatch→loop_tick"
        return True, streak, reason

    return False, streak, "ok"


def _fetch_recent_ticks(conn: sqlite3.Connection, loop_id: str, n: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT tick_n, content_hash, no_progress_streak
        FROM loop_tick
        WHERE loop_id = ?
        ORDER BY tick_n DESC
        LIMIT ?
        """,
        (loop_id, n),
    ).fetchall()
    return [{"tick_n": r[0], "content_hash": r[1], "no_progress_streak": r[2]} for r in rows]


def _detect_graph_cycle(conn: sqlite3.Connection, loop_id: str) -> bool:
    """Check if any dispatch spawned by this loop fed back into the same loop.

    Pattern: loop_tick (loop_id=X) → dispatch.parent_dispatch_ts → dispatch
             where that dispatch's dispatch_ts appears as loop_tick.dispatch_ts
             for the same loop_id X.
    """
    try:
        # Dispatches spawned by this loop's ticks
        spawned = conn.execute(
            "SELECT dispatch_ts FROM loop_tick WHERE loop_id = ? AND dispatch_ts IS NOT NULL",
            (loop_id,),
        ).fetchall()
        if not spawned:
            return False

        spawned_ts = {r[0] for r in spawned}

        # Any dispatch with parent_dispatch_ts in the spawned set also appears
        # as a loop_tick.dispatch_ts in this loop → cycle
        for ts in spawned_ts:
            children = conn.execute(
                "SELECT dispatch_ts FROM dispatch WHERE parent_dispatch_ts = ?",
                (ts,),
            ).fetchall()
            for child in children:
                if child[0] in spawned_ts:
                    return True
    except Exception:
        pass
    return False


def escalation_message(loop_id: str, tick_n: int, content_hash: str, streak: int) -> str:
    return (
        f"\n⚠ LIVELOCK DETECTED — loop {loop_id!r} at tick {tick_n}\n"
        f"  no_progress_streak : {streak}\n"
        f"  content_hash       : {content_hash}\n"
        f"  Action required    : review the last {streak} tick outputs and intervene.\n"
        f"  Loop is HALTED.    Use `mew loop status {loop_id}` to inspect.\n"
    )
