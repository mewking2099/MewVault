<div align="center">

<br>

<img src="assets/git_cat.png" alt="MewVault" width="420">

<h1>MewVault</h1>

<p>
  <strong>A federated AI workspace for Claude Code.</strong><br>
  Independent silos. Enforcement over advice.<br>
  Plain English in, verified work out.
</p>

</div>

---

## What it is

MewVault turns Claude Code into a managed workspace. It organises work into independent git **silos** (software, design, games, knowledge), injects the right context automatically at session start, and — its defining trait — **enforces quality with hard gates instead of hoping instructions are followed**. Plans are approved before code is written. Tests exist before source files. Design work can't ship with open P0 findings. A health monitor watches the whole thing and notifies you when something drifts.

**MewWiki** is the read layer — an Obsidian vault that stays current automatically. Decisions, session logs, and distilled knowledge flow into it at session end, get semantically indexed, and resurface in future sessions when relevant. You browse it; Claude maintains it.

```
workspace-root/
  mewwiki/              # Obsidian vault — auto-updated, semantically indexed
  mewvault/             # This repo — CLI, hooks, agents, gates
  software-projects/    # Code projects (Next.js, Astro, SvelteKit)
  design-studio/        # UX and design projects (Figma-integrated)
  game-lab/             # Godot / Unity games and experiments
  idea-hub/             # Idea capture and validation
  learn-lab/            # Skill acquisition — Japanese (SM-2 SRS) + trading (stage-gated)
  career-studio/        # Private silo — case studies, CV, skill matrix, mock interviews
  wiki/                 # Knowledge base and learning tracks
```

---

## No commands to memorise

Everything is a plain conversational sentence. The session hook detects the phrase and routes it — to a workflow or straight to the CLI.

| Say | What happens |
| --- | --- |
| **standup** | Morning brief: projects, calendar, PRs, inbox, unresolved Figma comments |
| **wrap up** | Session end: verified Definition-of-Done, log, wiki sync, commit suggestion |
| **dump — we decided X** | Classifies and routes the note (decisions carry Figma provenance) |
| **spec user-billing** | Spec-driven workflow: acceptance criteria → your approval → tests → code |
| **design session mysite** | Impeccable setup: context, PRODUCT.md check, lane, Figma pull |
| **critique https://…** | Severity-ranked design critique from pixels (works on competitors) |
| **weekly review** | Digests the week's logs into Brain/Memories, nudges stale projects |
| **doctor** / **is everything ok** | Runs the 15-check health monitor and explains any findings |
| **dashboard** | Generates and opens the HTML vault overview |
| **agent status** | Did agents actually run, and on which model |
| **token report** | Per-day token usage + cache-hit ratio |
| **token drift** | Figma variables vs DESIGN.md diff |
| **prepare handoff mysite** | Assembles the client-ready design package |
| **install ci** | Drops the CI safety net into code projects |
| **sync wiki** | Silos → mewwiki, then semantic re-index |
| **ingest raw/spec.pdf** | Proposes concept pages, writes them on approval |
| **meeting prep vodafone** | Attendee profiles + last notes + agenda |
| **brief \<topic\>** | Total-context pack: ranked excerpts from wiki, decisions, specs, logs (2k cap) |
| **validate \<idea\>** | Feasibility scan: competitors, market size, effort estimate, pursue/park/kill |
| **practice japanese** | SRS drill (due cards only) → one new grammar point → micro-conversation |
| **market prep** / **trade — \<details\>** | Trading track: journal entry, adherence review, backtest logging |
| **case study \<name\>** | Career: retro interview or auto-assembly from vault receipts |
| **mock interview** | Grounded questions from real vault history; scored feedback |

---

## The gates (enforcement over advice)

Every gate is a `PreToolUse` hook that blocks at the OS level — Claude cannot talk its way past them.

