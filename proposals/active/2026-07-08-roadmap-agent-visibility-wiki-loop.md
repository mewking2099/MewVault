# Proposal — agent visibility, wiki retrieval loop, dashboard (queued 2026-07-08)

Status: IMPLEMENTED 2026-07-08 (all 5 items). Restart Claude session to activate the new hooks.

## 1. Agent dispatch ledger + model gate + `mew agent status`

Problem: no evidence agents are dispatched at all; silent Sonnet fallback undetectable.

- PreToolUse hook entry with matcher `Task`: append `{agent, model, description, ts}` to `.claude/agent-dispatches.jsonl`; block (exit 2) mew-agent dispatches missing the `model` param (enforces the CLAUDE.md model table).
- `SubagentStop` hook: log completion + duration to the same ledger.
- `mew agent status`: recent dispatches, running vs completed, model actually used.

## 2. MewWiki retrieval loop (closes the Karpathy loop)

Problem: mewwiki is write-mostly; decisions/gotchas never resurface in sessions.

- Run `scripts/ingest_wiki.py` automatically at the end of `mew wiki sync`.
- Session-start `## Relevant Context (semantic)` pulls top-k Decisions/Gotchas for the active project.
- Periodic distillation: mew-learner consolidates `_inbox/` + raw notes into Knowledge pages, dedupes stale facts.

## 3. `mew dashboard`

Self-contained HTML (no server): all projects with phase/next-action/staleness from Project_Status.md, doctor health from `.claude/doctor-status.json`, agent activity from the dispatch ledger. Optional: mirror agent feed into mewwiki for Obsidian Bases instead.

## 4. Usage telemetry

`mew usage --report` parsing Claude Code transcript JSONL (tokens/session, cache-hit ratio); doctor check for abnormal burn rate — would have caught Headroom within a day.

## 5. Weekly review trigger

`weekly review` conversational trigger: mew-archivist digests the week's logs into Brain/Memories + stale-project nudges.

Principle from the July audit: no new always-on services or request-rewriting layers — the failure mode of this vault is extra layers, not missing features.
