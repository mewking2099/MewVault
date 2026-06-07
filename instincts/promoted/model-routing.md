# Instinct: Model Routing

**Type:** routing rule  
**Scope:** all silos  
**Confidence:** 1.0

---

## The One Decision Rule

> If the task needs **design judgment, tool iteration, or cross-file context** → Claude.  
> If the **spec is complete and the output contract is tight** → DeepSeek V3.  
> If it needs to **reason through logic before writing** → DeepSeek R1.

---

## Routing Matrix

### Always Claude (Sonnet)

| Task | Why |
|---|---|
| UI/UX components (React, animations, CSS) | Requires visual/design judgment, accessibility intuition, component API design |
| Frontend state management | Multi-file context dependencies |
| Debugging | Needs Read → Bash → fix iteration loop |
| Multi-file refactor | Cross-file coordination |
| Test writing | Requires behavioral understanding of the code under test |
| TypeScript with complex generics | Type inference needs full codebase context |
| Code review / PR feedback | Nuanced judgment |
| Documentation | Contextual understanding |
| Any task requiring tool calls | Claude is the only model with tool access |
| Small fixes / patches (<15 lines) | Not worth serializing; faster direct |
| Anything needing multi-turn iteration | DeepSeek has no conversation history |

### DeepSeek V3 — `mew-coder-simple` (fast, spec-driven generation)

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

## Auto-Dispatch Protocol (mandatory when proxy is running)

For any task that falls in the DeepSeek columns above, Claude MUST dispatch before writing. The steps:

**1. Check proxy** (once per session, skip if already confirmed up):
```bash
mew dispatch --check
```
If exit code 3 → proxy down → handle all tasks as Claude directly for this session.

**2. Gather context via tools first.** Read the relevant files, understand the interface. Do NOT skip this step — DeepSeek has no workspace access.

**3. Serialize the full spec into a task file:**
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

Do NOT include: file paths from this workspace, secrets, conversation history.

**4. Dispatch and capture:**
```bash
# To stdout (review before applying):
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md

# Write directly to destination:
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md --write src/utils/merge.py
```

**5. Review and apply.** Read the output. If it matches the spec, apply it (Write/Edit). If it's wrong, fix it as Claude directly — do NOT re-dispatch in a loop.

---

## Fallback Rule

DeepSeek routing is **optional infrastructure**. If the proxy is unavailable, Claude handles all tasks. Never block on a failed dispatch.

**Exit code convention:**
- `0` — success, use the output
- `1` — usage error — fix the command
- `3` — proxy unavailable (`DISPATCH_UNAVAILABLE`) — retake the task as Claude directly

When exit code is `3`, do NOT retry. Note "DeepSeek proxy not running — handled by Claude." and proceed.

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