| Gate | Rule |
| --- | --- |
| **MewKing** | No code on architecture-tier projects until `plan_approved: true` |
| **TDD** | On stalk/mewking projects, no source file without a test (derive tests from the spec's acceptance criteria; opt out per project with `tdd: off`) |
| **Audit** | Design projects can't move to handoff/delivery with `open_p0 > 0` |
| **Secrets** | Writes containing key patterns (`sk-`, `ghp_`, `AKIA`, …) are blocked |
| **Immutability** | `raw/` and direct `mewwiki/` writes are blocked |
| **Model routing** | Agent dispatches without an explicit model param are blocked |
| **Impeccable bans** | UI writes with side-stripes, gradient text, glassmorphism, or oversized radii get flagged back into context instantly |

---

## Health: `mew doctor`

Fifteen automated checks, token-health first: cache safety (detects prompt-rewriting proxies — the class of tool that silently breaks Anthropic's prompt caching), cache-hit ratio from real transcripts, hook registration and matcher scope, session-start injection size (it runs the hook and measures), CI presence, WIP limits (max 3 active projects, none idle 21+ days), instinct-queue overflow, semantic index freshness, Ollama, MCP surface area.

Doctor runs detached on the first prompt of every session. Problems trigger a macOS notification and are injected into the next session as a `## Vault Health` section, so Claude tells you what's wrong before you ask.

```bash
mew doctor            # human output
mew doctor --json     # machine output; exit 0/1/2 = ok/warn/fail
```

Hard-won rule, learned the expensive way: **never put a compressing/rewriting proxy between Claude Code and the API.** Cache reads cost ~0.1x input; anything that mutates the prompt prefix re-bills the whole conversation every turn. Optimize by injecting less, never by transforming the prompt. Full story: `wiki/headroom-postmortem.md`.

---

## Spec-driven development (software silo)

Built for a product lead who doesn't read code. Your review points are product language and green checks — everything between them is enforced.

```
raw/<brief>            your intent, in your words
   ↓
specs/<feature>.md     ★ you approve: numbered acceptance criteria (AC-1…, Given/When/Then)
   ↓
tests, from the criteria   ← TDD gate blocks source-without-test
   ↓
implementation until green
   ↓
wrap                   ★ you verify: "AC-1 ✓ AC-2 ✓", typecheck/lint/test/build
                         all run before "done" — failures tag the log [incomplete]
   ↓
CI on GitHub           green check = verified, red = not done
```

`mew ci install` backfills the workflow (typecheck, lint, tests, build, dependency audit) into existing projects; new scaffolds include it automatically.

---

## Design silo (Impeccable v3)

All frontend work — in any silo — follows the [Impeccable](https://impeccable.style) loop: **init** (PRODUCT.md + DESIGN.md) → **iterate** (`/impeccable typeset|layout|colorize|polish|bolder|quieter`) → **pre-ship gauntlet** (`audit`, `clarify`, `harden`) → **maintain** (`extract`, `document`).

MewVault makes it stick: a hook anchors the flow the moment UI work starts, the absolute-ban detector runs on every UI file write, audit scores persist to `Project_Status.md`, and the audit gate blocks handoff while P0s are open. Plus: `mew design tokens --diff` (Figma variable drift), `mew package <project> --design` (full handoff package), visual regression snapshots on wrap (Playwright + `snapshot.routes.json`), and `critique <url>` for pixel-level reviews.

---

## Learn-lab silo

Two independent skill-acquisition tracks with hard discipline rules baked in.

**Japanese** — SM-2 scheduler (`scripts/srs.py`) determines which cards are due; only due cards enter context. Reference data (JMdict, KANJIDIC2) lives locally — every card is verified against it, never LLM-invented. Session shape: drill due cards → one new grammar point + 3 i+1 sentences → micro-conversation → wrap (scheduler runs, streak increments). `practice japanese` trigger.

**Trading** — stage-gated: `curriculum → backtest → rulebook → demo → live`. The vault refuses to assist beyond the current stage. Journal and backtests are append-only (hook-enforced — bash `>>` only, never edited). Reviews grade adherence, not P&L. Guardrail: discipline coach and pattern analyst — never a signal generator, never financial advice. `market prep`, `trade — <details>`, `trading review` triggers.

---

## Career-studio silo

Private, offline-only git repo. No remote ever added; excluded from wiki sync, briefs, and semantic indexing. Publishing is an explicit export step, never a side effect.

**Case study pipeline:** `assembled → drafted → publishable`. `drafted` requires a voice pass (owner edited the draft; patterns written to `brand/voice.md`). `publishable` requires `confidentiality: cleared` — hook-blocked otherwise. Clearing = owner approves a named-entity checklist Claude extracts from the draft.

**Skill matrix** — five pillars (Design / Product / Development / AI & Tooling / Leadership), levels above 2 require evidence links from vault work. `skill review` quarterly; weekly review nudges the most dormant pillar with one concrete activity.

**Mock interviews** — questions grounded in real vault history (actual decisions, shipped work). `mock interview [portfolio|challenge|behavioral|leadership]`. Monthly cadence; weekly review nudges when overdue.

**CV** — `cv/master.md` is canonical; role-targeted variants derive from it. `refresh cv` mines vault logs and case studies for new accomplishments.

---

## Under the hood

### Hook runtime

Seven lifecycle hooks, registered once with `mew harness install`:

| Hook | Event | Role |
| --- | --- | --- |
| `session-start.js` | `UserPromptSubmit` | Context injection (first prompt only), trigger routing, doctor spawn |
| `session-end.js` | `Stop` | Auto-wrap log, wiki sync, memory indexing |
| `pre-tool-use.js` | `PreToolUse` (Bash/Write/Edit) | MewKing, TDD, audit, secrets, immutability gates |
| `agent-track.js` | `PreToolUse` (Task) | Dispatch ledger + model gate |
| `agent-track.js` | `SubagentStop` | Completion logging |
| `post-tool-use.js` | `PostToolUse` (Write/Edit) | Activity tracking, correction signals, Impeccable guard |
| `pre-compact.js` | `PreCompact` | Semantic snapshot before compaction |

### Token budget

The first prompt of a session gets one context block, hard-capped (default 3,000 tokens, `MEW_SESSION_START_MAX_TOKENS`). Static content (rules, persona) leads so it hits the prompt cache; dynamic content (status, instincts, health) follows. Per-silo whitelists keep irrelevant fields out. Over budget, whole low-priority sections are dropped — trigger instructions and the session card are never truncated. Subsequent prompts inject nothing except matched trigger instructions.

### Agent array

Specialist agents defined in `.claude/agents/`, selected by silo and task:

| Agent | Model | Role |
| --- | --- | --- |
| `mew-planner` | Opus | Architecture plans, MewKing proposals |
| `fable` | Opus | Deep codebase audits, MVP-to-production analysis |
| `mew-chief` | Sonnet | Cross-silo orchestration, standup, wiki sync |
| `mew-coder` | Sonnet | Code implementation, bug fixes, tests |
| `mew-designer` | Sonnet | UX design, Figma review, component specs |
| `mew-gamedev` | Sonnet | GDScript / Unity implementation |
| `mew-learner` | Sonnet | Concept distillation, wiki writing |
| `mew-researcher` | Sonnet | Feasibility analysis, market research |
| `mew-ideator` | Haiku | Idea capture and brief generation |
| `mew-archivist` | Haiku | Session wrap, log writes, commit messages |
| `mew-coder-simple` | DeepSeek | Straightforward implementation via LiteLLM proxy |
| `mew-coder-reason` | DeepSeek R1 | Complex reasoning tasks via LiteLLM proxy |

Every dispatch is written to a ledger; dispatches without an explicit model param are blocked (the silent-Sonnet-fallback fix). `mew agent status` shows what ran, when, on which model. DeepSeek agents go through `mew dispatch` + the LiteLLM proxy — not the Agent tool.

### Semantic memory (doobidoo)

SQLite-vec + Ollama embeddings, exposed as an MCP server. `mew wiki sync` re-indexes mewwiki automatically in the background, and every session is instructed to consult memory before substantive work — past decisions and gotchas resurface instead of rotting in the vault.

### Instinct system

Corrections become rules. When the same file is rapidly rewritten 3+ times, a candidate instinct lands in `instincts/pending/` (deduped per topic, queue capped). Promote with `mew instinct promote <id>`; promoted instincts inject at every session start.

---

## Installation

### Requirements

|  | macOS | Windows |
| --- | --- | --- |
| Python | 3.11+ — `brew install python` | `winget install Python.Python.3.12` |
| Node.js | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| Git | `brew install git` | `winget install Git.Git` |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | same |
| Obsidian | [obsidian.md](https://obsidian.md) | same |
| Ollama *(optional)* | `brew install ollama` — semantic search | [ollama.com](https://ollama.com/download) |

### Steps

```bash
# 1. Clone and install the CLI
cd ~/Jan                       # your workspace root
git clone <this-repo> mewvault
cd mewvault && pip3 install -e .

# 2. Environment variable (~/.zshrc or $PROFILE)
export MEWVAULT_ROOT="$HOME/Jan/mewvault"

# 3. Register hooks
mew harness install

# 4. Bootstrap silos
mew init

# 5. Bootstrap MewWiki, then open it in Obsidian as a vault
mew wiki init --path ~/Jan/mewwiki

# 6. First sync
mew wiki sync

# 7. (optional) Semantic search
ollama pull nomic-embed-text
pip install mcp-memory-service   # then add doobidoo to .mcp.json (see mcp-configs/)

# 8. Verify
mew check      # interactive sanity check
mew doctor     # automated health monitor
```

Then open Claude Code in the workspace and say **standup**.

### Upgrading

```bash
mew update      # or say "update the vault" in Claude Code
```

One command: stashes your personal files (log.md, statuses), pulls fast-forward-only, reinstalls the CLI, re-registers hooks, restores your files, and verifies with doctor. Your projects and mewwiki live in separate repos — an engine update can never touch them.

---

## CLI reference

### Health & visibility

| Command | Description |
| --- | --- |
| `mew doctor [--json --quiet --notify]` | 15-check health monitor (auto-runs each session) |
| `mew dashboard [--watch N] [--no-open]` | HTML overview: projects, health, agent activity |
| `mew agent status [--limit N]` | Agent dispatch ledger |
| `mew usage --report [--days N]` | Token usage + cache-hit ratio from transcripts |
| `mew check` | Interactive installation sanity check |

### Quality

| Command | Description |
| --- | --- |
| `mew ci install [--project NAME]` | CI safety net into code projects |
| `mew design tokens --diff [--project NAME]` | Figma variables vs DESIGN.md drift |
| `mew package <project> [--design]` | Client package; `--design` = full handoff |
| `mew validate [--fix]` | Project_Status.md schema compliance |

### Workspace & projects

| Command | Description |
| --- | --- |
| `mew status [--quick --stale N --project NAME]` | Vault/project status |
| `mew new <type> <name> [--stack next]` | Scaffold (includes CI, specs/, tests/) |
| `mew promote / archive / abandon / rename` | Project lifecycle |
| `mew sync [--commit "msg" --push --pr]` | Git across all silos |
| `mew wiki init / sync [--dry-run]` | MewWiki bootstrap and sync (+ auto re-index) |
| `mew secret set/get/list/rotate KEY` | Secrets (never in git, never echoed) |
| `mew instinct status / promote / prune` | Instinct pipeline |
| `mew agent list / invoke / sync` | Agent array |
| `mew dispatch --agent mew-coder-simple --task "…"` | DeepSeek via LiteLLM proxy |
| `mew harness install / status / disable` | Hook management |

---

## Tier gates

Every project carries a `tier` in `Project_Status.md`:

- **Pounce** — small tasks (<2h). Write directly; TDD warns only.
- **Stalk** — multi-session features. Verbal plan approval; TDD gate blocks.
- **MewKing** — architecture/risky. Hard gate: no code until `plan_approved: true` in Project_Status.md; enforced at OS level; two blocked attempts auto-write `REVIEW_REQUIRED.md`.

## Project layout

```
<silo>/<project>/
  Project_Status.md   # tier, phase, next_action, audit fields, spec_approved
  specs/              # acceptance-criteria specs (spec-driven pipeline)
  tests/              # written before src/ (TDD gate)
  proposals/active/   # MewKing plans
  src/                # source
  raw/                # briefs, PRDs — immutable
  wiki/               # concept pages (flow to mewwiki)
  log.md              # session log (flows to mewwiki)
```

Silo-specific layouts vary (learn-lab has `decks/` and `journal/`; career-studio has `cv/`, `cases/`, `brand/`) — see each silo's `CLAUDE.md` for the full structure.

---

*Changelog for the 2026-07-08 overhaul: `wiki/whats-new-2026-07-08.md`.  
learn-lab silo added 2026-07-13. career-studio silo added 2026-07-10.*
