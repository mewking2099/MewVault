"""SQLite ledger connection and write helpers (Phases 1-3)."""
from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_FILE = Path(__file__).parent / "schema.sql"
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_DB_NAME = ".mew-ledger.db"

# Code-level schema version — increment when new migrations are added
_CODE_SCHEMA_VERSION = 2


def connect(workspace_root: Path) -> sqlite3.Connection:
    db_path = workspace_root / _DB_NAME
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_FILE.read_text())
    conn.commit()
    _apply_pending_migrations(conn)


def migrate(conn: sqlite3.Connection, description: str = "") -> int:
    """Bump epoch and apply any pending SQL migrations. Returns new epoch."""
    _apply_pending_migrations(conn)
    new_epoch = bump_epoch(conn, description or f"migration to v{_CODE_SCHEMA_VERSION}")
    return new_epoch


def _apply_pending_migrations(conn: sqlite3.Connection) -> None:
    """Apply any .sql migration files not yet reflected in schema_epoch."""
    if not _MIGRATIONS_DIR.exists():
        return
    db_epoch = current_epoch(conn)
    sql_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    for sql_file in sql_files:
        # filename: NNN_description.sql — NNN is the target epoch
        try:
            file_epoch = int(sql_file.stem.split("_")[0])
        except ValueError:
            continue
        if file_epoch <= db_epoch:
            continue  # already applied
        _run_migration_sql(conn, sql_file)
        conn.execute(
            "INSERT OR IGNORE INTO schema_epoch (epoch, applied_at, description) VALUES (?, ?, ?)",
            (file_epoch, _now(), f"auto-migration: {sql_file.name}"),
        )
        conn.commit()


def _run_migration_sql(conn: sqlite3.Connection, sql_file: Path) -> None:
    """Execute a migration SQL file, ignoring duplicate-column errors (idempotent)."""
    raw = sql_file.read_text(encoding="utf-8")
    # Strip comment lines first so multi-line statements aren't skipped by startswith("--")
    clean = "\n".join(
        line for line in raw.splitlines() if not line.strip().startswith("--")
    )
    for statement in clean.split(";"):
        stmt = statement.strip()
        if not stmt:
            continue
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass  # already applied — safe to skip
            else:
                raise


