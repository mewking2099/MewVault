# mewvault log

## Entries

- **2026-05-12** — Replaced 7 slash commands with conversational triggers embedded in `session-start.js` `UserPromptSubmit` hook; README expanded with technical internals (token budget, vector DBs, instinct system, agent array), example sessions, and trigger reference; force-pushed to remote. [auto-wrap]

- **2026-05-12** — MewWiki v1.0 shipped (Phases 1–8 complete). `mew wiki init` bootstraps full Obsidian vault; `mew wiki sync` idempotent silo→wiki sync with git diff engine; 7 slash commands in `.claude/commands/` (/standup, /project-new, /dump, /wrap-up, /meeting-prep, /meeting-capture, /ingest); session-start now surfaces Brain/North Star focus + inbox count + stale project alerts; session-end auto-runs wiki sync + writes Brain/Memories entry; pre-tool-use blocks direct mewwiki writes. pdvault audited (empty), decommissioned, and deleted. mewwiki live at /Jan/mewwiki with neustring-copilot fully synced. [auto-wrap]

- **2026-05-10 — v2-mewharness implementation complete** — closed all 6 outstanding gaps from the plan audit: `hooks/hooks.json` (canonical source, harness.py now loads from it, installs resolved copy to `.claude/hooks/`); Phase 4 vector store config (`mcp-configs/` — memory-mcp, doobidoo, chromadb) + session-start/end integration with graceful degradation; Phase 5 `mew validate --slim`, `mew harness status --verbose`, cache-optimization comment in session-start, `max_tokens: 300` on mew-archivist; Phase 6 `mew sync --pr` (gh CLI), GitHub issues step in session-start, Figma Phase 4 section in mew-designer, design token directive in promote.py; Phase 7 `templates/commands/` deleted, help_cmd.py updated to v2.0 with hooks-are-automatic note. [auto-wrap]

