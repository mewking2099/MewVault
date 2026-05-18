# MewVault

A federated AI workspace manager built for Claude Code. One terminal window. Everything flows through `mewvault/` — your projects, your knowledge, your daily rhythm.

---

## What it is

MewVault organises work into independent git **silos**, enforces planning gates before code is written, and wires Claude Code hooks to inject context automatically at the start of every session.

**MewWiki** is the read layer — an Obsidian vault that stays current with your silos automatically. You browse it. Claude writes to it at session end via `mew wiki sync`. You never work from it directly.

```
workspace-root/
  mewwiki/              # Obsidian vault — auto-updated, read in Obsidian
  mewvault/             # This repo — CLI, hooks, agents
  software-projects/    # Code projects (Next.js, Astro, SvelteKit)
  design-studio/        # UX and design projects (Figma-integrated)
  game-lab/             # Godot games and experiments
  wiki/                 # Knowledge base and learning tracks
```

---

## Daily workflow

### Morning — start the day

```
cd ~/Jan/mewvault
claude
```

Claude Code opens. The session-start hook fires automatically and injects:
- Your active project status and current phase
- MewWiki inbox count (notes queued for review in Obsidian)
- Any projects idle for 14+ days
- Promoted instincts from past sessions

Then say:

> **standup**

Claude reads your Brain/North Star, all active Project_Status.md files, and your open PRs. You get a morning brief in one block — priorities, calendar (if Google Calendar is connected), inbox, PRs.

---

### During the day — working on a project

**Start new work in a silo:**

> **new project rate-calc**

Claude asks: name, silo, stack, north star, tier. Runs `mew new`, scaffolds the silo folder, creates a mewwiki mirror in `Projects/rate-calc/` immediately.

**Capture something mid-session:**

> **dump — we decided to use Supabase instead of Prisma for this project**

Claude classifies it (decision, idea, person note, API gotcha, etc.), proposes where it goes, and asks for confirmation before writing.

**Distil a spec document:**

> **ingest raw/spec.pdf**

Claude proposes a set of concept pages to extract, waits for your approval, then writes them to `wiki/`. They flow to mewwiki on the next sync.

---

### End of day — wrap up

> **wrap up**

Claude:
1. Writes a session log entry to the active project's `log.md`
2. Updates `Project_Status.md` with `last_session` and `next_action`
3. Runs `mew wiki sync` — silos → mewwiki, committed automatically
4. Flags any unrouted inbox items
5. Suggests a git commit message

Then open Obsidian. Your projects, decisions, and wiki pages are current.

---

### Other triggers you'll use

| Say this | What happens |
|---|---|
| **meeting prep vodafone** | Loads attendee profiles + last meeting notes + suggests agenda |
| **capture the meeting** | Extracts decisions + action items → files in Operations/ |
| **ingest raw/spec.pdf** | Discusses concept pages with you before writing |
| **standup** | Morning brief — projects, inbox, PRs, calendar |
| **wrap up** | Session end — log, sync, commit suggestion |

All triggers work as plain conversational sentences — no slash commands or special syntax.

---

## Example sessions

### A typical morning

```
You:    standup

Claude: ## Standup — 2026-05-12

        ### Focus
        Ship the Supabase auth flow for neustring-copilot (Phase 3)

        ### Active Projects
        | Project            | Phase    | Next action              | Blockers |
        |--------------------|----------|--------------------------|----------|
        | neustring-copilot  | phase-3  | wire up OAuth callback   | —        |
        | brand-refresh      | research | review Figma moodboard   | —        |

        ### Today
        10:00 Vodafone sync (Sarah Chen, Mike Ross)
        15:30 1:1 with Jamie

        ### Open PRs
        - #14 feat: supabase schema migration [draft]

        ### Inbox
        3 item(s) in mewwiki/_inbox/ waiting for review.
        neustring-copilot-auth-notes.md, brand-refresh-palette.md, vodafone-notes.md
```

---

### Mid-session capture

