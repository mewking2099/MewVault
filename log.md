# mewvault log

## Entries

- **2026-05-26 08:58** — auto-wrap: modified log.md [auto-wrap]

- **2026-05-26** — Phase 6 complete: 44-skill agent array with Hermes-inspired delegation model, persistent SQLite memory layer (164 entries indexed), agentskills.io compliance pass, github-issue-fix skill, image-gen/notify/schedule skills, Phase 1-3 all shipped [auto-wrap]

- **2026-05-26 08:57** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 08:56** — auto-wrap: modified Project_Status.md, memory_store.py, memory.py +4 more [auto-wrap]

- **2026-05-26 08:52** — auto-wrap: modified github-issue-fix.md, plan.md, Project_Status.md +1 more [auto-wrap]

- **2026-05-26 08:47** — auto-wrap: modified image-gen.md, notify.md, schedule.md +1 more [auto-wrap]

- **2026-05-26 08:43** — auto-wrap: modified dispatcher.md, browser-use.md, manifest.yaml +9 more [auto-wrap]

- **2026-05-26 08:39** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 08:34** — auto-wrap: modified project_mewvault_backlog.md [auto-wrap]

- **2026-05-26 08:30** — auto-wrap: modified project_mewvault_backlog.md, MEMORY.md [auto-wrap]

- **2026-05-26 08:29** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 08:25** — auto-wrap: modified webapp-testing.md, mcp-builder.md, claude-api.md +15 more [auto-wrap]

- **2026-05-26 08:04** — auto-wrap: modified idea-capture.md, idea-expand.md, idea-brief.md +3 more [auto-wrap]

- **2026-05-26 07:05** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 06:30** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 06:28** — auto-wrap: modified session-start.js, Project_Status.md, log.md +3 more [auto-wrap]

- **2026-05-26 06:25** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 06:24** — auto-wrap: modified idea-hub-rules.md, manifest.yaml, manifest.yaml +8 more [auto-wrap]

- **2026-05-26 05:54** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 05:49** — auto-wrap: session ended [auto-wrap]

- **2026-05-26 05:46** — auto-wrap: session ended [auto-wrap]

- **2026-05-24 08:07** — auto-wrap: session ended [auto-wrap]

- **2026-05-24 07:01** — auto-wrap: modified log.md, Project_Status.md [auto-wrap]

- **2026-05-24** — README Getting started rewritten: replaced 8-step manual install with one-liner bootstrap + link to INSTALL.md; custom workspace path example added. Committed and pushed (a5bf22a) — 15 files, 789 insertions. Repo is live and shareable. [wrap]

- **2026-05-24 06:02** — auto-wrap: modified README.md [auto-wrap]

- **2026-05-24 06:00** — auto-wrap: modified Project_Status.md, log.md [auto-wrap]

- **2026-05-24** — Phase 5 complete + bootstrap installer shipped. Phase 5: implemented skill chaining (`_execute_chains`, `_run_chained_agent` in `agent.py`) — fires `on_complete` chain links after task-mode invocations; MCP scoping (`build_mcp_config_for_agent`, `write_temp_mcp_config` in `skill_loader.py`) — task-mode spawns pass `--mcp-config --strict-mcp-config` with agent-scoped server list; deprecated `templates/agents/` with `DEPRECATED.md`. Bootstrap: `bootstrap.sh` one-liner installer (idempotent, Mac-first), `bootstrap/rules/` bundles all 6 rule files as single source of truth (symlinked on install), `bootstrap/settings.template.json` generates workspace-correct hooks config, fresh wiki scaffold for new installs. `INSTALL.md` step-by-step guide for a blank Mac. [wrap]

- **2026-05-24 05:59** — auto-wrap: modified INSTALL.md [auto-wrap]

- **2026-05-24 05:58** — auto-wrap: modified bootstrap.sh [auto-wrap]

- **2026-05-24 05:53** — auto-wrap: modified bootstrap.sh, settings.template.json, secrets.md +5 more [auto-wrap]

