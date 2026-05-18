# MewVault — How It Works

> Architecture reference for the federated MewVault workspace. See also: [[mewvault-ops-reference]].

---

## Workspace Layout

MewVault is a mono-root with five independent git silos:

```
/Jan/
├── .claude/
│   ├── rules/
│   │   ├── mew-common/     # vault-rules, tier-gates, secrets (all silos)
│   │   ├── mew-code/       # code-rules (software-projects/ only)
│   │   ├── mew-design/     # design-rules (design-studio/ only)
│   │   └── mew-game/       # godot-rules (game-lab/ only)
│   └── last-session-message.txt
├── .mcp.json               # MCP server definitions (memory + doobidoo)
├── wiki/                   # Obsidian knowledge base (git repo)
├── design-studio/          # Figma + UX projects (git repo)
├── software-projects/      # Code projects (git repo)
│   └── dsaas/              # AI-native Design System as a Service
├── game-lab/               # Godot games + experiments (git repo)
└── mewvault/               # CLI engine + hook runtime (this repo)
    ├── mew.py              # CLI entry point
    ├── mew/commands/       # One file per mew command (20 commands)
    ├── hooks/              # 5 Node.js hook scripts
    ├── skills/             # 25 bundled skill files
    ├── instincts/
    │   ├── pending/        # Rapid-rewrite captures, unreviewed
    │   └── promoted/       # Active instincts, injected at session-start
    ├── templates/          # Scaffolding templates ({{placeholder}} syntax)
    ├── secrets/            # Gitignored, chmod 0600
    └── .claude/
        └── settings.local.json   # Hook wiring + allow-list
```

---

## Session Lifecycle

Every Claude Code session follows this flow:

```
User types prompt
      ↓
UserPromptSubmit → session-start.js
  - Detects workspace root + silo (wiki/code/design/game)
  - Loads mew-common rules + silo-specific rules
  - Loads Project_Status.md fields (whitelisted per silo)
  - Injects promoted instincts
  - Injects agent identity (mew-coder, mew-designer, etc.)
  - All injected as additionalContext (invisible to user)
      ↓
Claude responds, calls tools
      ↓
PreToolUse → pre-tool-use.js (on Bash/Write/Edit/MultiEdit)
  - Blocks writes to raw/ (immutable sources)
  - Blocks writes to .obsidian/
  - Scans content for secret patterns (sk-, ghp_, AKIA, etc.)
  - MewKing gate: blocks code writes if tier=MewKing and plan_approved≠true
      ↓
PostToolUse → post-tool-use.js (on Write/Edit/MultiEdit)
  - Accumulates session activity (files modified, tool calls)
  - Rapid-rewrite detection: if same file written twice in <60s → writes pending instinct
      ↓
Session ends (/wrap, /exit, or window close)
      ↓
Stop → session-end.js
  - Prepends thin log entry to project log.md
  - Writes last-session-message.txt (commit message hint)
  - Clears session-activity.json
      ↓
PreCompact → pre-compact.js (if compaction triggered)
  - Writes context snapshot to .claude/context-snapshots/<silo>-<hash>-<ts>.md
```

---

## Hook Architecture

