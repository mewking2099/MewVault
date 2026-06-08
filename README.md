<div align="center">

<br>

<img src="assets/git_cat.png" alt="MewVault" width="420">

<h1>MewVault</h1>

<p>
  <strong>A federated AI workspace for Claude Code.</strong><br>
  Seven independent silos. A CLI that learns from corrections.<br>
  An agent array that routes itself.
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

MewVault does that too. But it's built around three structural ideas those patterns don't address:

<br>

**Two engines, not one.** Most setups treat the AI workspace as a single directory. MewVault splits it into a write engine and a read layer:

- **`mewvault/`** is where you *work* — the CLI, hooks, agents, secrets. Claude Code runs from here.
- **`mewwiki/`** is where you *browse* — a separate Obsidian vault that Claude syncs after every session. You never write to it directly; it stays current automatically.

This means your notes and project status are always in Obsidian in a browseable, linkable, searchable form — not buried in git commits or agent memory.

<br>

**Seven silos with separate git histories and separate workflows.** Code projects, design work, game prototypes, knowledge base, and raw idea capture each live in their own git repo with their own planning rules, hook context, and promotion paths. A code session injects different context than a design session. A game experiment doesn't need a MewKing plan; a production feature does.

<br>

**Projects promote between silos.** Research in `wiki/` can become a UX brief in `design-studio/`. A Figma-complete design can promote to a scaffolded code project in `software-projects/`. A `game-lab/` experiment can become a full game project. An idea in `idea-hub/` can seed any of them. The `mew promote` command handles the cross-silo handoff with a single command.

---

## Architecture

```
workspace-root/
├── mewvault/           ← you are here — CLI engine, hooks, agents
├── mewwiki/            ← Obsidian vault — auto-synced, read-only by convention
├── software-projects/  ← code (Next.js, Astro, SvelteKit)
├── design-studio/      ← UX & Figma-integrated design work
├── game-lab/           ← Godot 4 games and low-commitment experiments
├── wiki/               ← knowledge base, research, learning tracks
└── idea-hub/           ← idea capture, feasibility, lifecycle management
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
  idea-hub/                 (mew wiki sync)          Brain/ · Operations/
```

---

## Silo workflows and promotions

Each silo has its own rules and Claude persona:

| Silo | Stack | Agent | What's different |
|---|---|---|---|
| `software-projects/` | Next.js · Astro · SvelteKit | `mew-coder` | TDD warning on every new file; strict tier gates |
| `design-studio/` | Figma (via MCP) | `mew-designer` | Figma node reads; never manually transcribe measurements |
| `game-lab/` | GDScript / Godot 4 | `mew-gamedev` | `_experiments/` bypasses MewKing gate — prototype freely |
| `wiki/` | Markdown | `mew-learner` | Research, concept distillation, learning tracks |
| `idea-hub/` | Markdown | `mew-ideator` | Idea capture, feasibility, lifecycle — no-code zone |
| `mewvault/` | Python · Node.js | `mew-chief` | CLI engine, hooks, agent array, skills |

**Project promotion** — moving work between silos when it's ready:

