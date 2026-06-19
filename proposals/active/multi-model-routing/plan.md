# Multi-Model Routing — MewVault Plan

**Status:** Complete — routing instinct live as of 2026-06-19  
**Tier:** Stalk (one focused session once key is available)  
**Drafted:** 2026-06-04  

---

## Goal

Claude Code stays as the orchestrator/brain for all sessions. DeepSeek handles isolated pure-generation tasks (no tool calls required). Opus handles architecture and MewKing planning. Routing is driven by Claude's judgment guided by an instinct rule — no automated pre-router.

---

## Classification Matrix

| Task type | Needs tools? | Route to |
|-----------|-------------|----------|
| File I/O, Read/Write/Bash | Yes | Claude Sonnet (always) |
| Frontend / React / CSS | Yes | Claude Sonnet |
| Debugging | Yes | Claude Sonnet |
| Multi-file refactor | Yes | Claude Sonnet |
| Architecture decision | No | Opus (`mew-planner`) |
| MewKing proposal | No | Opus (`mew-planner`) |
| Long-horizon plan | No | Opus (`mew-planner`) |
| Simple plan (known feature) | No | DeepSeek V3 (`mew-coder-simple`) |
| Isolated algorithm / function | No | DeepSeek V3 (`mew-coder-simple`) |
| Boilerplate block | No | DeepSeek V3 (`mew-coder-simple`) |
| Math / logic puzzle | No | DeepSeek R1 (`mew-coder-reason`) |

**Rule:** If a task needs any tool call, Claude does it. DeepSeek only receives pure-generation prompts with full context serialised by Claude.

---

## Architecture — Three Layers

### Layer 1: LiteLLM config additions (`proxy/litellm-config.yaml`)

```yaml
- model_name: mew-coder-simple
  litellm_params:
    model: deepseek/deepseek-chat
    api_key: os.environ/DEEPSEEK_API_KEY

- model_name: mew-coder-reason
  litellm_params:
    model: deepseek/deepseek-reasoner
    api_key: os.environ/DEEPSEEK_API_KEY
```

Existing `mew-planner` (Opus) stays as-is. No changes to Sonnet agents.

### Layer 2: `mew dispatch` command (`mew/commands/dispatch.py`)

```
mew dispatch --agent mew-coder-simple --task-file /tmp/task.md
```

- Reads prompt from temp file (avoids bash escaping issues and prompt injection)
- POSTs to LiteLLM proxy at `:4000` using the OpenAI-compatible endpoint
- Streams or returns full response as stdout
- Claude calls this via the Bash tool, captures result, reviews and integrates

No execution loop — Claude handles all tool calls itself. DeepSeek only generates text.

### Layer 3: Routing instinct (`instincts/model-routing.md`)

Markdown rule loaded at session start that tells Claude:
- When to dispatch vs. do it itself
- How to serialise context into the task file
- How to evaluate and integrate worker output
- Fallback: if dispatch fails or output is wrong, Claude retakes the task

---

## Build Order (one Stalk session)

1. `mew/commands/dispatch.py` — ~60 lines, POST to LiteLLM, stdout return (~1hr)
2. Wire into `mew/cli.py` (~15min)
3. Update `proxy/litellm-config.yaml` with DeepSeek model entries (~5min)
4. Write `instincts/model-routing.md` — routing rules + serialisation guide (~20min)
5. `mew secret set DEEPSEEK_API_KEY` when key is available
6. Test: simple algorithm → DeepSeek, file refactor → Claude, plan → Opus

---

## Pre-conditions

- [x] DeepSeek API key obtained
- [x] LiteLLM proxy tested locally (`start-proxy.sh`) — confirmed reachable 2026-06-19
- [x] `DEEPSEEK_API_KEY` stored via `mew secret set`

---

## What stays Claude-only (no exceptions)

- All tool-using tasks (Read, Write, Bash, MCP)
- Frontend / React work
- Debugging sessions
- Anything requiring conversation history or multi-turn iteration
- Any task where correctness is hard to verify without running it