- **2026-05-24 05:48** — auto-wrap: session ended [auto-wrap]

- **2026-05-24 05:46** — auto-wrap: session ended [auto-wrap]

- **2026-05-24 05:40** — auto-wrap: modified skill_loader.py, agent.py, DEPRECATED.md [auto-wrap]

- **2026-05-24 05:20** — auto-wrap: session ended [auto-wrap]

- **2026-05-23 12:41** — auto-wrap: modified log.md, Project_Status.md [auto-wrap]

- **2026-05-23** — Agent Array v2 shipped. Dispatcher-driven architecture: mew-chief classifies every prompt and spawns specialist sub-agents via Claude Code native Agent tool — no LiteLLM proxy needed, works on subscription. Built `mew/lib/skill_loader.py` (scan, parse, assemble, chain detect), rewrote `mew/commands/agent.py` (invoke/sync/fetch-skills), updated `mew/cli.py` to register `sync` and `fetch-skills` sub-commands. Created 7 agent directories under `agents/` with manifest.yaml, system-prompt.md, and skills/. Seeded 16 skill .md files across all agents. `agents/.routing-index.json` built via `mew agent sync` (7 agents, 16 skills). Dispatcher skill injected into session-start by `loadAgentDispatcher()` in hooks/session-start.js with `{{ROUTING_INDEX}}` placeholder substitution. README agent array section rewritten to match v2 architecture (dispatcher flow diagram, skill drop-in pattern, stack table corrected). [wrap]

- **2026-05-23 12:36** — auto-wrap: modified README.md [auto-wrap]

- **2026-05-23 12:34** — auto-wrap: modified Project_Status.md, manifest.yaml, manifest.yaml +26 more [auto-wrap]

- **2026-05-23 12:17** — auto-wrap: modified doobidoo.json, hook-test.tmp, ingest_code.py +310 more [auto-wrap]

- **2026-05-21** — DSaaS session 29: fixed 4 bugs in `token-export.ts` that caused brand-tokens.json to fail Figma Variables import. Bugs: variable paths remapped to Figma-canonical (`brand.primary.50` → `Colors/Primary/50`, font paths → `Font/Typescales/Header/H1/line_height`, etc.), color values converted from hex strings to srgb color objects, `$type` values fixed (`fontFamilies`/`dimension`/`other` → `string`/`number`), root restructured with `$extensions.com.figma.modeName`. Regenerated brand-tokens.json for user testing. [wrap]

- **2026-05-18** — (session 4) Updated README.md: removed outdated ChromaDB HTTP server references, replaced with accurate doobidoo/SQLite-vec + Ollama description, rewrote Step 8 with correct setup instructions, added Ollama to requirements table. Committed and pushed to main. [wrap]

- **2026-05-18** — (session 3) Wiki documentation pass. Updated `wiki/mewvault-ops-reference.md`: fixed hook trigger event names, added pre-compact row, MCP server details, full mew CLI command list (20 commands), skills section (25 skills), expanded key file locations. Created `wiki/mewvault-how-it-works.md` (was linked but missing): workspace layout diagram, full session lifecycle flow, hook architecture table, silo detection + agent identity map, MCP server details, tier gates, instinct pipeline 4-step flow, rules hierarchy, skills index. Committed + pushed to main. [wrap]

- **2026-05-18** — (session 2) Hooks sanity check: all 5 firing confirmed. Instinct pipeline: 3 pending instincts from session 1 promoted — now surface in session-start banner. Ollama confirmed as launchd service (always up). Ops reference written to `mewvault/wiki/mewvault-ops-reference.md` + queued to `mewwiki/_inbox/`. Clarified: `/wrap` is not a slash command — use `wrap up` as a prompt instead. [wrap]

