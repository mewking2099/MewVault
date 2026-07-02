# Instinct: Model Routing

**Type:** routing rule  
**Scope:** all silos  
**Confidence:** 1.0

---

## The One Decision Rule

> **Default for all coding tasks: DeepSeek V3 (`mew-coder-simple`).**  
> Fall back to Claude only if the task is in the **Never Dispatch** list below.  
> If it needs to **reason through logic before writing** → DeepSeek R1.

---

## Routing Matrix

### DeepSeek V3 — `mew-coder-simple` (DEFAULT for all coding tasks)

Attempt dispatch for any coding task unless it is in the Claude-only list below.

| Task | Example |
|---|---|
| Pure backend functions | Given a signature, implement the function body |
| API route handlers | Given a schema, write the handler |
| Database queries / ORM | Given the schema, write the query |
| Data transformation utilities | Pure functions with typed input/output |
| Config and schema files | YAML, JSON, TOML with a known shape |
| GDScript game mechanics | Given a spec, write a self-contained .gd script |
| Python CLI commands | Following the established mewvault pattern |
| Shell scripts | Low-ambiguity automation |
| Type / interface definitions | Given a data shape, generate the types |
| Boilerplate following a known pattern | When the shape is clear and repetitive |
| Feature implementation | Implement a well-understood feature |
| Bug fix (isolated, known root cause) | Fix a single function or file |
| Refactor (single file, clear goal) | Rename, extract, simplify |
| New component (spec known) | React or Svelte component with clear props |

### Always Claude (Sonnet 5) — fallback only

| Task | Why |
|---|---|
| Debugging (root cause unknown) | Needs Read → Bash → fix iteration loop |
| Multi-file coordination / refactor | Cross-file context dependencies |
| Test writing | Requires behavioral understanding of code under test |
| TypeScript with complex generics | Type inference needs full codebase context |
| Code review / PR feedback | Nuanced judgment |
| Documentation | Contextual understanding |
| Any task requiring tool calls | Claude is the only model with tool access |
| Small patches (<10 lines, obvious fix) | Not worth serializing; faster direct |
| Spec is still unclear | Clarify first, then dispatch |
| Auth, crypto, security-sensitive code | Correctness too high-stakes for blind generation |

### DeepSeek R1 — `mew-coder-reason` (reasoning-then-generation)

| Task | Example |
|---|---|
| Algorithms and data structures | Sorting, graph traversal, DP problems |
| State machine implementation | Requires reasoning through all transitions |
| Regex and complex parsing logic | Analytically derived before written |
| Performance optimization | Trade-off analysis before the rewrite |
| Mathematical / logic-heavy functions | Non-obvious correctness requirements |

### Opus — reserved

| Task | Why |
|---|---|
| Architecture decisions | High-stakes long-form reasoning |
| MewKing proposals (plan.md) | Complex planning, multi-session scope |

---

## Auto-Dispatch Protocol (mandatory — fires mid-session on every qualifying task)

**Before writing any task that falls in the DeepSeek columns, always attempt dispatch.** This check is per-task, not per-session — a proxy that was down at session start may be running now.

**Step 1 — Attempt dispatch directly.** Do not pre-check; just dispatch. If the proxy is down, the command exits 3 in under 3 seconds and you retake the task as Claude.

**Step 2 — Gather context via tools first.** Read the relevant files, understand the interface. Do NOT skip this — DeepSeek has no workspace access.

**Step 3 — Serialize the full spec into a task file:**
```bash
cat > /tmp/task.md << 'EOF'
Language: Python 3.11
Task: Implement `merge_sorted_arrays(a: list[int], b: list[int]) -> list[int]`
Constraints: no imports, O(n+m) time, type-annotated
Example: merge_sorted_arrays([1,3,5], [2,4,6]) → [1,2,3,4,5,6]
EOF
```

Include:
- Language and framework
- Exact function signature / interface
- File it will live in (one sentence of context)
- Constraints (no imports, max lines, style rules)
- Example input/output if non-obvious

Do NOT include: workspace file paths, secrets, conversation history.

**Step 4 — Dispatch and capture:**
```bash
# Review before applying:
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md

# Write directly to destination:
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md --write src/utils/merge.py

# For logic-heavy tasks:
mew dispatch --agent mew-coder-reason --task-file /tmp/task.md
```

**Step 5 — Review and apply.** Read the output. If it matches the spec, apply it. If it's wrong, fix it as Claude directly — do NOT re-dispatch in a loop.

---

## Mid-Session Trigger (automatic)

This fires every time you are about to write code. Run through it before reaching for Write or Edit:

```
Is this task in the DeepSeek V3 or R1 column?
  YES → attempt dispatch (Step 3–5 above)
        exit 3? → handle as Claude directly, note "proxy down for this task"
  NO  → handle as Claude directly
```

Qualifying task types that MUST trigger this check mid-session:
- Any pure backend function or utility (not UI, not debugging)
- Any API route handler where the interface is already known
- Any GDScript game mechanic with a clear spec
- Any data transformation, config file, type definition, or shell script
- Any boilerplate following an established pattern in the project

---

## Fallback Rule

DeepSeek routing is **optional infrastructure**. If the proxy is unavailable for a task, Claude handles that task directly. Never block.

**Exit code convention:**
- `0` — success, use the output
- `1` — usage error — fix the command
- `3` — proxy unavailable — retake the task as Claude directly, tell the user "proxy down — handled by Claude"

If exit code 3 appears repeatedly in a session, surface this to the user:
> "DeepSeek proxy is not running. Run `bash proxy/start-proxy.sh` in the mewvault directory to enable cheaper model routing for backend tasks."

**Start proxy:** `bash proxy/start-proxy.sh` (requires `DEEPSEEK_API_KEY` in `secrets/workspace.env`)  
**Check proxy:** `mew dispatch --check`

---

## What Never Goes to DeepSeek

- UI/UX components and anything requiring visual judgment
- Debugging sessions (no tool access)
- Multi-file coordination
- Frontend/React work (requires iteration against actual renders)
- Tests (requires behavioral understanding of subject code)
- Anything where correctness is hard to verify without running it
- Tasks where the spec itself is unclear — clarify with the user first, then dispatch
