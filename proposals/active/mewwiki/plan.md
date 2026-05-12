# MewWiki — MewKing Plan

**Tier**: MewKing  
**Created**: 2026-05-12  
**Status**: APPROVED  
**Replaces**: `pdvault/` (deleted after migration)  
**Entry point**: Claude Code opened in `mewvault/` — single terminal window for all work

---

## North Star

One terminal window. Open Claude Code in `mewvault/`. Do everything — standup, new project, coding, capturing, wrapping — without switching directories. MewWiki is an Obsidian vault that updates automatically in the background. You browse it. You never work from it.

---

## Success Criteria

When this plan is complete:

1. `cd /Jan/mewvault && claude` → SessionStart fires → standup brief available, all active projects visible.
2. `/standup` → reads all silos + mewwiki Brain + Google Calendar → morning brief in <3s.
3. `new project rate-calc --stack next` → silo scaffolded, mewwiki mirror created, linked in Bases dashboard, all in one command.
4. `/dump <content>` → classifies and routes to correct silo wiki or mewwiki Operations in <1s.
5. `mew wiki sync` → reads all silo logs + wiki pages changed since last sync → mewwiki updated, no duplicates, idempotent.
6. `/wrap-up` → session log written, `mew wiki sync` runs, Obsidian is current before session closes.
7. Open Obsidian on `mewwiki/` → Active Projects Bases dashboard shows all silos with correct status.
8. `mew wiki init` → bootstraps a fresh mewwiki at a given path from scratch.
9. `/meeting-prep <topic>` → reads mewwiki People + Google Calendar MCP → meeting brief with agenda.
10. `pdvault/` deleted → nothing breaks, no orphaned references.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  mewvault/  — Claude Code home (single window)  │
│                                                 │
│  Slash commands  ←→  mew CLI  ←→  Hooks         │
└───────────┬─────────────────────────────────────┘
            │ reads / writes
    ┌───────┴────────────────────────────────────┐
    │  Project silos                             │
    │  software-projects/  game-lab/             │
    │  design-studio/      mewvault/             │
    └───────┬────────────────────────────────────┘
            │ mew wiki sync (on session end)
    ┌───────▼────────────────────────────────────┐
    │  mewwiki/  — Obsidian vault (read layer)   │
    │  You browse this. Claude writes to it.     │
    │                         ↑                  │
    │         Google Calendar / GitHub / Teams   │
    └────────────────────────────────────────────┘
```

**Key principle**: mewwiki has no CLAUDE.md, no hooks, no slash commands of its own. It is a pure output — a git repo written by `mew wiki sync` and read in Obsidian.

---

## What Gets Built

### Phase 1 — MewWiki Vault Scaffold

**`mew wiki init`** — bootstraps the vault.

Creates:
```
mewwiki/
├── CLAUDE.md                 ← read-only reference (written by mew, not edited)
├── README.md
├── .gitignore
├── .obsidian/                ← pre-configured (core plugins, appearance)
│
├── Home.md                   ← entry point with embedded Bases links
│
├── Projects/                 ← silo mirrors
│   └── _archive/
│
├── Knowledge/                ← cross-silo concept library
│   ├── index.md
│   ├── raw/                  ← immutable source docs
│   └── concepts/
│
├── Operations/               ← daily work layer
│   ├── People/
│   ├── Meetings/
│   │   └── _inbox/
│   ├── Decisions/
│   └── Ideas/
│       └── inbox.md
│
├── Integrations/             ← external data (written by sync, not manually)
│   ├── Calendar/
│   ├── GitHub/
│   └── Teams/                ← future
│
├── Brain/                    ← Claude's operational memory (read at SessionStart)
│   ├── North Star.md         ← active focus + project list
│   ├── Memories.md           ← topic index
│   ├── Patterns.md
│   └── Gotchas.md
│
├── _inbox/                   ← auto-drop zone from silo syncs
│
├── Templates/                ← 8 note templates
│
└── Bases/                    ← 6 live dashboards
    ├── Active Projects.base
    ├── Stale Projects.base
    ├── Decision Log.base
    ├── Idea Pipeline.base
    ├── Knowledge Index.base
    └── People Directory.base