```bash
# Research → UX brief
mew promote wiki/ --topic "payment-flow"

# Approved design → scaffolded code project
mew promote my-ux-project --to my-code-project

# Game experiment → full game project
mew promote game-lab/_experiments/platformer

# Validated idea → any silo
mew promote idea-hub/ideas/my-idea --to software-projects
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

## Core concepts

MewVault is built on five interconnected systems.

<br>

### 1 · Token budget management

| Layer | Mechanism | How it helps |
|---|---|---|
| **Hard cap** | `MEW_SESSION_START_MAX_TOKENS = 6000` | Injected context can't grow unboundedly regardless of how many projects you have |
| **Prompt cache** | Static content (rules, agent persona) is injected first | Anthropic caches it — repeated calls to this block are ~10× cheaper and faster |
| **Per-silo whitelist** | `Project_Status.md` fields are filtered per silo | A game session never receives code-silo fields; a design session never gets game fields |
| **Semantic search** | doobidoo MCP (SQLite-vec + Ollama) | On-demand retrieval instead of injecting everything upfront |

```
┌─ cached (static) ──────────────────────────────┐
│  vault rules · agent persona · silo rules       │  ← paid once, then free
└─────────────────────────────────────────────────┘
┌─ live (dynamic) ────────────────────────────────┐
│  project status · active instincts · wiki brief  │  ← fresh each turn
│  recent memory context · trigger instructions   │
└─────────────────────────────────────────────────┘
```

<br>

### 2 · Agent array

Nine specialist agents, no proxy required. `mew-chief` acts as a live dispatcher — it reads every prompt, classifies the intent, announces its routing decision, and spawns the right sub-agent as a native Claude Code agent with the correct model already selected. You never route manually.

```
you: "plan the auth refactor"
              ↓
        mew-chief (dispatcher)
              ↓ → Routing to mew-planner (opus)…
        mew-planner spawned
              ↓
        write-mewking-plan skill activated
              ↓ chains_to →
        mew-archivist logs the result
```

| Agent | Model | Silo | Skills | Role |
|---|---|---|---|---|
| `mew-chief` | Sonnet 4.6 | global | dispatcher | Classifies every request, announces routing, spawns sub-agents |
| `mew-planner` | **Opus 4.7** | any | 3 | Architecture, MewKing plans, risk maps, tier analysis |
| `mew-coder` | Sonnet 4.6 | software | 8 | TDD workflow, implementation, code review, refactor, webapp testing, MCP building |
| `mew-designer` | Sonnet 4.6 | design | 2 | Figma MCP reads, component specs, token audit |
| `mew-learner` | Sonnet 4.6 | wiki | 2 | Concept distillation, PDF ingest, knowledge routing |
| `mew-gamedev` | Sonnet 4.6 | game | 2 | GDScript review, mechanic design, Godot patterns |
| `mew-archivist` | **Haiku 4.5** | any | 3 | Session wrap, log writes, commit message generation |
| `mew-researcher` | Sonnet 4.6 | any | 4 | Web research, competitive analysis, feasibility assessment |
| `mew-ideator` | Sonnet 4.6 | idea | 3 | Idea capture, expansion, feasibility routing, lifecycle management |

**44 skills across 9 agents.** Drop a new `.md` skill file and run `mew agent sync`; the routing index rebuilds and the skill is live from the next session. No code changes needed.

**Hermes delegation** — agents can further delegate to other sub-agents mid-task. `mew-chief` may spawn `mew-planner`, which may in turn spawn `mew-archivist` to log its output. The delegation chain resolves through the routing index; no hardcoded wiring.

**Default:** the agent array runs entirely on your Claude Code subscription via native sub-agent spawning — no proxy needed.

**With LiteLLM:** agents can be routed to alternative providers. DeepSeek (`deepseek-chat`, `deepseek-reasoner`) is configured as the cost-reduction fallback — `mew-researcher` and `mew-archivist` can run on DeepSeek for high-volume or long-running tasks where Opus/Sonnet budget matters. LiteLLM handles the provider translation; agent skill files stay unchanged.

<br>

### 3 · SQLite memory layer

Cross-session context that persists between conversations. `mew memory sync` indexes every markdown file across all silos into a local SQLite FTS5 database. At session start, the `loadMemoryRecall` function queries the store and injects the most recently-updated documents into the context banner.

```bash
mew memory sync           → indexes all silos into .mew-memory.db
mew memory search "auth"  → full-text search across the store
mew memory recall         → recent docs for the current silo (session-start uses this)
mew memory purge          → remove entries older than N days
```

Unlike the in-session knowledge graph (which resets between conversations), the SQLite store is durable — it survives across sessions, machine restarts, and context compactions.

<br>

### 4 · Instinct system

When `post-tool-use.js` detects the same file was rewritten within 60 seconds (the *rapid-rewrite signal*), it logs a candidate to `instincts/pending/`. You review it, decide if it's worth keeping, and promote the ones that are. Promoted instincts are injected into every future session start.

```
you correct Claude → same file rewritten within 60s
                              ↓
              instincts/pending/<hash>.json
                              ↓
                  mew instinct status
                              ↓
              mew instinct promote <id>
                              ↓
              instincts/promoted/<id>.json    ← injected every session
