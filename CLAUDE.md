# Silo: mewvault — CLI Engine

This silo contains the `mew` CLI: entry point, commands, templates, and secrets.

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

**Model lookup table — never deviate from this:**

| Agent | model param |
|---|---|
| mew-planner | `opus` |
| fable | `opus` |
| mew-chief | `sonnet` |
| mew-coder | `sonnet` |
| mew-researcher | `sonnet` |
| mew-designer | `sonnet` |
| mew-ideator | `sonnet` |
| mew-gamedev | `sonnet` |
| mew-learner | `haiku` |
| mew-archivist | `haiku` |

**Correct pattern:**
```
Agent({
  description: "mew-planner: ...",
  model: "opus",          ← required, always
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

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
