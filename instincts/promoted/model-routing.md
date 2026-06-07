# Instinct: Model Routing

**Type:** routing rule  
**Scope:** all silos  
**Confidence:** 1.0

---

## The Rule

Claude Sonnet does all tool-using work. DeepSeek handles pure-generation tasks only. Opus handles architecture and MewKing planning.

**If a task requires any tool call — Read, Write, Bash, Edit, MCP — Claude does it. Full stop.**

---

## Routing Matrix

| Task | Route | Command |
|---|---|---|
| File I/O, Read/Write/Edit/Bash | Claude Sonnet (default) | — |
| Frontend / React / CSS | Claude Sonnet | — |
| Debugging | Claude Sonnet | — |
| Multi-file refactor | Claude Sonnet | — |
| Architecture decision / MewKing proposal | Opus (`mew-planner`) | `mew dispatch --agent mew-planner` |
| Isolated algorithm or function (no context needed) | DeepSeek V3 (`mew-coder-simple`) | `mew dispatch --agent mew-coder-simple` |
| Simple boilerplate block | DeepSeek V3 (`mew-coder-simple`) | `mew dispatch --agent mew-coder-simple` |
| Math / logic puzzle / reasoning chain | DeepSeek R1 (`mew-coder-reason`) | `mew dispatch --agent mew-coder-reason` |

---

## How to Dispatch

**Inline:**
```bash
mew dispatch --agent mew-coder-simple --task "Write a Fisher-Yates shuffle in GDScript"
```

**From file (preferred for long prompts — avoids shell escaping):**
```bash
# Write context to temp file, then dispatch
cat > /tmp/task.md << 'EOF'
Write a pure function that merges two sorted arrays in Python.
No imports. Return type annotated.
EOF
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md
```

**Capture output for review before integrating:**
```bash
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md > /tmp/result.md
# Review /tmp/result.md, then integrate manually
```

---

## Context Serialisation

When dispatching to DeepSeek, always serialise the full relevant context into the task file. DeepSeek has no conversation history.

Include:
- Language and framework
- Function signature or interface required
- Any constraints (no imports, typed, max lines, etc.)
- Example input/output if the behaviour is non-obvious

Do NOT include:
- File paths from this workspace (DeepSeek can't read them)
- Secrets or API keys
- Conversation history

---

## Fallback Rule

DeepSeek routing is **optional**. If the proxy is unavailable, Claude handles all tasks directly. Never block on a failed dispatch.

**Exit code convention for `mew dispatch`:**
- Exit `0` — success, use the output
- Exit `1` — usage error (bad args) — fix the command
- Exit `3` — proxy unavailable (`DISPATCH_UNAVAILABLE`) — retake the task as Claude directly

When exit code is `3`, do NOT retry dispatch. Simply handle the task yourself and optionally note: "DeepSeek proxy not running — handled by Claude."

**Check proxy status:** `mew dispatch --check`  
**Start proxy:** `bash proxy/start-proxy.sh` (requires `DEEPSEEK_API_KEY` in `secrets/workspace.env`)

---

## What Stays Claude-Only

- All tool-using tasks (no exceptions)
- Debugging sessions requiring Bash output
- Frontend / React work (requires file reads + iteration)
- Any task needing multi-turn conversation
- Anything where correctness is hard to verify without running it
