# ISSUE: Agent model routing is not enforced — all agents run on Sonnet 4.6

**Severity: Critical**
**Discovered: 2026-07-03**
**Status: Partially resolved — Claude-family agents fixed via .claude/agents/ (2026-07-03); DeepSeek agents (mew-coder-simple, mew-coder-reason) still pending Option B**

---

## What's broken

Every agent in `agents/*/manifest.yaml` specifies a `model:` field. None of those model assignments are actually enforced. When any agent is spawned (via the Agent tool, mew-chief dispatch, or any subagent call), the model used is always the session's active model — currently **Claude Sonnet 4.6** — regardless of what the manifest says.

## Affected agents and their intended models

| Agent | Manifest model | Actual model used | Gap |
|---|---|---|---|
| fable | claude-fable-5 | Sonnet 4.6 | ❌ Wrong model entirely |
| mew-coder-simple | deepseek-v3 | Sonnet 4.6 | ❌ Wrong model entirely |
| mew-coder-reason | deepseek-r1 | Sonnet 4.6 | ❌ Wrong model entirely |
| mew-chief | claude-sonnet-5 | Sonnet 4.6 | ⚠ Close but unversioned |
| mew-coder | claude-sonnet-5 | Sonnet 4.6 | ⚠ Close but unversioned |
| mew-learner | claude-haiku-4-5 | Sonnet 4.6 | ❌ Wrong model (should be cheaper/faster) |
| mew-designer | claude-sonnet-5 | Sonnet 4.6 | ⚠ Close but unversioned |

## Why it's broken

The `Agent` tool in Claude Code accepts `model: "sonnet" | "opus" | "haiku"` — three shorthand values mapping to the Claude family. It does **not** accept arbitrary model IDs (`claude-fable-5`, `deepseek-v3`, etc.).

The `manifest.yaml` model field is documentation only — no code reads it at dispatch time and enforces it.

The LiteLLM proxy on `:4000` (set up in a prior session) **can** route to DeepSeek models, but only if explicitly called via `mew dispatch`. The Agent tool flow bypasses it entirely.

## What this means in practice

- `$fable audit` runs on Sonnet 4.6, not Fable 5. No extended context. No multi-day reasoning.
- `mew-coder-simple` (meant to be cheap/fast DeepSeek V3 for routine code tasks) costs Sonnet 4.6 rates instead.
- `mew-learner` (meant to be Haiku for lightweight tasks) runs on Sonnet unnecessarily.
- The entire agent cost optimisation strategy is void.
- The agent array's value proposition (right model for the right task) does not exist yet.

## What a fix looks like

Three options, in order of feasibility:

### Option A — Enforce via Agent tool `model` param (partial fix, Claude-only)
When spawning Claude agents, explicitly pass the correct `model` shorthand in the Agent tool call:
- `mew-learner` → `model: "haiku"`
- `fable` → `model: "opus"` (closest available to Fable 5 in the shorthand system)
- All others → `model: "sonnet"`

**Limitation:** Still can't route to DeepSeek or Fable 5 by model ID via Agent tool.

### Option B — `mew dispatch` for non-Claude models (full fix for DeepSeek)
For `mew-coder-simple` and `mew-coder-reason`: use the existing LiteLLM proxy at `:4000`. When the routing index identifies a DeepSeek agent, call `mew dispatch <agent> <task>` instead of the Agent tool. This already exists but is not wired into the dispatch flow.

**Limitation:** Requires the LiteLLM proxy to be running. Doesn't help with Fable 5.

### Option C — Custom SDK dispatch layer (full fix, all models)
Build a `mew agent run <agent-name> "<prompt>"` command in `mew/commands/agent_run.py` that:
1. Reads `agents/<name>/manifest.yaml` to get the model ID
2. Routes Claude models → Anthropic API directly with the exact model ID
3. Routes DeepSeek models → LiteLLM proxy
4. Returns the response for use in the session

This is the correct long-term fix. It's a MewKing-tier change.

## Immediate workaround

Until fixed: when invoking an agent manually, note what model it's supposed to use and switch Claude Code's model before starting the session if it matters (e.g., switch to Fable 5 in Claude Code UI before running `$fable audit`).

## Fix priority

**Fix before:** Agent array is marketed as "right model for the right task"
**Fix after:** fable agent was added (2026-07-03), making the gap obvious
**Effort estimate:** Option A = S (1 session), Option B = M (1 session), Option C = XL (MewKing proposal required)

## Recommended approach

Do Option A immediately (Pounce — just fix the Agent tool calls to pass the right model shorthand). Then plan Option C as a MewKing proposal when capacity allows.
