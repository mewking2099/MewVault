<div align="center">

<br>

<h1>MewVault</h1>

<p>
  <strong>A federated AI workspace for Claude Code.</strong><br>
  Five independent silos. An Obsidian wiki that syncs itself.<br>
  An instinct system that learns from how you work.
</p>

<p>
  <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-required-D97706?style=flat-square">
  <img alt="Obsidian" src="https://img.shields.io/badge/Obsidian-mewwiki-7C3AED?style=flat-square">
  <img alt="macOS + Windows" src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows-555?style=flat-square">
</p>

<br>

</div>

---

## What makes it different

There are great patterns out there for working with AI on a codebase — the Karpathy wiki approach, community CLAUDE.md setups, various hook recipes for injecting context. They all solve the same core problem: *how do you give an AI the right context without burning your token budget?*

MewVault does that too. But it's built around two structural ideas that those patterns don't address:

<br>

**Two engines, not one.** Most setups treat the AI workspace as a single directory. MewVault splits it into a write engine and a read layer:

- **`mewvault/`** is where you *work* — the CLI, hooks, agents, secrets. Claude Code runs from here.
- **`mewwiki/`** is where you *browse* — a separate Obsidian vault that Claude syncs after every session. You never write to it directly; it stays current automatically.

This means your notes and project status are always in Obsidian in a browseable, linkable, searchable form — not buried in git commits or agent memory.

<br>

**Five silos with separate git histories and separate workflows.** Code projects, design work, game prototypes, and your knowledge base each live in their own git repo with their own planning rules, hook context, and promotion paths. A code session injects different context than a design session. A game experiment doesn't need a MewKing plan; a production feature does.

<br>

**Projects promote between silos.** Research in `wiki/` can become a UX brief in `design-studio/`. A Figma-complete design can promote to a scaffolded code project in `software-projects/`. A `game-lab/` experiment can become a full game project. The `mew promote` command handles the cross-silo handoff with a single command.

---

## Architecture

```
workspace-root/
├── mewvault/           ← you are here — CLI engine, hooks, agents
├── mewwiki/            ← Obsidian vault — auto-synced, read-only by convention
├── software-projects/  ← code (Next.js, Astro, SvelteKit)
├── design-studio/      ← UX & Figma-integrated design work
├── game-lab/           ← Godot games and low-commitment experiments
└── wiki/               ← knowledge base, research, learning tracks
```

Each silo is an independent git repo. `mewvault/` is the only one Claude opens by default. The `mew wiki sync` command — triggered automatically at session end — mirrors all silo content into `mewwiki/`.

<br>

```
  silos                    Claude Code               mewwiki (Obsidian)
  ─────                    ───────────               ──────────────────
  software-projects/   ──▶  session-start.js  ──▶   Projects/<name>/index.md
  design-studio/            (injects context)        Projects/<name>/log.md
  game-lab/                        │                 Knowledge/concepts/
  wiki/                    session-end.js     ──▶   _inbox/ (new wiki pages)
                            (mew wiki sync)          Brain/ · Operations/
```

---

## Silo workflows and promotions

Each silo has its own rules and Claude persona:

| Silo | Stack | Agent | What's different |
|---|---|---|---|
| `software-projects/` | Next.js · Astro · SvelteKit | `mew-coder` | TDD warning on every new file; strict tier gates |
| `design-studio/` | Figma (via MCP) | `mew-designer` | Figma node reads; never manually transcribe measurements |
| `game-lab/` | GDScript / Godot | `mew-gamedev` | `_experiments/` bypasses MewKing gate — prototype freely |
| `wiki/` | Markdown | `mew-learner` | Research, concept distillation, learning tracks |

**Project promotion** — moving work between silos when it's ready:

```bash
# Research → UX brief
mew promote wiki/ --topic "payment-flow"

# Approved design → scaffolded code project
mew promote my-ux-project --to my-code-project

# Game experiment → full game project
mew promote game-lab/_experiments/platformer
```

Each promotion scaffolds the destination project with the source artefacts already in place — no copy-pasting, no manual linking.

---

## Daily rhythm

### Morning

```bash
cd ~/Jan/mewvault
claude
```

Then say: **standup**

Claude reads your North Star, all active `Project_Status.md` files, and open PRs. You get a morning brief: priorities, inbox count, idle projects, today's calendar if connected.

<br>

### During the day

