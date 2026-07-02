# Plan: Persistent Memory Layer (phase-3-memory)

**Tier:** MewKing  
**Status:** COMPLETE — approved 2026-07-02, all phases implemented  
**Author:** Claude / mew-chief  
**Date:** 2026-05-26  

---

## Problem

MewVault's current memory system is flat `.md` files in `.claude/projects/memory/`. Claude reads them at session start but cannot:
- Search across them semantically or by keyword
- Filter by silo, project, or recency
- Auto-inject relevant context based on what's active right now
- Index the living content of the workspace (log.md, wiki pages, idea summaries)

Hermes Agent solves this with SQLite FTS5 + a Honcho user profile layer. We implement a MewVault-native equivalent.

---

## Scope

**In scope:**
- `mew memory sync` — index workspace content (logs, wiki, ideas) into SQLite
- `mew memory search <query>` — FTS search across indexed content
- `mew memory recall [--silo <name>] [--days <n>]` — recent context for a silo
- `mew memory purge [--before <date>]` — remove stale entries (default: >90 days)
- `session-start.js` update — auto-recall top entries for active silo at session start

**Out of scope (future):**
- Honcho user profiling (tracks personality/work style across sessions)
- Semantic/vector search (would require embedding model)
- Cross-machine sync (local SQLite only)

---

## Files to create / modify

| File | Action | Description |
|------|--------|-------------|
| `mew/memory_store.py` | Create | SQLite adapter — schema, CRUD, FTS search |
| `mew/commands/memory.py` | Create | CLI command: sync, search, recall, purge |
| `hooks/session-start.js` | Modify | Add `mew memory recall --silo <active>` injection |
| `mew.py` (or `mew/cli.py`) | Modify | Register `memory` subcommand |
| `CLAUDE.md` | Modify | Document new `mew/memory_store.py` in structure section |

---

## Schema

```sql
-- mewvault/.mew-memory.db  (gitignored)
CREATE TABLE entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,   -- 'log', 'wiki', 'idea', 'note'
    silo        TEXT NOT NULL,   -- 'mewvault' | 'idea-hub' | 'wiki' | 'design-studio' | 'software-projects' | 'game-lab' | 'global'
    project     TEXT,            -- project name within silo, nullable
    source_path TEXT,            -- relative path from silo root
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    tags        TEXT,            -- comma-separated
    created_at  TEXT NOT NULL,   -- ISO 8601
    updated_at  TEXT NOT NULL
);
CREATE VIRTUAL TABLE entries_fts USING fts5(
    title, body,
    content='entries',
    content_rowid='id'
);
-- Triggers to keep FTS in sync
CREATE TRIGGER entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, body) VALUES ('delete', old.id, old.title, old.body);
END;
CREATE TRIGGER entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, body) VALUES ('delete', old.id, old.title, old.body);
    INSERT INTO entries_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
```

DB file: `mewvault/.mew-memory.db` (add to `.gitignore`)

---

## Command API

```bash
# Index all workspace content (run at session start or on demand)
mew memory sync                    # all silos
mew memory sync --silo idea-hub    # one silo only

# Search across everything
mew memory search "feasibility market size"
mew memory search "Yaana design tokens" --silo design-studio

# Recent context for a silo (used by session-start.js)
mew memory recall --silo software-projects --days 7

# Prune stale entries
mew memory purge --before 2026-02-01
mew memory purge --days 90          # everything older than 90 days
```

---

## What `sync` indexes

| Source | Type | Silo |
|--------|------|------|
| `<silo>/*/log.md` | log | per silo |
| `<silo>/*/wiki/*.md` | wiki | per silo |
| `idea-hub/ideas/*/idea.md` | idea | idea-hub |
| `idea-hub/ideas/*/feasibility.md` | idea | idea-hub |
| `<silo>/*/proposals/active/*/plan.md` | note | per silo |

**Never indexed:** `raw/`, `secrets/`, `research/` (immutable directories), `.obsidian/`, `export/`

---

## session-start.js changes

After the existing context assembly (rules → persona → dispatcher → project status → instincts), add:

```javascript
// Inject relevant memory recall
const silo = detectActiveSilo(cwd);  // derived from working directory
const recall = execSync(`python mew.py memory recall --silo ${silo} --days 14 --limit 5`).toString();
if (recall.trim()) {
  systemPrompt += `\n\n## Recent context (${silo})\n${recall}`;
}
```

Keep the injected recall under ~800 tokens. If `mew.py` is not found or errors — fail silently.

---

## Platform compatibility

- SQLite with FTS5: bundled in Python 3.11+ on macOS and Windows ✓
- `pathlib.Path` for all file ops ✓
- No new pip dependencies (stdlib only)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| DB file grows unbounded | `purge` command + 90-day default retention |
| session-start.js already complex | Recall is a single shell call, fail-silent |
| FTS5 not available (rare) | Graceful fallback to LIKE search |
| Indexing raw/ or secrets/ by mistake | Explicit path blocklist in `sync` |
| Windows path separators | `pathlib.Path` throughout |

---

## Acceptance tests

- [ ] `mew memory sync` runs without errors on a fresh workspace
- [ ] `mew memory search "some query"` returns relevant results
- [ ] `mew memory recall --silo idea-hub` returns entries sorted by recency
- [ ] `mew memory purge --days 90` removes old entries, keeps recent ones
- [ ] `raw/`, `secrets/`, `research/` files are never indexed
- [ ] session-start.js injects recall without crashing when DB is empty
- [ ] DB file is gitignored

---

## Implementation order

1. `mew/memory_store.py` — schema + CRUD + FTS + purge
2. `mew/commands/memory.py` — CLI wrapper
3. Register in `mew.py`
4. `.gitignore` update
5. `session-start.js` injection
6. `CLAUDE.md` documentation update
