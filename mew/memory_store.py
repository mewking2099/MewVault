"""SQLite FTS5 memory store for MewVault cross-session context."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_NAME = ".mew-memory.db"

_TABLES = """
CREATE TABLE IF NOT EXISTS entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,
    silo        TEXT NOT NULL,
    project     TEXT,
    source_path TEXT UNIQUE,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    tags        TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    title, body,
    content='entries',
    content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, body)
    VALUES ('delete', old.id, old.title, old.body);
END;
CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, body)
    VALUES ('delete', old.id, old.title, old.body);
    INSERT INTO entries_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
"""


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._fts = self._setup()

    def _setup(self) -> bool:
        cur = self._conn.cursor()
        cur.executescript(_TABLES)
        try:
            cur.executescript(_FTS)
            self._conn.commit()
            return True
        except sqlite3.OperationalError:
            self._conn.commit()
            return False  # FTS5 not available, fall back to LIKE

    def upsert(
        self, *, type: str, silo: str, project: str | None,
        source_path: str, title: str, body: str, tags: str = "",
    ) -> None:
        now = datetime.utcnow().isoformat()
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT id FROM entries WHERE source_path = ?", (source_path,)
        ).fetchone()
        if row:
            cur.execute(
                "UPDATE entries SET title=?, body=?, tags=?, updated_at=? WHERE id=?",
                (title, body, tags, now, row["id"]),
            )
        else:
            cur.execute(
                "INSERT INTO entries "
                "(type, silo, project, source_path, title, body, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (type, silo, project, source_path, title, body, tags, now, now),
            )
        self._conn.commit()

    def search(self, query: str, silo: str | None = None, limit: int = 10) -> list[dict]:
        cur = self._conn.cursor()
        if self._fts:
            base = (
                "SELECT e.type, e.silo, e.project, e.title, "
                "snippet(entries_fts, 1, '[', ']', '…', 20) AS snippet, e.updated_at "
                "FROM entries_fts JOIN entries e ON entries_fts.rowid = e.id "
                "WHERE entries_fts MATCH ?"
            )
            params: list = [query]
            if silo:
                base += " AND e.silo = ?"
                params.append(silo)
            base += " ORDER BY rank LIMIT ?"
            params.append(limit)
        else:
            like = f"%{query}%"
            base = (
                "SELECT type, silo, project, title, "
                "substr(body, 1, 200) AS snippet, updated_at FROM entries "
                "WHERE (title LIKE ? OR body LIKE ?)"
            )
            params = [like, like]
            if silo:
                base += " AND silo = ?"
                params.append(silo)
            base += " LIMIT ?"
            params.append(limit)
        return [dict(r) for r in cur.execute(base, params).fetchall()]

    def recall(self, silo: str | None = None, days: int = 14, limit: int = 5) -> list[dict]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cur = self._conn.cursor()
        if silo:
            rows = cur.execute(
                "SELECT type, silo, project, title, body, updated_at FROM entries "
                "WHERE silo = ? AND updated_at >= ? ORDER BY updated_at DESC LIMIT ?",
                (silo, cutoff, limit),
            ).fetchall()
        else:
            rows = cur.execute(
                "SELECT type, silo, project, title, body, updated_at FROM entries "
                "WHERE updated_at >= ? ORDER BY updated_at DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def purge(self, cutoff: str) -> int:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM entries WHERE updated_at < ?", (cutoff,))
        deleted = cur.rowcount
        if deleted and self._fts:
            cur.execute("INSERT INTO entries_fts(entries_fts) VALUES ('rebuild')")
        self._conn.commit()
        return deleted

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

    def close(self) -> None:
        self._conn.close()


def find_db(workspace_root: Path) -> Path:
    return workspace_root / "mewvault" / DB_NAME
