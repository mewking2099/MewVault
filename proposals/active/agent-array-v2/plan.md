# Plan: Agent Array v2 — Dispatcher + Skill Plugins

## Tier: MewKing
## Status: COMPLETE — approved 2026-07-02, all 5 phases implemented

---

## Summary

Redesign the MewVault agent system from a static array of personas into a
live dispatcher + skill plugin architecture. mew-chief becomes the active
routing layer: every request is classified, then handed to the right specialist
sub-agent which is spawned with its model and a dynamically-assembled skill
context. New capabilities are added by dropping a `.md` file — no code changes.
Claude Code native skills and MCP plugins slot in as first-class citizens.

---

## Architecture overview

```
User message
      │
      ▼
┌───────────────────────────────────────────────────────────────┐
│  mew-chief (Sonnet) — dispatcher                              │
│  Reads routing-index.json · classifies intent · announces     │
│  "Routing to mew-planner…"                                    │
└──────────┬────────────────┬──────────────┬────────────────────┘
           │                │              │
     ┌─────▼──────┐  ┌──────▼──────┐  ┌───▼───────────┐  …
     │ mew-planner│  │  mew-coder  │  │ mew-archivist │
     │   (Opus)   │  │  (Sonnet)   │  │   (Haiku)     │
     └─────┬──────┘  └──────┬──────┘  └───┬───────────┘
           │                │              │
        skills/          skills/        skills/
        ├ write-plan      ├ tdd          ├ session-wrap
        ├ tier-check      ├ code-review  ├ commit-suggest
        ├ risk-map        ├ refactor     └ log-write
        └ spec-parse      └ test-gen
             │
        can chain to →  mew-archivist (write the plan.md)
                    →  /writing-plans (Claude Code skill)
```

Sub-agents are spawned via the Agent tool inside the active Claude Code session.
No proxy, no API key — works on Claude Code subscription.

---

## Key design decisions

### 1. Dispatcher announces routing

mew-chief always surfaces the routing decision before spawning:

```
→ Routing to mew-planner (opus) — write-mewking-plan skill
```

This lets you intercept ("no, handle it yourself") and builds trust in the system.

### 2. Skill chaining

A skill can declare `chains_to` agents/skills. mew-chief orchestrates the chain:

```yaml
# agents/mew-planner/skills/write-mewking-plan.md
chains_to:
  - agent: mew-archivist
    skill: log-write
    trigger: on_complete
```

Chains are explicit in the skill file — not inferred. Circular chains are detected
and blocked by the skill loader.

### 3. Skill discovery + sync

Skills are discovered at session start. No manual registry:

```
Drop file → mew agent sync → routing-index.json regenerated → next session: live
```

`routing-index.json` is a flat index of every skill across all agents:

```json
{
  "mew-planner": [
    { "name": "write-mewking-plan", "triggers": ["plan","architect","proposal"], "inject": "on-trigger" }
  ],
  ...
}
```

`session-start.js` reads this and injects it into mew-chief's routing context.
mew-chief never needs to know about skill internals — just names, triggers, agents.

### 4. Claude Code native skills as agent plugins

Existing slash-command skills in `skills/` can be invoked from within sub-agents
via the Skill tool. Agent skills declare which CC skills they delegate to:

```yaml
# agents/mew-planner/skills/write-plan-via-cc.md
claude_code_skills:
  - writing-plans
  - executing-plans
```

The sub-agent receives instructions to call those skills via the Skill tool.
This makes every CC skill in `skills/` available as a building block.

### 5. MCP plugins scoped per agent

Each agent's `manifest.yaml` declares which MCP servers it needs.
The Agent tool spawn includes `--mcp-config` for those servers:

```yaml
# agents/mew-designer/manifest.yaml
mcp_servers:
  - figma
  - canva
```

The skill loader resolves these against `/Jan/.mcp.json` at spawn time.
mew-coder never gets Figma. mew-designer always gets it.

### 6. Online skill repo fetching

```bash
mew agent fetch-skills --from awesome-claude   # curated list
mew agent fetch-skills --url <github-raw-url>  # single skill file
mew agent fetch-skills --repo <gh-slug>        # full repo scan
```

Fetched skills are staged in `agents/_fetched/<source>/` for review before
being promoted into an agent's `skills/` directory. Never auto-promoted.

Sources to seed from (Phase 4):
- anthropics/prompt-library (official examples)
- f/awesome-chatgpt-prompts (adaptable system prompts)
- mewking2099/mewvault-skills (future: own public skills repo)

---

## New directory structure

```
mewvault/
  agents/
    _fetched/                   ← staged online skills, awaiting promotion
    mew-chief/
      manifest.yaml
      system-prompt.md
      skills/
        dispatcher.md           ← THE routing logic (editable markdown)
        standup.md
        wrap.md
    mew-planner/
      manifest.yaml
      system-prompt.md
      skills/
        write-mewking-plan.md
        tier-analysis.md
        risk-map.md
        spec-parse.md
    mew-coder/
      manifest.yaml
      system-prompt.md
      skills/
        tdd-workflow.md
        code-review.md
        refactor.md
        test-gen.md
    mew-designer/
      manifest.yaml
      system-prompt.md
      skills/
        figma-spec.md
        component-design.md
        token-audit.md
    mew-archivist/
      manifest.yaml
      system-prompt.md
      skills/
        session-wrap.md
        commit-suggest.md
        log-write.md
    mew-learner/
      manifest.yaml
      system-prompt.md
      skills/
        concept-distill.md
        ingest-pdf.md
        link-notes.md
    mew-gamedev/
      manifest.yaml
      system-prompt.md
      skills/
        gdscript-review.md
        mechanic-design.md
  agents/.routing-index.json    ← auto-generated by mew agent sync
  templates/agents/             ← DEPRECATED, kept during transition
```

