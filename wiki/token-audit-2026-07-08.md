# MewVault token audit — 2026-07-08

Audit of the harness after the Sonnet 4.6 + Headroom update caused context-limit hits in single chats and rapid usage-limit burn on Claude Pro.

## Verdict

The harness core is healthy. The regression came almost entirely from the Headroom compression layer, not from Sonnet 4.6 and not from MewVault's own design. Full analysis: `wiki/headroom-postmortem.md`.

## What's working (unchanged)

Session-start injection design (full block on first prompt only, 3k-token budget, cache-aware ordering, per-silo whitelists), tier gates, secrets guardian, mewwiki sync, pre-compact snapshots, and the instinct concept. These are all sound and were kept.

## Findings and fixes applied

**1. Headroom broke prompt caching (root cause of usage burn).** The proxy compressed system and user messages on every request, rewriting the prompt prefix and invalidating Anthropic's cache (cache reads ≈ 0.1x input cost). Net effect: every turn re-billed the whole conversation as uncached input. Fixed: `start-headroom.sh` now refuses to start without `MEW_HEADROOM_FORCE=1`, `mcp-configs/headroom.json` marked disabled, postmortem written. Manual host steps: unload the launchd daemon and remove `ANTHROPIC_BASE_URL` (see postmortem).

**2. CCR compress/retrieve inflated context (root cause of context-limit hits).** Claude Code context is append-only; compressing already-read content adds a copy instead of freeing anything. Fixed: removed the `[headroom]` nudge from `post-tool-use.js` (it was also dead code — PostToolUse stdout never reaches the model).

**3. `mew harness install` ignored per-hook matchers.** It hardcoded matcher `""`, so PreToolUse/PostToolUse node processes spawned on every tool call including Read/Grep. Fixed in `harness.py`, `bootstrap/settings.template.json`, and the live `.claude/settings.json` (backup: `settings.json.bak-audit`).

**4. Instinct pipeline runaway.** 942 pending candidates from the 2-writes-in-60s heuristic, which fires on normal iterative editing. Fixed: now requires 3+ rapid rewrites, dedupes per silo+topic, caps the queue at 50, and prunes signal-tracking entries older than 24h. The 942 old candidates were archived to `instincts/_archive/pending-2026-07-08/`.

**5. Webflow MCP loaded globally.** Its full tool schema entered every session in every silo. Fixed: moved from `Jan/.mcp.json` (backup: `.mcp.json.bak-audit`) to `software-projects/golddiamondclub/.mcp.json`.

**6. Session-start truncation severed the Session Card.** The hard substring cut at budget removed whatever came last. Fixed: over-budget briefs now drop whole low-priority sections (semantic recall, mew memory, prior session) first.

**7. CLAUDE.md contradiction.** Agent dispatch example said `model: "opus" ← required, always` while the table said `claude-sonnet-4-6`. Fixed.

## New: `mew doctor` — automated health monitor

`mew/commands/doctor.py`, registered in the CLI. Nine checks, all token-health oriented: cache_safety (detects any rewriting proxy or compression env — the Headroom class of failure can never silently return), hooks_registered, hook_matchers, injection_size (actually runs session-start.js and measures output against budget), instinct_queue, signal_file, mcp_surface, ollama, index_freshness.

Auto-run: `session-start.js` spawns `mew doctor --quiet --notify` detached on the first prompt of each session. Problems produce a macOS notification and are cached to `.claude/doctor-status.json`; the next session start injects a `## Vault Health` section telling Claude to surface the issues. Manual: `mew doctor`, `mew doctor --json`, exit codes 0/1/2 for ok/warn/fail.

## Verification performed

`node --check` on both modified hooks; session-start probe still emits ~3,000 tokens on first prompt and only trigger text afterward; `python ast` parse on all modified Python; full `mew doctor` run passed 8/9 checks (Ollama unreachable only because the audit ran in a sandbox).