| Say this | What happens |
|---|---|
| **standup** | Morning brief — projects, inbox, PRs, calendar |
| **new project rate-calc** | Claude asks: silo, stack, north star, tier → scaffolds everything |
| **dump — we decided to use Supabase** | Classified as decision/idea/gotcha → proposed destination → you confirm |
| **ingest raw/spec.pdf** | Discusses concept pages with you → writes to `wiki/` on approval |
| **promote my-design --to my-app** | Cross-silo handoff — scaffolds the code project from the UX artefacts |
| **meeting prep vodafone** | Loads attendee profiles + last meeting notes + suggests agenda |
| **wrap up** | Session log, `Project_Status.md` update, wiki sync, commit suggestion |

All of these are plain sentences — no slash commands, no special syntax.

<br>

### End of day

Say: **wrap up**

Claude writes the session log, updates `Project_Status.md`, runs `mew wiki sync`, checks the inbox, and suggests a commit message. Open Obsidian — everything is current.

---

## Planning gates

Every project has a `tier` in `Project_Status.md`. This is enforced at the OS level by the `PreToolUse` hook — not just a guideline.

| Tier | When | How it works |
|---|---|---|
| **Pounce** | Small tasks, under 2 hours | No plan required. Claude writes directly. |
| **Stalk** | Multi-session features | Claude proposes approach in chat. Verbal approval before writing. |
| **MewKing** | Architecture or risky changes | Hard gate: no code until `plan_approved: true` in `Project_Status.md`. Claude creates `proposals/active/<feature>/plan.md` and waits. After two blocked attempts, `REVIEW_REQUIRED.md` is written automatically. |

---

<details>
<summary><strong>Under the hood — hooks, instincts, token budget</strong></summary>

<br>

### Hook runtime (MewHarness)

Five Claude Code lifecycle hooks fire automatically. Install once with `mew harness install`.

| Hook | Event | What it does |
|---|---|---|
| `session-start.js` | `UserPromptSubmit` | Injects vault rules, project status, Brain brief, instincts, semantic context — detects conversational triggers |
| `session-end.js` | `Stop` | Writes auto-wrap log entry, runs `mew wiki sync`, appends to Brain/Memories |
| `pre-tool-use.js` | `PreToolUse` | MewKing gate, secrets guard, `raw/` lock, mewwiki write guard, TDD warning |
| `post-tool-use.js` | `PostToolUse` | Accumulates session activity, detects rapid-rewrite signals for instinct candidates |
| `pre-compact.js` | `PreCompact` | Semantic context snapshot before conversation compresses |

<br>

### Token budget

The `UserPromptSubmit` hook prepends a context block to every prompt. To keep it efficient:

- Hard cap of **6,000 tokens** (configurable via `MEW_SESSION_START_MAX_TOKENS`)
- Static content (vault rules, agent persona) comes first — hits Anthropic's **prompt cache**, costs nothing after the first call
- Dynamic content (project status, instincts, wiki brief) comes after the cache boundary
- `Project_Status.md` fields are **whitelisted per silo** — a game session never gets code-silo fields

```
[static — cached]     vault rules + agent persona
[dynamic — live]      project status + instincts + wiki brief + trigger
```

<br>

### Instinct system

MewVault learns from corrections. When `post-tool-use.js` detects the same file was rewritten within 60 seconds, it writes a candidate to `instincts/pending/`. You review and promote the ones worth keeping. Promoted instincts are injected at every session start.

```
rapid rewrite detected
       ↓
instincts/pending/<id>.json     ← candidate, not yet active
       ↓  mew instinct promote <id>
instincts/promoted/<id>.json    ← injected every session
```

```bash
mew instinct status          # review pending candidates
mew instinct promote <id>    # make one permanent
mew instinct prune           # clean up stale entries
```

<br>

### Semantic search (doobidoo)

An MCP server backed by **SQLite-vec** and Ollama embeddings for persistent semantic search across wiki notes and source files. Runs via MCP stdio transport, auto-started by Claude Code.

- Backend: SQLite-vec at `~/.mewvault/chroma-wiki/memory.db`
- Embeddings: Ollama `nomic-embed-text` (local, no API cost)
- Re-index after significant changes: `python scripts/ingest_wiki.py`

<br>

### How mewwiki stays current

| Source file | Destination in mewwiki | Behaviour |
|---|---|---|
| `Project_Status.md` | `Projects/<slug>/index.md` | Always overwritten on sync |
| `log.md` | `Projects/<slug>/log.md` | New entries appended, no duplicates |
| `wiki/<page>.md` | `_inbox/<slug>-<page>.md` | Queued — you route them in Obsidian |

