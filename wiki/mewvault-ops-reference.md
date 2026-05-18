# MewVault Ops Reference

> Quick reference for running MewVault day-to-day. See also: [[mewvault-how-it-works]].

---

## Every Session

```
# At session END — always
/wrap
```

The Stop hook auto-writes a thin `log.md` entry. `/wrap` is the real one with context.

---

## What Fires Automatically

| Hook | Triggers on | What it does |
|------|-------------|--------------|
| `session-start.js` | Every prompt | Vault rules + agent routing + active instincts injected |
| `pre-tool-use.js` | Before Bash/Write/Edit | Secrets block, MewKing gate, token budget warning/block |
| `post-tool-use.js` | After Write/Edit | Rapid-rewrite detection → pending instinct written |
| `session-end.js` | Session end (Stop) | Auto-wrap log entry, wiki sync, session.tmp, commit hint |
| `pre-compact.js` | Before compaction | Context snapshot written |
| doobidoo MCP | Claude Code launch | Semantic search server starts (via `.mcp.json`) |
| Ollama | Mac login | Runs as launchd service — always up, no action needed |

---

## Manual Tasks

### Re-index doobidoo after significant file changes

```bash
# Code changes (software-projects/, game-lab/)
python /Users/Mohabbat/Jan/mewvault/scripts/ingest_code.py

# Wiki note changes
python /Users/Mohabbat/Jan/mewvault/scripts/ingest_wiki.py
```

Not needed every session — only when you've made edits you want to be semantically searchable.

### Instinct pipeline

```bash
# See what the system learned from your corrections
mew instinct status

# Promote one so it fires in future sessions
mew instinct promote <id>

# Clean up old low-confidence ones (>14 days, conf < 0.8)
mew instinct prune
```

Instincts are captured automatically when you rewrite a file quickly (within 60 seconds of the first write). They sit in `instincts/pending/` until you promote them — then they appear under `## Active Vault Instincts` at every session start.

---

## Ollama Check

Ollama runs as a Homebrew launchd service — starts at login, stays running.

```bash
brew services list | grep ollama   # should show: started
ollama list                         # confirm nomic-embed-text is present
```

doobidoo embeddings fail silently if Ollama is down. If something feels off with semantic search, check this first.

---

## MewKing Gate (when plan_approved matters)

If a project's `Project_Status.md` has `tier: MewKing`, Claude cannot write code until `plan_approved: true`. The PreToolUse hook enforces this at OS level (exit code 2).

To unblock after plan review: edit `Project_Status.md` and set `plan_approved: true`.

---

## Key File Locations

| File | Purpose |
|------|---------|
| `/Jan/.mcp.json` | Authoritative MCP server config (memory + doobidoo) |
| `mewvault/.claude/settings.local.json` | Hook wiring + enabled MCP servers |
| `mewvault/instincts/pending/` | Captured but unreviewed instincts |
| `mewvault/instincts/promoted/` | Active instincts (injected into session-start) |
| `~/.mewvault/chroma-wiki/memory.db` | doobidoo SQLite-vec database |
| `/Jan/.claude/last-session-message.txt` | Auto-generated commit message hint |