```
You:    dump — the Vodafone team confirmed they want a white-label version,
        not a separate product. decision made in the 10am call.

Claude: Type:    decision
        Route:   mewwiki/Operations/Decisions/vodafone-white-label.md
        Title:   White-label over separate product — Vodafone
        Project: neustring-copilot

        Content preview:
        We decided to build a white-label version of neustring-copilot for
        Vodafone rather than a separate product. Confirmed in 10am sync
        2026-05-12 with Sarah Chen and Mike Ross.

        Confirm? [y/n/reclassify]

You:    y

Claude: Written: mewwiki/Operations/Decisions/vodafone-white-label.md
        Will appear in Obsidian immediately.
```

---

### Starting a new project

```
You:    new project mew-billing

Claude: 1. Slug: mew-billing ✓
        2. Full name?
        3. Silo: software, design, or game?
        4. Stack: next, astro, or sveltekit?
        5. North star (one sentence — what does "done" look like)?
        6. Tier: pounce / stalk / mewking?

You:    MewVault Billing, software, next, users can subscribe and manage
        billing from the dashboard, stalk

Claude: Scaffolding...

        Project created: mew-billing
        Silo:       software-projects/mew-billing/
        Wiki mirror: mewwiki/Projects/mew-billing/
        North Star updated.
```

---

### Wrapping up

```
You:    wrap up

Claude: What happened this session?

You:    wired up the Supabase OAuth callback, fixed the redirect loop,
        wrote tests for the auth middleware

Claude: Log entry written → neustring-copilot/log.md
        Project_Status.md updated: last_session 2026-05-12, next_action: deploy to staging
        Wiki sync: 1 project updated (neustring-copilot)
        Inbox check: no unrouted items

        Commit suggestion:
        feat: wire Supabase OAuth callback and fix redirect loop

        Run: git add ... && git commit -m "feat: wire Supabase OAuth callback and fix redirect loop"
```

---

## How it works — under the hood

### Hook runtime (MewHarness)

Five Claude Code lifecycle hooks fire automatically. You install them once with `mew harness install` and never think about them again.

| Hook | Event | What it does |
|---|---|---|
| `session-start.js` | `UserPromptSubmit` | Injects vault rules, project status, Brain brief, instincts, semantic context — and detects conversational triggers |
| `session-end.js` | `Stop` | Writes auto-wrap log entry, runs `mew wiki sync`, appends to Brain/Memories, indexes to vector store |
| `pre-tool-use.js` | `PreToolUse` | MewKing gate, secrets guard, `raw/` lock, mewwiki write guard, TDD warning |
| `post-tool-use.js` | `PostToolUse` | Accumulates session activity, detects correction signals for instinct candidates |
| `pre-compact.js` | `PreCompact` | Semantic context snapshot before conversation compresses |

### Token budget

The `UserPromptSubmit` hook prepends a context block to every prompt. To keep it from ballooning:

- A hard cap of **6,000 tokens** (configurable via `MEW_SESSION_START_MAX_TOKENS`) limits the injected block
- Sections are ordered so static content (vault rules, agent persona) comes first — these hit Anthropic's **prompt cache** and cost nothing after the first call
- Dynamic content (project status, instincts, wiki brief) comes after the cache boundary
- The whitelist system filters `Project_Status.md` to only the fields relevant to the active silo (e.g. code projects only inject `current_phase`, `stack`, `open_threads`, `tier`, `plan_approved` — not every field)
- Context injection is **whitelisted per silo**, so a game session never gets code-silo fields

```
[static — cached]        vault rules + agent persona
[dynamic — not cached]   project status (whitelisted) + instincts + wiki brief + trigger
```

### Conversational triggers

When you type `standup` or `wrap up`, the `UserPromptSubmit` hook detects the phrase before your message reaches Claude and appends the full workflow instructions to the injected context block. Claude sees both your message and the instructions in the same turn and executes the workflow.

