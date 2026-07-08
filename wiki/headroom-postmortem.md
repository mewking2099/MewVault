# Headroom postmortem — why the compression layer burned tokens

**Date:** 2026-07-08 · **Status:** Headroom disabled for Claude Code · **Trigger:** token audit after usage-limit and context-limit problems appeared following the Sonnet 4.6 + Headroom update.

## Symptom

After adding Headroom as a compression layer, sessions started hitting the context limit in a single chat and the Pro plan usage limit drained far faster than before, despite Headroom advertising 60–95% token reduction.

## Root cause 1 — prompt-cache destruction (usage burn)

The proxy ran with `HEADROOM_COMPRESS_USER_MESSAGES=true` and `HEADROOM_COMPRESS_SYSTEM_MESSAGES=true`, intercepting every Claude Code request via `ANTHROPIC_BASE_URL=http://localhost:8787` (launchd daemon, `KeepAlive`, `RunAtLoad`).

Anthropic prompt caching only applies to a byte-identical prompt prefix. Cache reads cost ~0.1x normal input tokens; Claude Code is engineered so the system prompt and conversation history hit the cache on every turn. Compressing the system prompt and prior user messages rewrites that prefix on every request, so every turn paid full uncached input for the entire conversation plus 1.25x cache re-creation. Compression saved perhaps 40–60% of raw tokens while forfeiting a ~90% cache discount — a large net loss. On the API this shows up as cost; on a subscription it shows up as the usage limit draining several times faster.

## Root cause 2 — CCR inflation (context limit)

Claude Code's context window is append-only until `/compact` or auto-compact. Calling `headroom_compress` on already-read file content does not free anything: the original tool result stays in context and the compressed copy is appended on top; a later `headroom_retrieve` appends the original a third time. The `post-tool-use.js` nudge that told Claude to "compress this content now to free context" made this worse — and was dead code anyway, since PostToolUse stdout never reaches the model.

## Rule of thumb going forward

On Claude Code with a subscription, never put a request-rewriting proxy between the CLI and the API. Optimize by injecting less (session-start budget, silo whitelists, scoped MCP servers) and keeping the prompt prefix stable, not by transforming it. Compression layers only make sense for API-billed, cache-free pipelines (e.g. LiteLLM dispatch to DeepSeek).

## What was changed

Headroom launchd daemon and `ANTHROPIC_BASE_URL` removed from the launch path (manual step on host); `start-headroom.sh` now exits unless `MEW_HEADROOM_FORCE=1`; `mcp-configs/headroom.json` marked disabled; the post-tool-use nudge removed; `mew doctor` now fails the `cache_safety` check if any rewriting proxy or compression env var is ever detected again.
