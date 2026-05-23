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

## Step 2 — Route

Match the request to an agent using the routing index. If a match is found:

1. Announce: `→ Routing to <agent-name> (<model>)…`
2. Read the agent's system-prompt and matched skills from the routing index.
3. Spawn a sub-agent using the Agent tool:
   - `subagent_type`: the agent name (e.g. `mew-planner`)
   - `model`: the agent's model alias (opus / sonnet / haiku)
   - Include the assembled context (system-prompt + skills) in the prompt
4. Return the sub-agent's result to the user.

## Step 3 — Ambiguous requests

If the request could match multiple agents, pick the most specific one.
If genuinely unclear, ask **one** clarifying question before routing.

## Routing index

The routing index is injected below by session-start.js at session start.
Use it to determine which agent handles which triggers.

{{ROUTING_INDEX}}
