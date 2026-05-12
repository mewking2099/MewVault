# MewVault

A federated AI workspace manager built for Claude Code. One terminal window. Everything flows through `mewvault/` — your projects, your knowledge, your daily rhythm.

---

## What it is

MewVault organises work into independent git **silos**, enforces planning gates before code is written, and wires Claude Code hooks to inject context automatically at the start of every session.

**MewWiki** is the read layer — an Obsidian vault that stays current with your silos automatically. You browse it. Claude writes to it at session end via `mew wiki sync`. You never work from it directly.

```
workspace-root/
  mewwiki/              # Obsidian vault — auto-updated, read in Obsidian
  mewvault/             # This repo — CLI, hooks, slash commands
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

> **standup** (or `/standup`)

Claude reads your Brain/North Star, all active Project_Status.md files, and your open PRs. You get a morning brief in one block — priorities, meetings (if Google Calendar is connected), inbox, PRs.

---

### During the day — working on a project

**Start new work in a silo:**

> **new project rate-calc** (or `/project-new rate-calc`)

Claude asks: name, silo, stack, north star, tier. Runs `mew new`, scaffolds the silo folder, creates a mewwiki mirror in `Projects/rate-calc/` immediately — no waiting for sync.

**Jump into an existing project:**

Just open Claude Code in the project folder, or say the project name. The session-start hook detects the silo and injects the right context automatically.

**Capture something mid-session:**

> **dump — we decided to use Supabase instead of Prisma for this project** (or `/dump ...`)

Claude classifies it (decision, idea, person note, API gotcha, etc.), proposes where it goes, and asks for confirmation before writing. Decisions land in `Operations/Decisions/`, ideas in the inbox, API notes in the silo's `wiki/`.

---

### End of day — wrap up

> **wrap up** (or `/wrap-up`)

Claude:
1. Writes a session log entry to the active project's `log.md`
2. Updates `Project_Status.md` with `last_session` and `next_action`
3. Runs `mew wiki sync` — silos → mewwiki, committed automatically
4. Flags any unrouted inbox items
5. Suggests a git commit message

Then open Obsidian. Your projects, decisions, and wiki pages are current.

---

### Other commands you'll use regularly

| Say this | What happens |
|---|---|
| **meeting prep vodafone** | Loads attendee profiles + last meeting notes + suggests agenda |
| **capture the meeting** | Extracts decisions + action items → files in Operations/ |
| **ingest raw/spec.pdf** | Discusses concept pages with you before writing (Karpathy rule) |
| **standup** | Morning brief — projects, inbox, PRs, calendar |
| **wrap up** | Session end — log, sync, commit suggestion |

All of these work as plain sentences or as `/slash` commands.

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

This registers five Claude Code lifecycle hooks in `~/.claude/settings.json`. They fire automatically — nothing else needed.

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

Your vault is ready. Run `mew wiki sync` to pull your first silo content in.

---

### Step 7 — First sync

```bash
cd ~/Jan/mewvault
python mew.py wiki sync
```

Obsidian updates immediately — no reload needed. Each silo's `Project_Status.md` and `log.md` are mirrored into `Projects/`. Wiki pages queue in `_inbox/` for you to route.

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

## Slash commands

All commands work as `/command` or as plain English. They live in `.claude/commands/`.

| Command | Trigger | What it does |
|---|---|---|
| `/standup` | "standup", "morning brief" | Projects, inbox, PRs, calendar |
| `/project-new` | "new project <slug>" | Scaffold silo + mewwiki mirror |
| `/dump` | "dump — <content>" | Classify + route a note |
| `/wrap-up` | "wrap up", "end session" | Log, sync, commit suggestion |
| `/meeting-prep` | "prep for <topic>" | Attendee context + last meeting + agenda |
| `/meeting-capture` | "capture the meeting" | Decisions + action items → Operations/ |
| `/ingest` | "ingest <file>" | Distill raw doc into concept pages |

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

## MewHarness hooks

Five hooks run automatically — no manual triggers.

| Event | What it does |
|---|---|
| `UserPromptSubmit` | Injects vault rules, project status, Brain/North Star, inbox count, instincts |
| `Stop` | Writes auto-wrap log entry, runs `mew wiki sync`, appends to Brain/Memories |
| `PreToolUse` | MewKing gate, secrets guard, `raw/` lock, mewwiki write guard, TDD warning |
| `PostToolUse` | Accumulates session activity, detects correction signals for instincts |
| `PreCompact` | Semantic compact, context snapshots |

---

## Tier gates

Every project has a `tier` in `Project_Status.md`.

**Pounce** — small tasks under 2 hours. No plan required. Claude writes directly.

**Stalk** — multi-session features. Claude proposes approach in chat. Verbal approval before writing.

**MewKing** — architecture or risky changes. Hard gate: Claude cannot write code until `plan_approved: true` in `Project_Status.md`. Creates `proposals/active/<feature>/plan.md`. After two blocked attempts, `REVIEW_REQUIRED.md` is written automatically.

---

## How mewwiki stays current

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

The sync is idempotent. Run it as many times as you want. mewwiki has its own git repo — every sync creates a commit.

Direct writes to `mewwiki/` are blocked by the `PreToolUse` hook. All content flows through silos.

---

## Agent array

Seven specialist agents routed through a LiteLLM proxy.

| Agent | Role |
|---|---|
| `mew-planner` | Architecture, MewKing plans |
| `mew-designer` | UX, Figma review, component specs |
| `mew-coder` | Implementation, tests |
| `mew-gamedev` | GDScript, game mechanics, Godot |
| `mew-learner` | Concept distillation, learning tracks |
| `mew-archivist` | Session wrap, log writes, git messages |
| `mew-chief` | Cross-silo orchestration, triage |

```bash
mew harness proxy     # start the proxy first
mew agent list
mew agent invoke mew-planner --task "Design auth flow for acme-web"
```

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
  Integrations/       # Calendar, GitHub (future: Teams)
  _inbox/             # New wiki pages queued for review
  Bases/              # 6 live dashboards
  Templates/          # 8 note templates
```
