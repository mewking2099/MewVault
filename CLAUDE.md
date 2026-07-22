# Silo: mewvault — CLI Engine

This silo contains the `mew` CLI: entry point, commands, templates, and secrets.

> **What's new (2026-07-08):** major overhaul — token/caching fixes (Headroom removed), `mew doctor` auto health checks, agent dispatch ledger + model gate, `mew dashboard`, wiki retrieval loop, spec-driven development (TDD hard gate, `spec` trigger, CI safety net), design silo v2 (Impeccable enforcement, audit gate, token drift, handoff packager), and natural-language command triggers. Full details: `wiki/whats-new-2026-07-08.md`.

## Structure

- `mew.py` — entry point (`python mew.py <command>`)
- `mew/` — Python package (commands, workspace detection, utilities)
- `mew/memory_store.py` — SQLite FTS5 adapter for cross-session memory
- `mew/commands/memory.py` — `mew memory sync|search|recall|purge`
- `templates/` — scaffolding templates per project type
- `secrets/` — gitignored, owner-only permissions
- `.mew-memory.db` — gitignored SQLite memory store (auto-created on first sync)

## Development rules

- Python 3.11+. Use `pathlib.Path` for all file operations — no hardcoded POSIX paths.
- Cross-platform: Mac and Windows. File permission hardening uses `icacls` on Windows, `chmod 0600` on Unix.
- Never echo secret values. Never commit `secrets/*.env`.
- Keep each command in its own file under `mew/commands/`.
- Templates use `{{placeholder}}` syntax — double curly braces.

## Running

```bash
python mew.py help
python mew.py init
python mew.py status --quick
```

Or install editably: `pip install -e .` → `mew help`

## Optional third-party tooling

These are helpful but not required. MewVault works without them. Full setup guide: `wiki/tooling-linting.md`.

| Tool | Silo | Purpose | Install |
|---|---|---|---|
| `ruff` | mewvault | Python lint + format | `pip install ruff` |
| `gdtoolkit==4.*` | game-lab | GDScript lint + format | `pip install "gdtoolkit==4.*"` |
| `fallow` | software-projects | TS/JS dead code + duplication | `npx fallow` |
| `graphifyy` | all silos | Knowledge graph + `/graphify` skill | `pip install graphifyy` |

## Agent dispatch — mandatory rules

When spawning any mew agent via the Agent tool, you MUST pass the `model` parameter explicitly. The `.claude/agents/` frontmatter only enforces models when the user invokes agents natively (e.g. `@mew-planner`). When you call the Agent tool programmatically, you are responsible for passing the correct model — otherwise every agent silently runs on the session default.

**Important constraint:** The Agent tool only accepts short family aliases (`"sonnet"`, `"opus"`, `"haiku"`). Full model IDs like `claude-sonnet-4-6` cause an `InputValidationError`. The alias resolves to Claude Code's current default for that family (currently Sonnet 4.6, Haiku 4.5). We cannot pin a specific sub-version through this parameter — if precise version control matters, raise it with the user.

**Model lookup table — never deviate from this:**

| Agent | model param | Resolves to (current) |
|---|---|---|
| fable | `opus` | claude-opus-4-7 |
| mew-planner | `opus` | claude-opus-4-7 |
| mew-chief | `sonnet` | claude-sonnet-4-6 |
| mew-coder | `sonnet` | claude-sonnet-4-6 |
| mew-designer | `sonnet` | claude-sonnet-4-6 |
| mew-gamedev | `sonnet` | claude-sonnet-4-6 |
| mew-learner | `sonnet` | claude-sonnet-4-6 |
| mew-researcher | `sonnet` | claude-sonnet-4-6 |
| mew-ideator | `haiku` | claude-haiku-4-5 |
| mew-archivist | `haiku` | claude-haiku-4-5 |

**Correct pattern:**
```
Agent({
  description: "mew-planner: ...",
  model: "opus",   ← short alias only — full IDs are rejected by the Agent tool
  prompt: "..."
})
```

**Wrong pattern (silent Sonnet fallback — never do this):**
```
Agent({
  description: "mew-planner: ...",
  prompt: "..."           ← model omitted = always Sonnet regardless of .claude/agents/
})
```

DeepSeek agents (mew-coder-simple, mew-coder-reason) cannot be dispatched via the Agent tool — use `mew dispatch` + LiteLLM proxy instead.

## Planning discipline — MASTER_SPEC as single source of truth

When planning any feature for a known project (especially DSaaS / `software-projects/dsaas`):

1. **Never create a new `proposals/active/<feature>/plan.md`** without first reading the project's MASTER_SPEC (e.g. `proposals/MASTER_SPEC.md §8 Proposal Index`).
2. If the feature maps to a known phase in MASTER_SPEC, add a section there (`§N`) instead of a new file.
3. If a standalone `plan.md` already exists and overlaps with MASTER_SPEC, consolidate it: integrate the content into the relevant MASTER_SPEC section and replace the file with a one-line stub pointing to MASTER_SPEC.
4. Standalone `plan.md` files are allowed only for truly standalone work that has no corresponding MASTER_SPEC phase — and only after confirming this with the user.

## Project lock

`mewvault/.active-project` is a machine-local lock file (gitignored). When it exists, the pre-tool-use hook blocks writes to any path outside the locked project directory (with exemptions for `mewvault/` tooling and `~/.claude/` memory).

Commands:
- `mew lock <project-path>` — lock to a project (e.g. `mew lock software-projects/dsaas`)
- `mew lock --status` — show what is currently locked
- `mew unlock` — release the lock

**Auto-lock on session start (mandatory):** When the user says anything that means "let's work on X" — e.g. "let's work on dsaas", "start a dsaas session", "I want to work on yaana DS" — immediately run `mew lock <resolved-path>` before doing anything else, then confirm: "Locked to `<path>`." Do not wait to be asked.

**Auto-unlock on project switch:** When the user signals a switch to a different project, run `mew unlock` then `mew lock <new-path>` automatically.

**Known project name → path map:**
- `dsaas` / `DSaaS` → `software-projects/dsaas`
- `yaana DS` / `yaana design system` → `software-projects/yaana-design-system`
- `mewvault` / `vault` / `mew cli` → `mewvault`
- `game-lab` / any game project → `game-lab/<project>`
- `design-studio` / any design project → `design-studio/<project>`
- `career` / `career studio` → `career-studio`
- `idea-hub` / `ideas` → `idea-hub`

If the project name is ambiguous, ask before locking.

The hook message is explicit: it names the locked path and the blocked path, so there's no silent bleed.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