```

Each instinct carries a **confidence score** (0–1) and decays if it stops being triggered. `mew instinct prune` removes the stale ones so the injected block stays tight.

<br>

### 5 · Semantic command system

MewVault has no slash commands. All workflows are triggered by plain sentences. The `session-start.js` hook runs a regex matcher against every prompt before it reaches Claude — if a trigger fires, the full workflow instructions are appended to the context block in the same turn.

| You say | What gets injected |
|---|---|
| `standup` / `morning brief` | Full standup workflow: parallel reads of North Star, all Project_Status.md files, open PRs, calendar |
| `wrap up` / `done for the day` | Wrap workflow: log write, status update, wiki sync, commit suggestion |
| `dump — <content>` | Classification + routing workflow: type detection, destination proposal, confirmation |
| `new project <name>` | Scaffolding workflow: questions → `mew new` → mewwiki mirror |
| `meeting prep <name>` | Loads attendee profiles + last meeting notes + agenda suggestions |
| `ingest <file>` | Concept page proposal → approval → wiki write |

The trigger system is entirely in `hooks/session-start.js` as a `TRIGGERS` array of `{ pattern, name, instructions }` objects — easy to add new commands without touching Claude's config.

<br>

### Stack

| Component | Technology |
|---|---|
| CLI | Python 3.11+ · `pathlib` throughout · editable install via `pip install -e .` |
| Hooks | Node.js · five Claude Code lifecycle hooks · `hooks/*.js` |
| Agent routing | `mew-chief` dispatcher · `agents/.routing-index.json` · rebuilt via `mew agent sync` |
| Agent skills | 44 markdown plugin files · `agents/<name>/skills/*.md` · auto-discovered · MCP-scoped |
| Persistent memory | SQLite FTS5 · `.mew-memory.db` · silo-aware · cross-session |
| Semantic search | doobidoo (mcp-memory-service) · SQLite-vec · Ollama `nomic-embed-text` (local) |
| In-session memory | `@modelcontextprotocol/server-memory` · knowledge graph · resets between sessions |
| LiteLLM | Provider abstraction layer · DeepSeek API · cost-optimised routing for select agents |
| Wiki layer | Obsidian · Bases plugin · auto-synced via `mew wiki sync` |
| Secrets | File-based · `secrets/*.env` · gitignored · `chmod 0600` on Unix · `icacls` on Windows |
| Models | Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 · DeepSeek via LiteLLM · Claude Code subscription |

---

<details>
<summary><strong>Under the hood — hooks, instincts, token budget</strong></summary>

<br>

### Hook runtime (MewHarness)

Five Claude Code lifecycle hooks fire automatically. Install once with `mew harness install`.

| Hook | Event | What it does |
|---|---|---|
| `session-start.js` | `UserPromptSubmit` | Injects vault rules, project status, Brain brief, instincts, memory recall — detects conversational triggers |
| `session-end.js` | `Stop` | Writes auto-wrap log entry, runs `mew wiki sync`, appends to Brain/Memories |
| `pre-tool-use.js` | `PreToolUse` | MewKing gate, secrets guard, `raw/` lock, mewwiki write guard, TDD warning |
| `post-tool-use.js` | `PostToolUse` | Accumulates session activity, detects rapid-rewrite signals for instinct candidates |
| `pre-compact.js` | `PreCompact` | Semantic context snapshot before conversation compresses |

<br>

### Token budget

- Hard cap of **6,000 tokens** (configurable via `MEW_SESSION_START_MAX_TOKENS`)
- Static content (vault rules, agent persona) comes first — hits Anthropic's **prompt cache**, costs nothing after the first call
- Dynamic content (project status, instincts, memory recall) comes after the cache boundary
- `Project_Status.md` fields are **whitelisted per silo** — a game session never gets code-silo fields

```
[static — cached]     vault rules + agent persona
[dynamic — live]      project status + instincts + memory recall + trigger
```

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

### One-liner install (macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/mewking2099/MewVault/main/bootstrap.sh | bash
```

This creates `~/Jan/`, clones the vault, installs `mew`, wires up Claude Code hooks and rules, and scaffolds a fresh personal wiki. Idempotent — safe to re-run.

> **Step-by-step guide for a brand-new Mac** → see [INSTALL.md](INSTALL.md)

<br>

After the bootstrap completes:

**1 — Install Claude Code**

```bash
npm install -g @anthropic-ai/claude-code
claude   # log in via browser auth
```

**2 — Store your API key**

```bash
mew secret set ANTHROPIC_API_KEY
```

**3 — Open your wiki in Obsidian**

Open Obsidian → **Open folder as vault** → select `~/Jan/mewwiki`.

**4 — First session**

```bash
cd ~/Jan/mewvault && claude
```

Then say: **standup**

<br>

### Requirements

| | macOS | Windows |
|---|---|---|
| Python | 3.11+ · `brew install python@3.11` | 3.11+ · `winget install Python.Python.3.12` |
| Node.js | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | same |
| Obsidian | [obsidian.md](https://obsidian.md) | same |
| Ollama *(optional)* | `brew install ollama` | [ollama.com](https://ollama.com/download) |

<br>

### Custom workspace path

The bootstrap defaults to `~/Jan`. To use a different location:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/mewking2099/MewVault/main/bootstrap.sh) ~/myworkspace
```

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
| `mew promote idea-hub/ideas/<slug> --to <silo>` | Idea → any silo |

**Git**

| Command | Description |
|---|---|
| `mew sync` | Git status across all repos |
| `mew sync --commit "message"` | Interactively commit each repo |
| `mew sync --pr` | Create GitHub PR from session message |

**Memory**

| Command | Description |
|---|---|
| `mew memory sync` | Index all silos into SQLite store |
| `mew memory sync --silo NAME` | Re-index one silo |
| `mew memory search QUERY` | Full-text search across the store |
| `mew memory recall` | Recent context for the current silo |
| `mew memory recall --silo NAME --days 7` | Recent context for a specific silo |
| `mew memory purge --days 90` | Remove entries older than N days |

**Agents & Skills**

| Command | Description |
|---|---|
| `mew agent sync` | Rebuild routing index from agent manifests and skills |
| `mew agent fetch-skills` | Pull skills from remote skill registries |
| `mew agent invoke <name>` | Manually invoke a named agent |

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

## Inspiration

MewVault draws on patterns and ideas from several open-source projects. None of these are dependencies — they informed the design.

**[affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)**
The primary reference for the hook architecture, token budget structure, and skill injection model. The three-pillar framing (token optimisation · memory persistence · subagent orchestration) comes directly from the ECC integration analysis. Many of MewVault's 44 skills were seeded from the ECC skill library.

**[obra/superpowers](https://github.com/obra/superpowers)**
Additional hook patterns and skill file conventions. The `always` / `on-trigger` / `manual` inject mode taxonomy is modelled on the superpowers approach.

**[nousresearch/hermes-agent](https://github.com/NousResearch/hermes-agent)**
Hermes' sub-agent delegation pattern directly informed Phase 6 of the agent array — specifically the idea that agents can spawn further sub-agents mid-task rather than returning to the dispatcher. The `agentskills.io` skill format (YAML frontmatter + markdown body) is the same philosophy as MewVault's SKILL.md format, and future skill publishing to that registry is on the roadmap.

**[bgreenwell/OctoAgent](https://github.com/bgreenwell/OctoAgent)**
A 9-agent pipeline for automated GitHub issue resolution. MewVault doesn't use it (OpenAI-only, no MCP support), but the pipeline concept — triage → plan → fix → review → commit → comment — inspired the planned `github-issue-fix` skill for `mew-coder`.

---

<div align="center">
<br>
<sub>Built for Claude Code · Works on macOS and Windows · Requires Obsidian for the wiki layer</sub>
</div>