```

Deliverable: `mew/commands/wiki.py` with `wiki init` subcommand.

---

### Phase 2 — Sync Engine

**`mew wiki sync`** — the core mechanic. Idempotent, safe to run repeatedly.

Algorithm:
1. Read `mewwiki/.sync-manifest.json` → last-synced commit SHA per silo
2. For each silo, `git log <last-sha>..HEAD --name-only` → changed files
3. For each changed `log.md` → append new entries to `mewwiki/Projects/<slug>/log.md`
4. For each changed `Project_Status.md` → rewrite `mewwiki/Projects/<slug>/index.md` fields
5. For each new `wiki/<page>.md` → copy to `mewwiki/_inbox/<silo>-<page>.md` (not silently overwrite Knowledge — user reviews first)
6. Update `.sync-manifest.json` with new HEAD SHAs
7. `git add -A && git commit -m "sync: <timestamp>"` inside mewwiki

Deliverable: `mew wiki sync` subcommand + `.sync-manifest.json` schema.

---

### Phase 3 — mewvault Slash Commands

All commands run from mewvault. Implemented as skills in `mewvault/skills/` (already the pattern from v2.0).

**`/standup`**
- Reads `mewwiki/Brain/North Star.md`
- Reads each active project's `Project_Status.md` from silos
- Reads `mewwiki/_inbox/` count
- Calls Google Calendar MCP → today's events
- Calls `gh pr list` → open PRs per silo
- Outputs: morning brief with priorities, meetings, inbox, PRs

**`/project-new <slug>`**
- Interactive: asks name, north star, stack, blockers, tier
- Runs `mew new <slug> --silo <silo>` → scaffolds silo
- Creates `mewwiki/Projects/<slug>/index.md` mirror immediately (no waiting for sync)
- Appends project to `mewwiki/Brain/North Star.md` under Active Projects
- Links from `mewwiki/Home.md`

**`/dump <content>`**
- Classifies content: idea / decision / meeting note / person observation / api note / gotcha
- Routes to correct location:
  - idea → `mewwiki/Operations/Ideas/inbox.md`
  - decision → `mewwiki/Operations/Decisions/<project>-<slug>.md`
  - person obs → `mewwiki/Operations/People/<Name>.md`
  - api note / gotcha → current silo's `wiki/`
- Asks for confirmation before writing
- Every routed note gets a `[[wikilink]]` back to its source project

**`/wrap-up`**
- Writes session log entry to current silo's `log.md`
- Runs `mew wiki sync`
- Suggests commit message
- Checks for orphaned notes (new notes without inbound links)
- Outputs session summary

**`/meeting-prep <topic>`**
- Reads `mewwiki/Operations/People/<attendees>.md`
- Reads most recent meeting note for this topic/person
- Calls Google Calendar MCP → finds upcoming meeting
- Outputs: attendee context, open items from last meeting, suggested agenda

**`/meeting-capture`**
- Interactive: who, what was decided, any action items
- Writes to `mewwiki/Operations/Meetings/YYYY-MM/<slug>.md`
- Extracts decisions → `mewwiki/Operations/Decisions/`
- Extracts person observations → appends to People notes
- Appends to relevant project `wiki/`

**`/ingest <path>`**
- Reads source doc from `raw/`
- Discusses proposed concept pages before writing (Karpathy rule)
- Writes to silo `wiki/` + queues for mewwiki Knowledge sync
- Appends to `mewwiki/Knowledge/index.md`

Deliverables: 7 skill files in `mewvault/skills/`.

---

### Phase 4 — Hook Updates

Extend existing MewHarness hooks (no new hooks — just new logic in existing ones).

**SessionStart** — add:
- Read `mewwiki/Brain/North Star.md` for active project list
- Read `mewwiki/_inbox/` count → surface in orientation brief
- Read stale projects from mewwiki Bases manifest (projects idle >14 days)

**SessionEnd** — add:
- Auto-run `mew wiki sync` before closing
- Write session summary to mewwiki Brain if >3 notes touched

**PreToolUse** — add:
- Intercept writes to `mewwiki/` directly — block with message "write to mewwiki via mew wiki sync, not directly"

Deliverables: updated `hooks/session-start.js`, `hooks/session-end.js`, `hooks/pre-tool-use.js`.

---

### Phase 5 — Obsidian Configuration

Pre-configure `.obsidian/` so the vault is ready on first open.

- **Core plugins enabled**: Bases, Templates, Graph, Backlinks, Outgoing links, Daily notes (off by default)
- **Bases dashboards**: 6 `.base` files with queries wired to vault structure
- **Templates**: 8 templates pre-populated
- **Graph groups**: colour-code by folder (Projects = navy, Knowledge = lime, Operations = gray)
- **Hotkeys**: none changed from defaults

Deliverable: `.obsidian/` config committed to mewwiki repo.

---

### Phase 6 — Google Calendar Integration

Uses the existing Figma MCP pattern — connects via Claude Code's MCP connector.

**Setup** (one-time, documented in mewwiki/README.md):
1. Run `/mcp` in Claude Code
2. Select Google Calendar
3. Authorize in browser

**Wired into**:
- `/standup` → today's meetings
- `/meeting-prep` → auto-detect next meeting
- `/wrap-up` → note any meetings captured today

No calendar data is written to mewwiki unless explicitly captured via `/meeting-capture`.

Deliverable: documented setup in README + calendar MCP calls in skill files.

---

### Phase 7 — GitHub Integration

Uses existing `gh` CLI (already available).

**Wired into**:
- `/standup` → open PRs per active silo (`gh pr list --repo <repo>`)
- `/project-new` → optionally create GitHub repo
- `/wrap-up` → suggest `git commit` + `git push`

Deliverable: `gh` calls in skill files where noted above.

---

### Phase 8 — pdvault Migration + Deletion

1. Export worth-keeping content from `pdvault/Builder/Brain/` → `mewwiki/Brain/`
2. Export `pdvault/Builder/Knowledge/concepts/` → `mewwiki/Knowledge/concepts/`
3. Export `pdvault/Builder/People/` → `mewwiki/Operations/People/`
4. Verify no broken wikilinks in mewwiki after import
5. `rm -rf /Jan/pdvault` — confirmed by user before executing
6. Remove any pdvault references from mewvault CLAUDE.md and rules

Deliverable: migration checklist + user confirmation before deletion.

---

## Build Order

| Phase | Deliverable | Complexity |
|---|---|---|
| 1 | `mew wiki init` — vault scaffold | Medium |
| 2 | `mew wiki sync` — sync engine | High |
| 3 | 7 slash commands (skills) | Medium |
| 4 | Hook updates | Low |
| 5 | Obsidian config | Low |
| 6 | Google Calendar wiring | Low (MCP already exists) |
| 7 | GitHub wiring | Low (gh CLI already exists) |
| 8 | pdvault migration + deletion | Low (manual + confirm) |

Phases 1–2 are the load-bearing work. Phases 3–8 extend from that foundation.

---

## What Stays Unchanged

- All 15 existing `mew` commands
- Python/argparse/pyyaml stack
- `Project_Status.md` schema
- Secrets model (`mewvault/secrets/`)
- Silo model and tier system
- MewHarness hook runtime
- Agent array (mew-archivist, mew-designer, etc.)
- Template system for new projects

---

## Risks

| Risk | Mitigation |
|---|---|
| Sync overwrites manually edited mewwiki content | Sync only writes to `_inbox/` and Project mirrors — Knowledge/Operations never auto-overwritten |
| pdvault content lost on deletion | Phase 8 is a checklist migration — user confirms before `rm -rf` |
| mewwiki repo grows large with binary attachments | `.gitignore` excludes images/PDFs by default; raw docs stay in silos |
| Calendar MCP not connected | `/standup` and `/meeting-prep` degrade gracefully — skip calendar section with a note |

---

## Out of Scope (this plan)

- Microsoft Teams MCP (future — wired in Phase 6 slot when available)
- Figma-to-mewwiki design decision sync (separate plan after this ships)
- Mobile access to mewwiki (Obsidian Sync — user's choice, not built here)
- AI-powered weekly synthesis (`/weekly` command — Phase 2 of mewwiki)