All hooks are Node.js scripts in `mewvault/hooks/`. They read context from stdin (Claude Code's hook JSON protocol) and optionally output `additionalContext` JSON to inject text back into the model context.

| Script | Event | Timeout | Blocking |
|--------|-------|---------|----------|
| `session-start.js` | UserPromptSubmit | 15s | No (injects context) |
| `pre-tool-use.js` | PreToolUse | 5s | Yes (exit 2 blocks the tool call) |
| `post-tool-use.js` | PostToolUse | 10s | No (side-effects only) |
| `session-end.js` | Stop | 15s | No (writes log + commit hint) |
| `pre-compact.js` | PreCompact | 15s | No (writes snapshot) |

Hook wiring lives in `mewvault/.claude/settings.local.json`. Run `mew harness install` to (re)install.

---

## Silo Detection

All hooks detect the active silo by checking the working directory's path relative to the workspace root:

| Path prefix | Silo | Agent identity |
|------------|------|----------------|
| `wiki/` | wiki | mew-learner |
| `software-projects/` | code | mew-coder |
| `design-studio/` | design | mew-designer |
| `game-lab/` | game | mew-gamedev |
| (anything else) | — | mew-chief |

---

## MCP Servers

Defined in `/Jan/.mcp.json`, enabled per-project in `settings.local.json`.

### memory
- Package: `@modelcontextprotocol/server-memory` (npx)
- Purpose: In-session knowledge graph for building up entity/relation context during long tasks
- Scope: Resets between sessions

### doobidoo
- Binary: `mewvault/venv/bin/mcp-memory-server`
- Backend: SQLite-vec at `~/.mewvault/chroma-wiki/memory.db`
- Embeddings: Ollama `nomic-embed-text` at `localhost:11434`
- Purpose: Persistent semantic search across wiki notes and code
- Re-index: run `scripts/ingest_wiki.py` or `scripts/ingest_code.py` after significant changes

---

## Tier Gates

Every project has a `tier` in `Project_Status.md`. The `pre-tool-use.js` hook enforces hard gates.

| Tier | Gate | Autonomy |
|------|------|----------|
| Pounce | None | Write directly, wrap at end |
| Stalk | Verbal approval in chat | Propose approach, wait, then write |
| MewKing | `plan_approved: true` required | Full `proposals/active/<feature>/plan.md` + approval |

MewKing violations increment `gate_block_count`. At 2 blocks, a `REVIEW_REQUIRED.md` file is auto-written in the proposal directory.

---

## Instinct Pipeline

The system learns from corrections automatically:

1. **Capture** — `post-tool-use.js` detects when the same file is rewritten in <60s. Writes a JSON record to `instincts/pending/` with the before/after diff.
2. **Review** — `mew instinct status` shows pending captures. You decide which are useful.
3. **Promote** — `mew instinct promote <id>` moves the record to `instincts/promoted/`.
4. **Inject** — `session-start.js` reads all promoted instincts and injects them into every session as `## Active Vault Instincts`.

Prune stale instincts (>14 days, confidence <0.8) with `mew instinct prune`.

---

## Rules Hierarchy

Rules load in order: `mew-common` first, then silo-specific. Later rules can override earlier ones.

```
/Jan/.claude/rules/mew-common/
  ├── vault-rules.md      # file system boundaries, cross-silo ops, session discipline
  ├── tier-gates.md       # Pounce / Stalk / MewKing gate definitions
  └── secrets.md          # secret patterns to block

/Jan/.claude/rules/mew-code/
  └── code-rules.md       # Project layout, stack conventions (Next/Astro/Svelte), TDD warning

/Jan/.claude/rules/mew-design/
  └── design-rules.md     # Figma MCP usage, design decision storage, deliverable assembly

/Jan/.claude/rules/mew-game/
  └── godot-rules.md      # GDScript conventions, experiment vs project rules, mechanics tracking
```

---

## Skills

25 skills live in `mewvault/skills/` and are globally symlinked to `~/.claude/skills/`. Invoke with `/skill-name` in any silo.

Full list:
`ci-cd-pipeline-builder`, `code-reviewer`, `context-budget`, `differential-review`,
`dispatching-parallel-agents`, `executing-plans`, `frontend-design`, `get-shit-done`,
`github-ops`, `iterative-retrieval`, `mcp-builder`, `plan-orchestrate`, `shadcn-ui`,
`skill-security-auditor`, `static-analysis`, `subagent-driven-development`,
`systematic-debugging`, `tdd-workflow`, `token-budget-advisor`, `using-git-worktrees`,
`variant-analysis`, `verification-loop`, `web-artifacts-builder`, `webapp-testing`,
`writing-plans`