- **2026-05-18** — Doobidoo full wiring + chromadb removal. Fixed doobidoo env vars (`MCP_EXTERNAL_EMBEDDING_URL/MODEL` replacing stale ChromaDB names) in `mcp-configs/doobidoo.json` and `/Jan/.mcp.json`. Discovered workspace-level `.mcp.json` was the authoritative MCP config (not user-scope); updated it directly with correct doobidoo entry (venv binary, correct env vars), removed chromadb server block. Wired all 5 hooks into `settings.local.json` (were documented in `hooks.json` but never loaded by Claude Code). Ingested 36 wiki notes (312 chunks) via `scripts/ingest_wiki.py`; ingested 413 code files from software-projects/ + game-lab/ (3588 chunks) via `scripts/ingest_code.py` — added text fallback chunker for source extensions `.ts/.tsx/.gd/.py/.cs` that `get_loader_for_file` doesn't handle. Verified semantic search works for both silos. `retrieve_memories` returns `{"memories":[...], "query":..., "count":...}`. [auto-wrap]

- **2026-05-17** — ECC integration complete (3-pillar upgrade). Token optimization: write size guard in pre-tool-use.js (warn >40k chars, block >200k chars, thresholds in `.claude/limits.json`), MAX_INJECT_CHARS cap in session-start, model routing hints, MCP tool count warning. Memory persistence: session-end now writes `~/.claude/sessions/<project>-session.tmp` (bounded summary, rotate last 10); session-start loads prior session context (capped 8k, opt-out via MEW_SESSION_CONTEXT=off). Subagent orchestration: `wiki/subagent-model-routing.md` published, `skills/plan-orchestrate/SKILL.md` bridges MewKing plans to Agent() calls. 25 skills added from ECC/superpowers/anthropics/trailofbits/gsd/shadcn repos and globally symlinked to `~/.claude/skills/`; `mew harness install` updated to auto-run symlinks. Conflict audit: `verification-before-completion` merged into `verification-loop`, duplicate removed. DSaaS docs.tsx rewrite pushed. [auto-wrap]

- **2026-05-13** — DSaaS session 4: Phase 2 architecture decision (Radix UI + CSS vars + `tailwindcss-animate`), 17-component plan written and MewKing-approved, `@dsaas/react-ui` package scaffolded (vite lib build, Vitest + RTL, TenantProvider, 9 Radix primitives). Next: Step 2 — Storybook scaffold. [auto-wrap]

- **2026-05-12** — Replaced 7 slash commands with conversational triggers embedded in `session-start.js` `UserPromptSubmit` hook; README expanded with technical internals (token budget, vector DBs, instinct system, agent array), example sessions, and trigger reference; force-pushed to remote. [auto-wrap]

- **2026-05-12** — MewWiki v1.0 shipped (Phases 1–8 complete). `mew wiki init` bootstraps full Obsidian vault; `mew wiki sync` idempotent silo→wiki sync with git diff engine; 7 slash commands in `.claude/commands/` (/standup, /project-new, /dump, /wrap-up, /meeting-prep, /meeting-capture, /ingest); session-start now surfaces Brain/North Star focus + inbox count + stale project alerts; session-end auto-runs wiki sync + writes Brain/Memories entry; pre-tool-use blocks direct mewwiki writes. pdvault audited (empty), decommissioned, and deleted. mewwiki live at /Jan/mewwiki with neustring-copilot fully synced. [auto-wrap]

- **2026-05-10 — v2-mewharness implementation complete** — closed all 6 outstanding gaps from the plan audit: `hooks/hooks.json` (canonical source, harness.py now loads from it, installs resolved copy to `.claude/hooks/`); Phase 4 vector store config (`mcp-configs/` — memory-mcp, doobidoo, chromadb) + session-start/end integration with graceful degradation; Phase 5 `mew validate --slim`, `mew harness status --verbose`, cache-optimization comment in session-start, `max_tokens: 300` on mew-archivist; Phase 6 `mew sync --pr` (gh CLI), GitHub issues step in session-start, Figma Phase 4 section in mew-designer, design token directive in promote.py; Phase 7 `templates/commands/` deleted, help_cmd.py updated to v2.0 with hooks-are-automatic note. [auto-wrap]

