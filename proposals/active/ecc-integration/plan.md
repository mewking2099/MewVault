# ECC Integration Plan — MewVault Upgrade

**Source:** github.com/affaan-m/everything-claude-code + github.com/obra/superpowers  
**Goal:** Bring mewvault's hooks and skills up to ECC best practices across three pillars: token optimization, memory persistence, and subagent orchestration.

---

## Pillar 1: Token Optimization

### 1.1 — Write size guard in `pre-tool-use.js`

Add a content-length check to the existing PreToolUse hook for Write calls:

- **Warn** (stderr, exit 0) when `content.length > 40,000 chars` (~10k tokens)
- **Block** (stderr, exit 2) when `content.length > 200,000 chars` (~50k tokens)

Implement in the existing `main()` function after the TDD gate. Make limits configurable via `mewvault/.claude/limits.json` so they can be tuned without touching hook code.

```json
// .claude/limits.json (new file)
{
  "write_warn_chars": 40000,
  "write_block_chars": 200000
}
```

### 1.2 — Slim `session-start.js` injection

The session-start hook currently injects project status, instincts, and open issues with no size cap. Add a `MAX_INJECT_CHARS` guard (default 6,000 chars) that truncates the injected block with a `[truncated — run mew status for full context]` notice rather than dumping everything.

### 1.3 — Model selection guidance (session-start)

Append a one-line model routing hint to the session-start output based on project tier:
- Pounce → "Suggest: Haiku for exploration, Sonnet for implementation"
- Stalk → "Suggest: Sonnet for implementation, Opus for architecture calls"
- MewKing → "Suggest: Opus for architecture, Sonnet for code, Haiku for search"

This guides subagent spawning without adding context overhead.

### 1.4 — MCP audit note in session-start

When >8 MCP tools are active, log a one-line warning: `⚠ N MCP tools loaded (~N×500 tokens). Use /context-budget to audit.`

---

## Pillar 2: Memory Persistence

### 2.1 — Session state files

On session end, `session-end.js` writes a bounded summary to:
```
~/.claude/sessions/<project-name>-session.tmp
```

Structure:
```markdown
# Session: <project> — <date>

## What worked
- …

## What failed / was abandoned
- …

## What's next
- …

## Open questions
- …
```

Rotate: keep last 5 `.tmp` files per project, delete older ones.

### 2.2 — Session state loading in `session-start.js`

At session start, load the most recent `.tmp` file for the current project (match by closest ancestor directory name). Cap at `ECC_SESSION_START_MAX_CHARS` (default 8,000). Inject into Claude's context via stdout as:

```
--- Prior session context (capped at 8000 chars) ---
[content]
--- End prior session context ---
```

Allow opt-out: if `ECC_SESSION_START_CONTEXT=off` is set, skip loading.

### 2.3 — Pre-compact state capture

Enhance `pre-compact.js` to save a compact snapshot before compaction fires:
```
~/.claude/sessions/<project>-precompact.md
```

Include: list of files modified this session, current task summary from TodoWrite if available, any unresolved errors from the last Bash output.

---

## Pillar 3: Subagent Orchestration

### 3.1 — Agent model routing

When spawning subagents (Agent tool calls), default model selection based on task type:

| Role | Model |
|------|-------|
| Explore / search | Haiku |
| Simple edit, 1-2 files | Haiku |
| Multi-file implementation | Sonnet |
| Architecture / design | Opus |
| Security / review | Opus |

Document this table in `mewvault/wiki/subagent-model-routing.md` so it loads as context.

### 3.2 — Iterative retrieval skill

Add from ECC: `skills/iterative-retrieval/SKILL.md` (4-phase loop: dispatch → evaluate → refine → return). Use when spawning subagents that need codebase context they can't predict upfront.

### 3.3 — Plan → agent orchestration

Add ECC's `plan-orchestrate` skill to bridge MewKing plan documents to per-step agent chains. Trigger: user says "orchestrate this plan" or "give me agent prompts for each step".

---

## Skills to Add Now (from superpowers + ECC)

These are already being added alongside this plan:

| Skill | Source | Purpose |
|-------|--------|---------|
| `systematic-debugging` | superpowers | 4-phase root cause analysis |
| `dispatching-parallel-agents` | superpowers | Concurrent subagent workflows |
| `subagent-driven-development` | superpowers | Two-stage review per task |
| `using-git-worktrees` | superpowers | Isolated parallel branches |
| `writing-plans` | superpowers | Spec-driven plan documents |
| `executing-plans` | superpowers | Plan execution with checkpoints |
| `verification-before-completion` | superpowers | Evidence before claims |
| `github-ops` | ECC | PR/issue management via gh CLI |
| `context-budget` | ECC | Audit context window consumption |
| `token-budget-advisor` | ECC | Control response depth |
| `iterative-retrieval` | ECC | Progressive context retrieval for subagents |

---

## Skills NOT Yet Available

These are in the post but not in ECC or superpowers (need separate fetches):

| Skill | Source | Status |
|-------|--------|--------|
| `get-shit-done` | gsd repo | Pending |
| `static-analysis` | trailofbits | Pending |
| `variant-analysis` | trailofbits | Pending |
| `differential-review` | trailofbits | Pending |
| `skill-security-auditor` | alirezarezvani | Pending |
| `webapp-testing` | anthropics | Pending |
| `mcp-builder` | anthropics | Pending |
| `frontend-design` | anthropics | Pending |
| `shadcn/ui` | shadcn | Pending |
| `web-artifacts-builder` | anthropics | Pending |
| `ci-cd-pipeline-builder` | alirezarezvani | Pending |

---

## Implementation Order

**Phase A (hooks — Stalk tier, no gate needed):**
1. `pre-tool-use.js` write guard (1.1)
2. `session-start.js` max-chars cap (1.2)
3. `session-end.js` state file (2.1)
4. `session-start.js` state loading (2.2)
5. `pre-compact.js` snapshot (2.3)

**Phase B (hooks — enhancement):**
6. Model selection hint in session-start (1.3)
7. MCP count warning in session-start (1.4)

Each change is isolated to one hook file. No cross-silo changes. Tests: manually verify hook outputs after each change.