def current_epoch(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(epoch) FROM schema_epoch").fetchone()
    return row[0] if row and row[0] is not None else 1


def bump_epoch(conn: sqlite3.Connection, description: str = "") -> int:
    new_epoch = current_epoch(conn) + 1
    conn.execute(
        "INSERT INTO schema_epoch (epoch, applied_at, description) VALUES (?, ?, ?)",
        (new_epoch, _now(), description),
    )
    conn.commit()
    return new_epoch


def write_dispatch(conn: sqlite3.Connection, **kwargs) -> None:
    try:
        epoch = current_epoch(conn)
        task_hash = _task_hash(
            kwargs.get("agent", ""), kwargs.get("task_text", "")
        )
        ts = kwargs.get("dispatch_ts") or _now()
        conn.execute(
            """
            INSERT OR IGNORE INTO dispatch (
                task_hash, graph_epoch, dispatch_ts,
                agent, model_intended, model_actually_run, provider,
                silo, project_lock, parent_dispatch_ts,
                task_text,
                tokens_in, tokens_out, cost_usd, duration_ms,
                outcome_class, verification_mode, tools_used,
                predicted_agent, predicted_model,
                predicted_radius, actual_radius,
                complexity_score, confidence_bucket,
                routing_rationale, cross_silo_reads
            ) VALUES (
                :task_hash, :graph_epoch, :dispatch_ts,
                :agent, :model_intended, :model_actually_run, :provider,
                :silo, :project_lock, :parent_dispatch_ts,
                :task_text,
                :tokens_in, :tokens_out, :cost_usd, :duration_ms,
                :outcome_class, :verification_mode, :tools_used,
                :predicted_agent, :predicted_model,
                :predicted_radius, :actual_radius,
                :complexity_score, :confidence_bucket,
                :routing_rationale, :cross_silo_reads
            )
            """,
            {
                "task_hash": task_hash,
                "graph_epoch": epoch,
                "dispatch_ts": ts,
                "agent": kwargs.get("agent"),
                "model_intended": kwargs.get("model_intended"),
                "model_actually_run": kwargs.get("model_actually_run"),
                "provider": kwargs.get("provider"),
                "silo": kwargs.get("silo"),
                "project_lock": kwargs.get("project_lock"),
                "parent_dispatch_ts": kwargs.get("parent_dispatch_ts"),
                "task_text": (kwargs.get("task_text") or "")[:500],
                "tokens_in": kwargs.get("tokens_in"),
                "tokens_out": kwargs.get("tokens_out"),
                "cost_usd": kwargs.get("cost_usd"),
                "duration_ms": kwargs.get("duration_ms"),
                "outcome_class": kwargs.get("outcome_class"),
                "verification_mode": kwargs.get("verification_mode"),
                "tools_used": kwargs.get("tools_used"),
                "predicted_agent": kwargs.get("predicted_agent"),
                "predicted_model": kwargs.get("predicted_model"),
                "predicted_radius": kwargs.get("predicted_radius"),
                "actual_radius": kwargs.get("actual_radius"),
                "complexity_score": kwargs.get("complexity_score"),
                "confidence_bucket": kwargs.get("confidence_bucket"),
                "routing_rationale": kwargs.get("routing_rationale"),
                "cross_silo_reads": kwargs.get("cross_silo_reads"),
            },
        )
        conn.commit()
    except Exception:
        pass  # ledger writes are fire-and-forget; never crash the dispatch


def update_actual_radius(conn: sqlite3.Connection, dispatch_ts: str, actual_radius: int) -> None:
    """Set actual_radius post-dispatch once graphify diff is available."""
    try:
        conn.execute(
            "UPDATE dispatch SET actual_radius = ? WHERE dispatch_ts = ?",
            (actual_radius, dispatch_ts),
        )
        conn.commit()
    except Exception:
        pass


def write_loop_tick(conn: sqlite3.Connection, **kwargs) -> None:
    try:
        epoch = current_epoch(conn)
        conn.execute(
            """
            INSERT OR IGNORE INTO loop_tick (
                loop_id, tick_n, graph_epoch,
                loop_type, predicate_state,
                content_hash, embedding_ref, no_progress_streak,
                terminated_reason, tick_ts, dispatch_ts
            ) VALUES (
                :loop_id, :tick_n, :graph_epoch,
                :loop_type, :predicate_state,
                :content_hash, :embedding_ref, :no_progress_streak,
                :terminated_reason, :tick_ts, :dispatch_ts
            )
            """,
            {
                "loop_id": kwargs["loop_id"],
                "tick_n": kwargs["tick_n"],
                "graph_epoch": epoch,
                "loop_type": kwargs.get("loop_type", "unknown"),
                "predicate_state": kwargs.get("predicate_state"),
                "content_hash": kwargs.get("content_hash"),
                "embedding_ref": kwargs.get("embedding_ref"),
                "no_progress_streak": kwargs.get("no_progress_streak", 0),
                "terminated_reason": kwargs.get("terminated_reason"),
                "tick_ts": kwargs.get("tick_ts") or _now(),
                "dispatch_ts": kwargs.get("dispatch_ts"),
            },
        )
        conn.commit()
    except Exception:
        pass


def extract_model_self_report(content: str) -> str | None:
    """Parse [model=...] from the first non-empty line of an agent response."""
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.search(r"\[model=([^\]]+)\]", line)
        return m.group(1) if m else None
    return None


def write_route_prediction(conn: sqlite3.Connection, **kwargs) -> None:
    try:
        epoch = current_epoch(conn)
        ts = kwargs.get("predicted_at") or _now()
        task_hash = _task_hash(kwargs.get("predicted_agent", ""), kwargs.get("task_text", ""))
        conn.execute(
            """
            INSERT OR IGNORE INTO route_prediction (
                task_hash, predicted_at, graph_epoch,
                task_text, predicted_agent, predicted_model, predicted_silo,
                blast_radius_bucket, complexity_bucket
            ) VALUES (
                :task_hash, :predicted_at, :graph_epoch,
                :task_text, :predicted_agent, :predicted_model, :predicted_silo,
                :blast_radius_bucket, :complexity_bucket
            )
            """,
            {
                "task_hash": task_hash,
                "predicted_at": ts,
                "graph_epoch": epoch,
                "task_text": (kwargs.get("task_text") or "")[:500],
                "predicted_agent": kwargs.get("predicted_agent"),
                "predicted_model": kwargs.get("predicted_model"),
                "predicted_silo": kwargs.get("predicted_silo"),
                "blast_radius_bucket": kwargs.get("blast_radius_bucket"),
                "complexity_bucket": kwargs.get("complexity_bucket"),
            },
        )
        conn.commit()
        return task_hash
    except Exception:
        return None


def get_last_prediction(conn: sqlite3.Connection, task_hash: str) -> dict | None:
    row = conn.execute(
        """
        SELECT task_hash, predicted_at, predicted_agent, predicted_model,
               predicted_silo, blast_radius_bucket, complexity_bucket
        FROM route_prediction
        WHERE task_hash = ? AND actual_dispatch_ts IS NULL
        ORDER BY predicted_at DESC LIMIT 1
        """,
        (task_hash,),
    ).fetchone()
    if not row:
        return None
    cols = ["task_hash", "predicted_at", "predicted_agent", "predicted_model",
            "predicted_silo", "blast_radius_bucket", "complexity_bucket"]
    return dict(zip(cols, row))


def reconcile_prediction(conn: sqlite3.Connection, task_hash: str,
                         dispatch_ts: str, actual_agent: str,
                         actual_model: str | None) -> None:
    try:
        pred = get_last_prediction(conn, task_hash)
        if not pred:
            return
        agent_diverged = int(pred["predicted_agent"] != actual_agent)
        model_diverged  = int((pred["predicted_model"] or "") != (actual_model or ""))
        conn.execute(
            """
            UPDATE route_prediction
            SET actual_dispatch_ts = ?,
                actual_agent       = ?,
                actual_model       = ?,
                agent_diverged     = ?,
                model_diverged     = ?
            WHERE task_hash = ? AND predicted_at = ?
            """,
            (dispatch_ts, actual_agent, actual_model,
             agent_diverged, model_diverged,
             pred["task_hash"], pred["predicted_at"]),
        )
        conn.commit()
    except Exception:
        pass


# ── helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _task_hash(agent: str, task_text: str) -> str:
    raw = f"{agent}:{task_text[:500]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