Trigger patterns live in `hooks/session-start.js` as regex + instruction pairs. Arguments are extracted from the prompt — `dump — <content>` passes the content as the argument to the dump workflow.

### Semantic search (doobidoo)

MewVault ships a persistent semantic search layer called **doobidoo** — an MCP server backed by SQLite-vec and Ollama embeddings.

- Runs via MCP stdio transport, auto-started by Claude Code on launch
- Backend: **SQLite-vec** at `~/.mewvault/chroma-wiki/memory.db`
- Embeddings: Ollama `nomic-embed-text` running locally
- Indexes wiki notes and source files; Claude calls it as a tool during any session
- Re-index after significant changes: `python scripts/ingest_wiki.py` or `scripts/ingest_code.py`
- Falls back silently if Ollama is not running

**memory MCP** (all silos)
- In-session knowledge graph via `@modelcontextprotocol/server-memory`
- Claude uses it to build up entity and relation context during long tasks
- Resets between sessions — not a persistent store

### Instinct system

MewVault learns from corrections. When `post-tool-use.js` detects that the same file was rewritten within 60 seconds (a rapid-rewrite signal), it writes a candidate to `instincts/pending/`. You review candidates with `mew instinct status` and promote the ones worth keeping. Promoted instincts are injected at every session start as the `## Active Vault Instincts` section.

```
rapid rewrite detected
       ↓
instincts/pending/<id>.json    (candidate — not yet active)
       ↓  mew instinct promote <id>
instincts/promoted/<id>.json   (injected every session)
```

### Agent array

Seven specialist agents routed through a **LiteLLM proxy**. Each agent has a fixed model and a scoped role — the session-start hook selects the right one based on the active silo.

| Agent | Silo | Role |
|---|---|---|
| `mew-coder` | code | Implementation, refactoring, test generation |
| `mew-gamedev` | game | GDScript, game mechanics, Godot patterns |
| `mew-designer` | design | UX, Figma review, component specs |
| `mew-learner` | wiki | Concept distillation, research ingest |
| `mew-planner` | any | Architecture, MewKing plans |
| `mew-archivist` | any | Session wrap, log writes, git messages |
| `mew-chief` | global | Cross-silo orchestration, triage, routing |

The proxy starts with `mew harness proxy`. Agents are invoked via `mew agent invoke <name> --task "..."` or automatically selected by silo context.

### How mewwiki stays current

```
mewvault/  ──prompt──▶  Claude Code
                              │
                    writes to silos
                              │
              log.md  Project_Status.md  wiki/*.md
                              │
              mew wiki sync (on session end)
                              │
               mewwiki/ ──reads──▶  Obsidian
```

- `Project_Status.md` → `mewwiki/Projects/<slug>/index.md` (always overwritten)
- `log.md` → `mewwiki/Projects/<slug>/log.md` (new entries appended, no duplicates)
- `wiki/<page>.md` → `mewwiki/_inbox/<slug>-<page>.md` (queued — you route them)

The sync is idempotent and git-diff-based — only changed files trigger writes. mewwiki has its own git repo; every sync creates a commit. Direct writes to `mewwiki/` are blocked by the `PreToolUse` hook. All content flows through silos.

---

## Installation

### Requirements

