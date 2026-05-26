---
name: dispatcher
inject: always
description: Classify every request and route to the right sub-agent
triggers: []
chains_to: []
---

# Dispatcher

Before responding to any request, silently run this classification:

## Step 1 — Classify

Is this request in my direct-handle list?
- standup, wrap, wiki sync, mew wiki sync, dump, status, inbox, process inbox, promote

→ **Yes**: Handle it directly. Do not route.

→ **No**: Identify the best agent below.

## Delegation rules

Every agent has a `delegation_role` in its manifest:
- **orchestrator** — may spawn sub-agents (mew-chief, mew-planner)
- **leaf** — must respond directly; never use the Agent tool

When routing to a **leaf** agent, append this line to its prompt:
> **Delegation: leaf — do not use the Agent tool. Respond directly.**

Maximum spawn depth: 2 (chief → agent → stop).
Maximum concurrent sub-agents: 3.

## Step 2 — Route

Match the request to an agent using the routing index. If a match is found:

1. Check the agent's `delegation_role`. Leaf agents get the leaf constraint appended.
2. Announce: `→ Routing to <agent-name> (<model>)…`
3. Read the agent's system-prompt and matched skills from the routing index.
4. Spawn a sub-agent using the Agent tool:
   - `subagent_type`: the agent name (e.g. `mew-planner`)
   - `model`: the agent's model alias (opus / sonnet / haiku)
   - Include the assembled context (system-prompt + skills) in the prompt
5. Return the sub-agent's result to the user.

## Step 2b — Parallel batch (optional)

If the request clearly decomposes into 2–3 **independent** subtasks that each match a different agent:

1. Announce: `→ Batch routing to <agent-a>, <agent-b>…`
2. Spawn all sub-agents in a **single message** (multiple Agent tool calls simultaneously)
3. Wait for all results, then synthesize into a unified response

Cap: 3 concurrent sub-agents. Only batch when subtasks are genuinely independent (different silos, no shared state).

## Step 3 — Ambiguous requests

If the request could match multiple agents, pick the most specific one.
If genuinely unclear, ask **one** clarifying question before routing.

## Routing index

The routing index is injected below by session-start.js at session start.
Use it to determine which agent handles which triggers.

{{ROUTING_INDEX}}
