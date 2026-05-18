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

| Hook | Event | Triggers on | What it does |
|------|-------|-------------|--------------|
| `session-start.js` | `UserPromptSubmit` | Every user prompt | Vault rules + agent routing + active instincts injected into context |
| `pre-tool-use.js` | `PreToolUse` | Before Bash/Write/Edit/MultiEdit | Secrets block, raw/ guard, MewKing gate, .obsidian guard |
| `post-tool-use.js` | `PostToolUse` | After Write/Edit/MultiEdit | Rapid-rewrite detection → pending instinct written; session activity accumulated |
| `session-end.js` | `Stop` | Session end | Auto-wrap log entry, wiki sync, writes `last-session-message.txt` commit hint |
| `pre-compact.js` | `PreCompact` | Before compaction | Context snapshot written to `.claude/context-snapshots/` |

MCP servers start automatically when Claude Code launches (via `.mcp.json` at `~/.claude/mcp.json` or `/Jan/.mcp.json`):
- **memory** — `@modelcontextprotocol/server-memory` (in-session knowledge graph)
- **doobidoo** — SQLite-vec semantic search over wiki + code (backed by Ollama `nomic-embed-text`)

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

**Current instinct count:** ~8 pending, 3 promoted.

### mew CLI — full command list

```bash
mew init              # Bootstrap the workspace (silos, CLAUDE.md files, git repos)
mew status            # Show project status across all silos
mew new               # Scaffold a new project or learning path
mew validate          # Check all Project_Status.md files for schema compliance
mew secret            # Manage secrets (get, set, list, rotate)
mew dump              # Token-budgeted project context snapshot
mew promote           # Promote projects across silos (UX→Code, wiki→UX, experiment→game)
mew abandon           # Mark a project as abandoned
mew rename            # Rename a project folder and update its Project_Status.md
mew rebuild-status    # Regenerate a missing or corrupted Project_Status.md
mew archive           # Move a project to _archive/ with per-silo behavior
mew package           # Assemble a client deliverable package from a UX project
mew process-inbox     # List wiki/_inbox/ and propose routing for each file
mew sync              # Git status across all repos, with optional commit or PR
mew harness           # Install and manage the MewHarness hook runtime
mew agent             # List or invoke specialist agents
mew instinct          # Manage the instinct pipeline (promote, prune, export)
mew compact           # Generate a semantic context map for pre-compaction snapshots
mew help              # Show help or detail for a specific command
```

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

If a project's `Project_Status.md` has `tier: MewKing`, Claude cannot write code until `plan_approved: true`. The `pre-tool-use.js` hook enforces this at OS level (exit code 2).

To unblock after plan review: edit `Project_Status.md` and set `plan_approved: true`.

---

## Skills

25 bundled skills are available globally, symlinked under `~/.claude/skills/` from `mewvault/skills/`. They are available in all silos without path qualification.

Key skills for day-to-day work:

| Skill | Use for |
|-------|---------|
| `systematic-debugging` | Multi-step bug investigation |
| `tdd-workflow` | Test-first feature development |
| `executing-plans` | Running an approved MewKing plan |
| `plan-orchestrate` | Planning + dispatching parallel agents |
| `frontend-design` | Component + UI implementation |
| `shadcn-ui` | shadcn/ui component work |
| `code-reviewer` | Code review pass |
| `github-ops` | PR creation, review, merge |

---

## Key File Locations

| File / Directory | Purpose |
|-----------------|---------|
| `/Jan/.mcp.json` | Authoritative MCP server config (memory + doobidoo) |
| `mewvault/.claude/settings.local.json` | Hook wiring + enabled MCP servers + allow-list |
| `/Jan/.claude/rules/mew-common/` | Global rules (vault-rules, tier-gates, secrets) |
| `/Jan/.claude/rules/mew-code/` | Code silo rules |
| `/Jan/.claude/rules/mew-design/` | Design silo rules |
| `/Jan/.claude/rules/mew-game/` | Game silo rules |
| `mewvault/hooks/` | 5 Node.js hook scripts |
| `mewvault/skills/` | 25 bundled skill files |
| `mewvault/instincts/pending/` | Captured but unreviewed instincts |
| `mewvault/instincts/promoted/` | Active instincts (injected at session-start) |
| `mewvault/.claude/context-snapshots/` | Pre-compaction context dumps |
| `~/.mewvault/chroma-wiki/memory.db` | doobidoo SQLite-vec database |
| `/Jan/.claude/last-session-message.txt` | Auto-generated commit message hint |