The sync is idempotent and git-diff-based — only changed files trigger writes. Direct writes to `mewwiki/` are blocked by the `PreToolUse` hook; all content flows through silos.

</details>

---

## Getting started

### Requirements

| | macOS | Windows |
|---|---|---|
| Python | 3.11+ · `brew install python` | 3.11+ · `winget install Python.Python.3.12` |
| Node.js | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | same |
| Obsidian | [obsidian.md](https://obsidian.md) | same |
| Ollama *(optional)* | `brew install ollama` | [ollama.com](https://ollama.com/download) |

<br>

**1 — Clone and install**

```bash
cd ~/Jan   # your workspace root
git clone <this-repo> mewvault
cd mewvault
pip3 install -e .
```

**2 — Set the workspace root**

```bash
# ~/.zshrc or ~/.bash_profile
export MEWVAULT_ROOT="$HOME/Jan/mewvault"
```

**3 — Register hooks**

```bash
mew harness install
```

**4 — Bootstrap silos**

```bash
mew init
```

Creates `wiki/`, `design-studio/`, `game-lab/`, and `secrets/` adjacent to `mewvault/`.

**5 — Bootstrap MewWiki**

```bash
mew wiki init --path ~/Jan/mewwiki
```

Creates the Obsidian vault with Brain, Projects, Operations, Knowledge, Integrations, Bases, and Templates pre-configured.

**6 — Open in Obsidian**

Open Obsidian → **Open folder as vault** → select `~/Jan/mewwiki`. Enable **Bases** in Settings → Core plugins.

**7 — First sync**

```bash
mew wiki sync
```

**8 — Verify**

```bash
mew status --quick      # vault overview
mew harness status      # hook registration check
```

Open Claude Code in `mewvault/`. Say **standup**.

---

<details>
<summary><strong>Full CLI reference</strong></summary>

<br>

**MewWiki**

| Command | Description |
|---|---|
| `mew wiki init [--path PATH]` | Bootstrap a new Obsidian vault |
| `mew wiki sync` | Sync all silos → mewwiki |
| `mew wiki sync --dry-run` | Preview without writing |

**Workspace**

| Command | Description |
|---|---|
| `mew status` | Vault overview across all silos |
| `mew status --domain software` | Filter to one silo |
| `mew status --stale 14` | Projects untouched for 14+ days |
| `mew status --quick` | Single-line summary |
| `mew validate` | Check all Project_Status.md files |

**Projects**

| Command | Description |
|---|---|
| `mew new code-project <name> --stack next` | Scaffold a code project |
| `mew new ux-project <name>` | Scaffold a design project |
| `mew new game-project <name>` | Scaffold a full game project |
| `mew new game-experiment <name>` | Low-commitment prototype (no gate) |
| `mew rename <old> <new>` | Rename a project |
| `mew archive <name>` | Move to `_archive/` |
| `mew abandon <name>` | Mark abandoned with a reason |

**Promotions**

| Command | Description |
|---|---|
| `mew promote <ux-name> --to <code-name>` | Design → code project |
| `mew promote game-lab/_experiments/<name>` | Experiment → full game |
| `mew promote wiki/ --topic <tag>` | Research → UX project |

**Git**

| Command | Description |
|---|---|
| `mew sync` | Git status across all repos |
| `mew sync --commit "message"` | Interactively commit each repo |
| `mew sync --pr` | Create GitHub PR from session message |

**Secrets**

| Command | Description |
|---|---|
| `mew secret set KEY_NAME` | Store a secret |
| `mew secret get KEY_NAME` | Inject as env variable |
| `mew secret list` | List key names (not values) |
| `mew secret rotate KEY_NAME` | Rotate a stored secret |

**Harness & Instincts**

| Command | Description |
|---|---|
| `mew harness install` | Register hooks |
| `mew harness status` | Hook registration and instinct counts |
| `mew harness disable` | Remove all hooks |
| `mew instinct status` | Pending and promoted instincts |
| `mew instinct promote <id>` | Promote a pending instinct |
| `mew instinct prune` | Remove stale instincts |

</details>

---

<div align="center">
<br>
<sub>Built for Claude Code · Works on macOS and Windows · Requires Obsidian for the wiki layer</sub>
</div>