---

## Manifest format

```yaml
# agents/<name>/manifest.yaml
name: mew-planner
model: opus               # opus | sonnet | haiku
silo: global              # global | code | design | game | wiki
role: Architecture and MewKing planning
routing_triggers:
  - plan
  - architect
  - mewking
  - proposal
  - risk
  - phase
mcp_servers: []           # MCP server keys from .mcp.json
handles_direct: false     # true = mew-chief can also handle itself
```

---

## Skill file format

```yaml
---
name: write-mewking-plan
triggers: [plan, architect, proposal, mewking]
description: Produce plan.md with phases, files, risks, acceptance tests
inject: on-trigger         # always | on-trigger | manual
chains_to: []              # [{agent, skill, trigger: on_complete|on_request}]
claude_code_skills: []     # CC slash-command skills to delegate to
requires_approval: true    # pause and show output before continuing
---

# Skill: Write MewKing Plan

[instructions for the sub-agent...]
```

---

## Files created

| Path | Purpose |
|---|---|
| `agents/*/manifest.yaml` | 7 agent manifests |
| `agents/*/system-prompt.md` | migrated from `templates/agents/*.md` |
| `agents/*/skills/*.md` | ~3–4 starter skills per agent (25 total) |
| `agents/.routing-index.json` | auto-generated, not hand-edited |
| `agents/mew-chief/skills/dispatcher.md` | THE routing logic |
| `mew/commands/agent.py` | rewritten: sync, fetch-skills, invoke updated |
| `mew/lib/skill_loader.py` | new: scans skills, builds assembled context |
| `hooks/session-start.js` | updated: inject routing-index + dispatcher skill |

## Files modified

| Path | Change |
|---|---|
| `mew/commands/agent.py` | add `sync`, `fetch-skills` sub-commands |
| `mew/commands/help_cmd.py` | update agent help text |
| `hooks/session-start.js` | inject routing-index.json into mew-chief context |

## Files deprecated (not deleted until Phase 5)

| Path | Replacement |
|---|---|
| `templates/agents/*.md` | `agents/*/system-prompt.md` |

---

## Phases

### Phase 1 — Directory structure + migration (Pounce, ~1h)
- Create `agents/` tree
- Write 7 `manifest.yaml` files
- Migrate `templates/agents/*.md` → `agents/*/system-prompt.md`
- `mew agent list` reads from new structure, falls back to old

### Phase 2 — Skill loader library (Pounce, ~1h)
- `mew/lib/skill_loader.py`
  - `scan_agent_skills(agent_name)` → list of skill dicts
  - `assemble_context(agent_name, task)` → system_prompt + matched skills string
  - `detect_chains(skill)` → list of chain steps, cycle detection
  - `build_routing_index()` → writes `agents/.routing-index.json`
- `mew agent sync` command: runs `build_routing_index()`

### Phase 3 — Dispatcher skill + session-start injection (Stalk, ~2h)
- Write `agents/mew-chief/skills/dispatcher.md` — routing instructions with
  routing-index embedded at inject time
- Update `session-start.js` to:
  1. Read `agents/.routing-index.json`
  2. Append it to the mew-chief context block as `## Agent Routing Index`
  3. Append `dispatcher.md` skill instructions
- Test: ask mew-chief a planning question → should announce routing to mew-planner

### Phase 4 — Seed skills (Pounce per agent, ~3h total)
- Write 3–4 starter skills per agent (from existing rules/templates knowledge)
- Implement `mew agent fetch-skills` with staging area
- Seed from one external source (anthropics/prompt-library) as proof of concept

### Phase 5 — Chaining + MCP scoping (Stalk, ~2h)
- Implement chain resolution in skill_loader.py
- Pass `--mcp-config` to Agent tool spawns based on manifest.mcp_servers
- Deprecate `templates/agents/` with migration notice

---

## Risks

| Risk | Mitigation |
|---|---|
| Dispatcher over-routes (everything goes to sub-agent) | dispatcher.md explicitly lists direct-handle cases; tune via that file |
| Token budget blown by skill injection | skill_loader respects `MEW_SESSION_START_MAX_TOKENS`; on-trigger skills only load when needed |
| Skill chains loop | skill_loader.py detects cycles at scan time, raises before spawn |
| Fetched skills are malicious/poor quality | staging area (`_fetched/`) requires explicit `mew agent promote` before going live |
| Migration breaks `mew agent invoke` | fallback: reads `templates/agents/` if `agents/` not found |

---

## Success criteria

- [ ] `mew agent sync` runs in < 1s and produces valid `routing-index.json`
- [ ] Asking "plan the auth refactor" causes mew-chief to announce "Routing to mew-planner…" and spawn a sub-agent on Opus
- [ ] Dropping a new `.md` file + running `mew agent sync` makes the skill available in the next session with zero other changes
- [ ] `mew agent fetch-skills --from awesome-claude` stages skills without auto-promoting
- [ ] `mew agent invoke mew-planner` still works (backwards-compatible)
- [ ] A mew-planner skill successfully invokes `/writing-plans` CC skill
- [ ] Chain: mew-planner → mew-archivist executes in sequence with correct models

---

## Rollback

- `templates/agents/` is kept intact throughout all phases — revert `agent.py`
  to read from there if `agents/` causes issues
- `session-start.js` changes are additive — remove the routing-index injection
  block to return to today's behaviour
- No database, no migration — all state is flat files