| | macOS | Windows |
|---|---|---|
| Python | 3.11+ — `brew install python` | 3.11+ — `winget install Python.Python.3.12` |
| Node.js | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| Git | `brew install git` | `winget install Git.Git` |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | same |
| Obsidian | [obsidian.md](https://obsidian.md) | same |
| Ollama *(optional)* | `brew install ollama` — for semantic search | [ollama.com](https://ollama.com/download) |

---

### Step 1 — Clone and install the CLI

**macOS:**
```bash
cd ~/Jan   # or wherever your workspace root is
git clone <this-repo> mewvault
cd mewvault
pip3 install -e .
```

**Windows (PowerShell):**
```powershell
cd C:\Users\<you>\Jan
git clone <this-repo> mewvault
cd mewvault
pip install -e .
```

---

### Step 2 — Set the environment variable

**macOS** — add to `~/.zshrc` or `~/.bash_profile`:
```bash
export MEWVAULT_ROOT="$HOME/Jan/mewvault"
source ~/.zshrc
```

**Windows** — add to `$PROFILE`:
```powershell
$env:MEWVAULT_ROOT = 'C:\Users\<you>\Jan\mewvault'
```

---

### Step 3 — Register hooks

```bash
mew harness install
```

Registers five Claude Code lifecycle hooks in `~/.claude/settings.json`. They fire automatically — nothing else needed.

---

### Step 4 — Bootstrap the workspace silos

```bash
mew init
```

Creates `wiki/`, `design-studio/`, `game-lab/`, and `secrets/` adjacent to `mewvault/`. Skips any that already exist.

---

### Step 5 — Bootstrap MewWiki

```bash
mew wiki init --path ~/Jan/mewwiki
```

Creates the Obsidian vault at `~/Jan/mewwiki` with:
- `Brain/` — North Star, Memories, Patterns, Gotchas
- `Projects/` — auto-mirrored from silos on each sync
- `Operations/` — People, Meetings, Decisions, Ideas inbox
- `Knowledge/` — cross-silo concept library
- `Integrations/` — Calendar, GitHub (populated by sync)
- `Bases/` — 6 live dashboards (configure via Obsidian UI)
- `Templates/` — 8 note templates
- `.obsidian/` — pre-configured core plugins

---

### Step 6 — Open in Obsidian

1. Open Obsidian → **Open folder as vault** → select `~/Jan/mewwiki`
2. Go to **Settings → Core plugins** → enable **Bases**
3. Go to **Settings → Core plugins → Templates** → set folder to `Templates`

---

### Step 7 — First sync

```bash
cd ~/Jan/mewvault
python mew.py wiki sync
```

Obsidian updates immediately. Each silo's `Project_Status.md` and `log.md` are mirrored into `Projects/`. Wiki pages queue in `_inbox/` for you to route.

---

### Step 8 (optional) — Enable semantic search

MewVault uses **doobidoo** for persistent semantic search across wiki notes and source files. It requires Ollama running locally.

```bash
# Install Ollama and pull the embedding model
brew install ollama          # macOS
ollama pull nomic-embed-text

# Install the doobidoo MCP server into the venv
pip install mcp-memory-service

# Add doobidoo to Claude Code's MCP config (see mcp-configs/doobidoo.json)
# Point it at the workspace root: /Jan/.mcp.json
```

Ollama runs as a Homebrew launchd service — it starts at login and stays running. Verify with:

```bash
brew services list | grep ollama   # should show: started
ollama list                         # confirm nomic-embed-text is present
```

After significant file changes, re-index manually:

```bash
python scripts/ingest_wiki.py    # wiki notes
python scripts/ingest_code.py    # source files
```

---

### Verify everything works

```bash
mew status --quick      # vault overview
mew harness status      # hook registration
mew wiki sync --dry-run # preview next sync without writing
```

Then open Claude Code in `mewvault/`:
```bash
cd ~/Jan/mewvault
claude
```

Say **standup**. You should see a morning brief with your active projects and inbox count.

---

## Upgrading

```bash
cd ~/Jan/mewvault
git pull
pip3 install -e .
mew harness install   # re-registers if new hooks were added
```

---

## CLI reference

### MewWiki

| Command | Description |
|---|---|
| `mew wiki init [--path PATH]` | Bootstrap a new mewwiki vault |
| `mew wiki sync` | Sync all silos → mewwiki (idempotent) |
| `mew wiki sync --dry-run` | Preview what would sync without writing |
| `mew wiki sync --wiki PATH` | Override vault path for this run |

### Workspace

| Command | Description |
|---|---|
| `mew status` | Vault overview across all silos |
| `mew status --domain software` | Filter to one silo |
| `mew status --project <name>` | Deep view of a single project |
| `mew status --stale 14` | Projects untouched for 14+ days |
| `mew status --quick` | Single-line vault summary |
| `mew validate` | Check all Project_Status.md files |
| `mew validate --fix` | Offer to repair fixable issues |

### Projects

| Command | Description |
|---|---|
| `mew new code-project <name> --stack next` | Scaffold a code project |
| `mew new ux-project <name>` | Scaffold a design project |
| `mew new game-project <name>` | Scaffold a full game project |
| `mew new game-experiment <name>` | Low-commitment prototype |
| `mew new learning-path <name>` | Learning track in wiki/ |
| `mew rename <old> <new>` | Rename a project folder |
| `mew archive <name>` | Move to `_archive/` |
| `mew abandon <name>` | Mark abandoned with a reason |

### Promotions

| Command | Description |
|---|---|
| `mew promote <ux-name> --to <code-name>` | UX → code project |
| `mew promote game-lab/_experiments/<name>` | Experiment → full game |
| `mew promote wiki/ --topic <tag>` | Wiki research → UX project |

### Git

| Command | Description |
|---|---|
| `mew sync` | Git status across all silo repos |
| `mew sync --commit "message"` | Interactively commit each repo |
| `mew sync --commit "message" --push` | Commit and push |
| `mew sync --pr` | Create GitHub PR from last-session-message.txt |

### Secrets

| Command | Description |
|---|---|
| `mew secret set KEY_NAME` | Store a secret |
| `mew secret get KEY_NAME` | Inject as env variable |
| `mew secret list` | List key names (not values) |
| `mew secret rotate KEY_NAME` | Rotate a stored secret |

### Context

| Command | Description |
|---|---|
| `mew dump <project>` | Token-budgeted context snapshot |
| `mew compact` | Semantic context map for workspace |
| `mew compact --project <name>` | Scope to one project |
| `mew process-inbox` | List `wiki/_inbox/` and propose routing |

### Agents

| Command | Description |
|---|---|
| `mew harness proxy` | Start the LiteLLM proxy |
| `mew agent list` | List specialist agents |
| `mew agent invoke <name> --task "..."` | Invoke an agent |

### Instincts

| Command | Description |
|---|---|
| `mew instinct status` | Pending and promoted instincts |
| `mew instinct promote <id>` | Promote a pending instinct |
| `mew instinct prune` | Remove stale instincts |
| `mew instinct export --out file.json` | Export to JSON |

### Harness

| Command | Description |
|---|---|
| `mew harness install` | Register hooks |
| `mew harness status` | Hook registration and instinct counts |
| `mew harness status --verbose` | Per-silo field whitelist |
| `mew harness config` | Harness env vars |
| `mew harness disable` | Remove all hooks |

---

## Tier gates

Every project has a `tier` in `Project_Status.md`.

**Pounce** — small tasks under 2 hours. No plan required. Claude writes directly.

**Stalk** — multi-session features. Claude proposes approach in chat. Verbal approval before writing.

**MewKing** — architecture or risky changes. Hard gate: Claude cannot write code until `plan_approved: true` in `Project_Status.md`. Creates `proposals/active/<feature>/plan.md`. After two blocked attempts, `REVIEW_REQUIRED.md` is written automatically.

---

## Project layout

```
<silo>/<project>/
  Project_Status.md   # tier, status, current_phase, next_action
  proposals/active/   # MewKing plans
  src/                # Source code
  raw/                # Specs, PRDs — immutable
  wiki/               # Architecture decisions (flow to mewwiki)
  log.md              # Session log (flows to mewwiki)
```

```
mewwiki/
  Brain/              # North Star, Memories, Patterns, Gotchas
  Projects/           # Mirrors of all silo projects
  Operations/         # People, Meetings, Decisions, Ideas
  Knowledge/          # Cross-silo concept library
  Integrations/       # Calendar, GitHub
  _inbox/             # New wiki pages queued for review
  Bases/              # 6 live dashboards
  Templates/          # 8 note templates
```
