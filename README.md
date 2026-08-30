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

MewVault turns Claude Code into a managed, multi-discipline workspace. Work is organised into independent git **silos** — software, design, games, knowledge, ideas, learning, and career. The right context is injected automatically at session start. Quality is enforced with hard gates that block at the OS level, not with instructions that can be reasoned around.

**MewWiki** is the read layer — an Obsidian vault that stays current automatically. Decisions, session logs, and distilled knowledge flow into it at session end, get semantically indexed, and resurface in future sessions when relevant.

```
workspace-root/
  mewwiki/              # Obsidian vault — auto-updated, semantically indexed
  mewvault/             # This repo — CLI, hooks, agents, gates
  software-projects/    # Code projects (Next.js, Astro, SvelteKit)
  design-studio/        # UX and design projects (Figma-integrated)
  game-lab/             # Godot / Unity games and experiments
  idea-hub/             # Idea capture and validation
  learn-lab/            # Skill acquisition — language SRS + trading (stage-gated)
  career-studio/        # Private silo — case studies, CV, skill matrix, mock interviews
  wiki/                 # Knowledge base and learning tracks
```

---

## Technology stack

| Layer | Technology |
|---|---|
| **CLI engine** | Python 3.11+, PyYAML, setuptools (editable install via `pip install -e .`) |
| **Hook runtime** | Node.js (CommonJS) — 7 lifecycle hooks registered with Claude Code |
| **Linting** | Ruff (pycodestyle, pyflakes, isort, naming, pyupgrade) |
| **Memory — full-text** | SQLite FTS5 (built-in, zero external deps) |
| **Memory — session** | SQLite-vec + Ollama (`nomic-embed-text`) + doobidoo MCP server |
| **Memory — project index** | ChromaDB (persistent, `~/.mew/chroma/`) + sentence-transformers (`all-MiniLM-L6-v2`) — auto-built at session end |
| **Graph engine** | graphify (AST-based knowledge graph, `graphify-out/graph.json` per project) |
| **AI models** | Claude Sonnet (implementation, design, coordination), Claude Opus (planning, audits, ideation), Claude Haiku (capture, archiving) |
| **Alternative models** | DeepSeek V3 / R1 via LiteLLM proxy (optional, for cost-sensitive tasks); GLM-5.2 via Z.ai (ideation cross-critique) |
| **SRS scheduler** | Python SM-2 algorithm (`scripts/srs.py`) |
| **Design system** | Impeccable v3 (`impeccable.style`) |
| **Figma integration** | Figma MCP (`get_design_context`, `get_screenshot`, `use_figma`) |
| **Wiki** | Obsidian vault with auto-sync |
| **CI** | GitHub Actions (typecheck, lint, tests, build, dependency audit) |
| **macOS notifications** | `osascript` — health alerts, doctor findings |
| **Skills** | Markdown-based skill files in `.agents/skills/` |

---

## No commands to memorise

Everything is a plain conversational sentence. The session hook detects the phrase and routes it automatically.

| Say | What happens |
| --- | --- |
| **standup** | Morning brief: projects, calendar, PRs, inbox, unresolved Figma comments |
| **wrap up** | Session end: verified Definition-of-Done, log, wiki sync, commit suggestion |
| **dump — we decided X** | Classifies and routes the note (decisions carry Figma provenance) |
| **spec user-billing** | Spec-driven workflow: acceptance criteria → your approval → tests → code |
| **design session myproject** | Impeccable setup: context, PRODUCT.md check, lane, Figma pull |
| **critique https://…** | Severity-ranked design critique from pixels (works on competitors) |
| **weekly review** | Digests the week's logs into memory, nudges stale projects |
| **doctor** / **is everything ok** | Runs the 15-check health monitor and explains any findings |
| **dashboard** | Generates and opens the HTML vault overview |
| **agent status** | Did agents actually run, and on which model |
| **token report** | Per-day token usage + cache-hit ratio |
| **token drift** | Figma variables vs DESIGN.md diff |
| **prepare handoff myproject** | Assembles the client-ready design package |
| **install ci** | Drops the CI safety net into code projects |
| **sync wiki** | Silos → mewwiki, then semantic re-index |
| **ingest raw/spec.pdf** | Proposes concept pages, writes them on approval |
| **meeting prep topic** | Attendee profiles + last notes + agenda |
| **brief \<topic\>** | Total-context pack: ranked excerpts from wiki, decisions, specs, logs (2k cap) |
| **validate \<idea\>** | Feasibility scan: competitors, market size, effort estimate, pursue/park/kill |
| **practice japanese** | SRS drill (due cards only) → new grammar point → micro-conversation |
| **market prep** / **trade — \<details\>** | Trading track: journal entry, adherence review, backtest logging |
| **case study \<name\>** | Career: retro interview or auto-assembly from vault receipts |
| **mock interview** | Grounded questions from real vault history; scored feedback |

---

## How tokens are saved

Token budget discipline is the single most important operational concern. MewVault enforces it at multiple levels.

### Session injection cap

The first prompt of every session receives exactly one context block, hard-capped at **3,000 tokens** (configurable via `MEW_SESSION_START_MAX_TOKENS`). The `session-start.js` hook builds this block in a strict priority order:

```
1. Static rules (mew-common + current silo rules)   ← injected first, hits prompt cache
2. Trigger instructions (matched phrases only)
3. Session card (project status, next action, active agents)
4. Instincts (promoted corrections from past sessions)
5. Health warnings (doctor findings, if any)
6. Dynamic state (instinct queue size, MCP surface)
```

Static content leads so it lands in Anthropic's prompt cache on every turn. Dynamic content follows. Over budget, entire low-priority sections are dropped — trigger instructions and the session card are never truncated. Subsequent prompts inject nothing at all except matched trigger phrases.

### Cache safety

A hard rule, learned the expensive way: **never put a compressing or rewriting proxy between Claude Code and the Anthropic API.** Cache reads cost ~0.1× input tokens. Any proxy that mutates the prompt prefix re-bills the full conversation on every turn, silently destroying cache hits. The `doctor` command actively detects this class of tool via `ANTHROPIC_BASE_URL` inspection and alerts immediately. Optimize by injecting less, never by transforming the prompt. Full story: `wiki/headroom-postmortem.md`.

### Per-silo whitelisting

Each silo (code, design, game, idea, learn, career) has its own whitelist of which Project_Status.md fields to include in the session card. Irrelevant fields from other silos never enter context.

### `mew usage`

Reports actual token consumption and cache-hit ratio by parsing real Claude Code transcript files — not estimates. Run `mew usage --report` to see per-day breakdowns and identify sessions where cache missed.

---

## How memory is saved and used

MewVault has two memory layers that work together.

### Layer 1 — Full-text memory (SQLite FTS5)

Built into Python's standard library. No external database. Stored at `.mew-memory.db` in the workspace root (gitignored).

**Schema:**
```
entries (id, type, silo, project, source_path, title, body, tags, created_at, updated_at)
entries_fts (virtual FTS5 table — title + body, auto-synced via triggers)
```

**Entry types:** `decision`, `concept`, `session_log`, `spec`, `note`

**How it gets populated:**
- `mew memory sync` walks mewwiki and indexes every markdown file as an entry
- `session-end.js` fires automatically at session stop, triggering a background sync
- `mew wiki sync` syncs silo logs and wiki pages, then re-indexes

**How it's used:**
- `mew memory search "<query>"` — BM25 full-text search, returns ranked excerpts
- `mew brief <topic>` — searches memory + wiki, assembles a 2,000-token context pack of ranked, relevant excerpts
- Claude Code consults memory at session start for cross-session continuity

### Layer 2a — Session memory (SQLite-vec + Ollama + doobidoo)

Semantic recall at the cross-session level. Requires Ollama running locally with `nomic-embed-text` pulled.

**Stack:**
- `sqlite-vec` extension — vector storage and cosine similarity search inside SQLite
- `ollama` — local embedding inference, no API cost, no data leaving the machine
- `doobidoo` MCP server — exposes `memory_search`, `memory_store`, `memory_harvest`, `memory_health`, and a dozen other tools directly to Claude Code

**How it gets populated:**
- `mew memory sync` generates embeddings for each entry and stores them in sqlite-vec
- `doobidoo` MCP tools allow Claude to store and retrieve observations directly during a session
- `memory_harvest` ingests new wiki content in bulk

**How it's used:**
- Claude Code calls `memory_search` at session start via the doobidoo MCP server
- Past decisions, architectural choices, and corrections resurface automatically when semantically relevant
- `memory_conflicts` and `memory_quality` tools let Claude self-audit the memory store for contradictions

### Layer 2b — Project knowledge graph index (ChromaDB)

Semantic index of every file in the active project. Runs automatically — no Ollama required.

**Stack:**
- `ChromaDB` — persistent vector store at `~/.mew/chroma/` (one collection per project)
- `sentence-transformers` (`all-MiniLM-L6-v2`) — local CPU-friendly embeddings, no external API

**How it gets populated:**
- `session-end.js` chains `graphify update . && mew index build <active-project>` as a detached background shell after every session that touches files
- `post-tool-use.js` triggers the same chain after significant file writes
- `mew index build [--all]` rebuilds manually if needed
- New projects with no index are flagged with a ⚠ alert in the session card

**How it's used:**
- `mew index search "<query>"` returns ranked file excerpts by semantic similarity
- `mew route blast-radius <node>` uses ChromaDB for Stage 2 semantic expansion (beyond the BFS hop graph)
- `mew brief <topic>` merges ChromaDB hits with FTS5 results for a richer context pack
- `mew dispatch` consults the index for routing confidence before choosing an agent

```bash
mew index build               # build for locked project
mew index build --all         # rebuild all silo projects
mew index status              # show per-project index freshness
mew index search "token budget"  # semantic search
```

### Auto-save memory file

In addition to the database, Claude Code maintains a file-based auto-memory at `.claude/projects/<path>/memory/` — markdown files per memory type (user, feedback, project, reference), indexed in `MEMORY.md`. This layer is always active, even without Ollama.

---

## Graph-aware routing

Every `mew dispatch` call passes through a three-stage routing pipeline before choosing an agent or model.

### Stage 1 — Blast radius (what does this task touch?)

**BFS hop graph** (`mew/routing/blast_radius.py`) walks the project's `graphify-out/graph.json` up to 2 hops from the anchor node, collecting every file in the neighbourhood. This is the structural impact estimate — what could break.

**Semantic expansion** (`vector_index.search()`) extends that neighbourhood using ChromaDB: files whose content is semantically similar to the task description are added to the blast radius even if they're not adjacent in the graph. Together, BFS + semantic gives a more honest picture than graph topology alone.

```bash
mew route blast-radius "mew/commands/dispatch.py"  # show 2-hop + semantic neighbourhood
```

### Stage 2 — Complexity scorer

`mew/routing/complexity.py` scores the blast radius: `file_count × community_span × type_diversity`. High scores route to Opus; low scores stay on Sonnet or Haiku. Community span penalises tasks that cross module boundaries — those are the risky ones.

### Stage 3 — Capability registry

`mew/routing/capability.py` matches the task against a registry of agent capability edges (`graphify-out/capability-edges.json`) — "which agent has successfully handled tasks touching these file types before?" Confidence is computed from the registry, and low-confidence routes are flagged before dispatch.

### Project-based graph resolution

All routing commands resolve the graph path with `_project_graph_path()`:
1. `<locked-project>/graphify-out/graph.json` — project-specific graph (most accurate)
2. `<silo>/graphify-out/graph.json` — silo-level fallback
3. `/dev/null` — routing still works, just without graph data

```bash
mew route dry-run "add pagination to the sessions list"  # predict agent + model without dispatching
mew route baseline                                        # record current routing decisions
mew route status                                          # shadow-mode delta vs baseline
mew route confidence                                      # per-silo confidence scores
```

---

## Dual-model ideation (`mew ideate`)

`mew ideate` runs a structured two-model debate loop: GLM-5.2 (via Z.ai) and Claude Opus critique each other's analysis, then Opus synthesises. This isn't conversational brainstorming — it's adversarial, cross-model pressure-testing.

**Loop shape:**

```
Round 0:  GLM analysis   ↘
                          → Round 1 cross-critique (each model reviews the other)
Round 0:  Opus analysis  ↗
                          → Opus synthesis (weighs both, resolves conflicts)
                          → saved to --write-dir if provided
```

**When to use it:** positioning decisions, PRD risk analysis, feature expansion, README evaluation, architecture tradeoffs — anything where a single-model answer might be overconfident.

```bash
mew ideate "should we use pg_cron or Vercel Cron for background jobs?" \
  --write-dir proposals/active/cron-decision/
```

Synthesis files land in `--write-dir` as `synthesis.md`. Z.ai SSL timeouts are intermittent — if round 1 fails twice, deliver analysis directly from the available context rather than retrying indefinitely.

---

## Loop primitives (`mew loop`)

Four loop types for autonomous multi-step work, with built-in safeguards against runaway agents.

| Loop type | Shape | Use for |
|---|---|---|
| `spec_build_verify` | spec → build → verify → iterate | TDD cycles on known specs |
| `plan_approve_execute` | plan → approval gate → execute | MewKing features needing human sign-off |
| `research_synthesise` | search → draft → critique → revise | Feasibility analysis, wiki writing |
| `design_critique_refine` | design → Impeccable audit → refine | UI work with P0 gate |

**Termination predicates** (`mew/loops/predicates.py`): each loop type has a fixed set of conditions that signal completion — tests green, P0s clear, synthesis stable, plan approved. Loops stop when predicates are met, not when they run out of tokens.

**Livelock detection** (`mew/loops/livelock.py`): content-hash streaks (same output 3× in a row) and graph cycle detection halt loops that are spinning without progress.

**Caps** (`~/.mew/loop-caps.yaml`): per-loop-type `max_ticks` and `max_no_progress` limits. Exceeding either stops the loop and writes a summary to the ledger.

**Verifier-generator collision rule (§A-8):** Never dispatch a verifier on the same model family as the generator. A Sonnet verifier cannot catch errors a Sonnet generator made — it produces false `predicate_met` signals. `mew loop start` checks for family collision at start time and halts unless `--override` is passed.

```bash
mew loop start spec_build_verify --anchor "user-auth"
mew loop tick <loop-id>       # manual tick (usually called by agents)
mew loop status <loop-id>     # current predicate state + tick count
mew loop list                 # all active loops
```

---

## Dispatch ledger (`mew ledger`)

Every agent dispatch is recorded — model used, task hash, blast radius, confidence score, tick count, outcome. The ledger is the audit trail for routing decisions.

```bash
mew ledger migrate   # initialise / migrate schema
mew ledger tail      # live-tail recent dispatches
mew ledger show <id> # full record for one dispatch
mew ledger stats     # per-agent, per-model, per-silo summaries
```

The ledger database lives at `.mew-ledger.db` (gitignored). `mew agent status` is the human-facing summary; `mew ledger` is the raw record.

---

## How the instinct system works

Instincts are the mechanism by which corrections become permanent rules.

### Detection

The `post-tool-use.js` hook fires after every file write (`Write`, `Edit` tool calls). It tracks rewrites of the same file within a session. When the same file is rewritten **3 or more times rapidly**, the hook writes a candidate instinct to `instincts/pending/`:

```json
{
  "id": "prefer-named-exports-over-default",
  "topic": "module exports",
  "correct_behavior": "Use named exports. Default exports make refactoring harder.",
  "triggered_by": "src/components/Button.tsx rewritten 4 times",
  "confidence": 0.75,
  "created_at": "2026-07-21T14:23:00Z"
}
```

Candidates are deduplicated by topic — the same correction doesn't stack up as multiple files.

### Queue management

- `instincts/pending/` is capped. When it overflows, `doctor` flags it as a warning.
- `mew instinct status` shows all pending candidates ranked by confidence score (0.0–1.0)
- Candidates with confidence ≥ 0.80 are marked `→ promote?`

### Promotion

```bash
mew instinct promote <id>   # moves to instincts/promoted/
mew instinct prune          # removes low-confidence pending candidates
```

Promoted instincts are loaded by `session-start.js` and injected into every future session's context block. They appear under a `## Instincts` section and are treated as hard rules, not suggestions.

### Effect

A promoted instinct is indistinguishable from a hand-written rule from Claude's perspective. The difference is it was derived from observed behaviour rather than typed manually. Over time, the instinct set accumulates the specific quirks and preferences of your codebase and workflow without any explicit maintenance.

---

## The gates (enforcement over advice)

Every gate is a `PreToolUse` hook that exits with code 2 — Claude Code sees a blocked tool call and cannot proceed. There is no workaround, no "please ignore this rule" escape.

| Gate | Rule |
| --- | --- |
| **MewKing** | No code on architecture-tier projects until `plan_approved: true` in Project_Status.md. Two blocked attempts auto-write `REVIEW_REQUIRED.md`. |
| **TDD** | On Stalk/MewKing projects, no source file without a corresponding test file. Tests must derive from the spec's acceptance criteria. Opt out per-project with `tdd: off`. |
| **Audit** | Design projects can't move to handoff/delivery while `open_p0 > 0` in Project_Status.md. |
| **Secrets** | Writes containing key patterns (`sk-`, `ghp_`, `AKIA`, `password=`, `API_KEY=`, …) are blocked unconditionally. |
| **Immutability** | `raw/` directories and direct writes to `mewwiki/` are blocked. Corrections go through the wiki sync pipeline. |
| **Model routing** | Agent dispatches via the Agent tool without an explicit `model` parameter are blocked. Prevents the silent Sonnet fallback where every specialist agent runs on the default model regardless of its manifest. |
| **Impeccable bans** | UI file writes containing side-stripes (`border-left/right > 1px` as accent), gradient text (`background-clip: text`), glassmorphism, identical card grids, tracked uppercase eyebrows, oversized radii (`> 16px`), or ghost-cards are flagged back into context instantly via `post-tool-use.js`. |
| **Unity editor writes** | Blocked in Unity game projects — the hybrid contract requires Claude to write code, humans to do all editor work. |

---

## Health: `mew doctor`

Fifteen automated checks run unattended — from the `session-start.js` hook on the first prompt of every session, or on demand.

**Checks:**

| Check | What it catches |
|---|---|
| `cache_safety` | `ANTHROPIC_BASE_URL` set to a mutating proxy — the silent cache-killer |
| `hook_matchers` | PreToolUse/PostToolUse matchers scoped too broadly (`""` matches everything) |
| `hooks_registered` | All 7 lifecycle hooks present in Claude Code settings |
| `injection_size` | Session-start output within token budget and error-free |
| `instinct_queue` | `instincts/pending/` not overflowing (cap: 20) |
| `signal_file` | `correction-signals.json` not growing unbounded |
| `mcp_surface` | Number of always-on MCP servers (each adds to every prompt's token cost) |
| `ollama` | Embedding backend reachable (only checked if doobidoo is configured) |
| `index_freshness` | Semantic index not older than the newest wiki content |
| `wip_limits` | Maximum 3 active projects, none idle 21+ days |
| `ci_presence` | Code projects have a CI workflow |
| `secrets_dir` | `secrets/` exists and has correct permissions (0600) |
| `plan_files` | MewKing projects have a plan.md before `plan_approved: true` |
| `spec_files` | TDD-on projects have spec files before source |
| `stale_instincts` | Pending instincts older than 30 days without promotion |

Doctor writes machine-readable output to `.claude/doctor-status.json`. Problems trigger a macOS notification and are injected into the next session's context block as a `## Vault Health` section, so you're told what's wrong before you ask.

```bash
mew doctor            # human output
mew doctor --json     # machine output; exit 0/1/2 = ok/warn/fail
mew doctor --quiet    # problems only
mew doctor --notify   # macOS notification on warn/fail
```

---

## Hook runtime

Seven lifecycle hooks, registered once with `mew harness install` and written to Claude Code's settings:

| Hook | Event | Role |
| --- | --- | --- |
| `session-start.js` | `UserPromptSubmit` | Context injection (first prompt only), trigger routing, doctor spawn, new-project graph alert |
| `session-end.js` | `Stop` | Auto-wrap log, wiki sync, memory indexing; chains `graphify update . && mew index build <project>` (detached) |
| `pre-tool-use.js` | `PreToolUse` (Bash/Write/Edit) | MewKing, TDD, audit, secrets, immutability gates |
| `agent-track.js` | `PreToolUse` (Task) | Dispatch ledger + model gate |
| `agent-track.js` | `SubagentStop` | Completion logging |
| `post-tool-use.js` | `PostToolUse` (Write/Edit) | Activity tracking, correction signals, Impeccable ban detector; triggers `graphify update . && mew index build` (detached) |
| `pre-compact.js` | `PreCompact` | Semantic snapshot before compaction |
| `unity-guard.js` | `PreToolUse` | Blocks Unity editor writes (MCP) in Unity game projects |

All hooks are Node.js (CommonJS) so they run with the same Node binary Claude Code already ships — no separate runtime dependency.

---

## Agent array

Specialist agents defined in `.claude/agents/`, each with a fixed model assignment. The session-start hook injects the recommended agent for the current silo.

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
| `mew-coder-simple` | DeepSeek V3 | Straightforward implementation via LiteLLM proxy |
| `mew-coder-reason` | DeepSeek R1 | Complex reasoning tasks via LiteLLM proxy |

Every dispatch is written to a ledger. The model gate (`agent-track.js`) blocks any Agent tool call without an explicit `model` parameter — the silent-Sonnet-fallback that made every specialist agent run identically regardless of its manifest is closed. `mew agent status` shows what ran, when, and on which model.

DeepSeek agents go through `mew dispatch` + the LiteLLM proxy, not the Claude Code Agent tool. The proxy is optional — MewVault works without it.

---

## Spec-driven development (software silo)

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

`mew ci install` backfills the GitHub Actions workflow (typecheck, lint, tests, build, dependency audit) into existing projects. New scaffolds include it automatically.

---

## Design silo (Impeccable v3)

All frontend work — in any silo — follows the [Impeccable](https://impeccable.style) loop:

1. **Init** — `PRODUCT.md` (audience, constraints) + `DESIGN.md` (decisions, tokens)
2. **Iterate** — named commands: `/impeccable typeset|layout|colorize|animate|polish|bolder|quieter`
3. **Pre-ship gauntlet** — `audit` (P0–P3 scores), `clarify` (microcopy vs audience), `harden` (long strings, i18n, offline, 500s)
4. **Maintain** — `extract` (consolidate repeated patterns into tokens), `document` (re-capture DESIGN.md)

MewVault makes it stick:
- `post-tool-use.js` runs the absolute-ban detector on every UI file write
- Audit scores persist to `Project_Status.md`
- The audit gate blocks handoff while P0s are open
- `mew design tokens --diff` shows Figma variable drift vs DESIGN.md
- `mew package <project> --design` assembles the full handoff package
- `critique <url>` gives a severity-ranked pixel-level design review

---

## Learn-lab silo

Two independent skill-acquisition tracks with hard discipline rules.

**Language track (SM-2 SRS)** — `scripts/srs.py` implements the SM-2 spaced repetition algorithm. Only cards that are due enter context — never the full deck. Reference data (JMdict, KANJIDIC2) lives locally; every card is verified against it before use, never LLM-invented. Session shape: drill due cards → one new grammar point + 3 generated i+1 sentences → micro-conversation → wrap (scheduler re-runs, streak increments).

**Trading track (stage-gated)** — Five stages: `curriculum → backtest → rulebook → demo → live`. MewVault refuses to assist beyond the current stage. The journal is append-only — enforced by the pre-tool-use hook which blocks any write that isn't a bash `>>` append. Backtests require 50 logged setups + ≥60% accuracy before advancing. Reviews grade adherence, not P&L. The vault is a discipline coach and pattern analyst — never a signal generator, never financial advice.

---

## Career-studio silo

Private, offline-only git repo. No remote ever added; excluded from wiki sync, briefs, and semantic indexing. Publishing is an explicit export step, never a side effect.

**Case study pipeline:** `assembled → drafted → publishable`. `drafted` requires a voice pass (owner edited the draft; patterns written to `brand/voice.md`). `publishable` requires `confidentiality: cleared` — hook-blocked otherwise. Clearing = owner approves a named-entity checklist Claude extracts from the draft.

**Skill matrix** — five pillars (Design / Product / Development / AI & Tooling / Leadership). Levels above 2 require evidence links from vault work. `skill review` quarterly. Weekly review nudges the most dormant pillar with one concrete, real-work-tied activity.

**Mock interviews** — questions grounded in real vault history (actual decisions, shipped work). Monthly cadence; `mew doctor` warns when overdue.

**CV** — `cv/master.md` is canonical; role-targeted variants derive from it. `refresh cv` mines vault logs and case studies for new accomplishments.

---

## Tier gates

Every project carries a `tier` in `Project_Status.md`:

- **Pounce** — small tasks (<2h). Write directly. TDD warns but doesn't block.
- **Stalk** — multi-session features. Verbal plan approval in conversation; TDD gate blocks source-without-test.
- **MewKing** — architecture or risky changes. Hard gate: no code until `plan_approved: true`. Enforced at OS level. Two blocked attempts auto-write `proposals/active/<feature>/REVIEW_REQUIRED.md`.

---

## Project layout

```
<silo>/<project>/
  Project_Status.md   # tier, phase, next_action, audit fields, spec_approved, plan_approved
  specs/              # acceptance-criteria specs (spec-driven pipeline)
  tests/              # written before src/ (TDD gate)
  proposals/active/   # MewKing plans (plan.md required before plan_approved: true)
  src/                # source
  raw/                # briefs, PRDs — immutable (writes blocked by hook)
  wiki/               # concept pages (flow to mewwiki at wrap)
  log.md              # session log (flows to mewwiki at wrap)
```

Silo-specific layouts vary — `learn-lab` has `decks/` and `journal/`; `career-studio` has `cv/`, `cases/`, `brand/`. See each silo's `CLAUDE.md` for the full structure.

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

### Quality & enforcement

| Command | Description |
| --- | --- |
| `mew ci install [--project NAME]` | CI safety net into code projects |
| `mew design tokens --diff [--project NAME]` | Figma variables vs DESIGN.md drift |
| `mew package <project> [--design]` | Client package; `--design` = full handoff |
| `mew validate [--fix]` | Project_Status.md schema compliance |
| `mew instinct status / promote / prune` | Instinct pipeline management |

### Workspace & projects

| Command | Description |
| --- | --- |
| `mew status [--quick --stale N --project NAME]` | Vault and project status |
| `mew new <type> <name> [--stack next]` | Scaffold (includes CI, specs/, tests/) |
| `mew promote / archive / abandon / rename` | Project lifecycle |
| `mew sync [--commit "msg" --push --pr]` | Git across all silos |
| `mew wiki init / sync [--dry-run]` | MewWiki bootstrap and sync (+ auto re-index) |
| `mew memory sync / search / recall / purge` | Memory store operations |
| `mew secret set/get/list/rotate KEY` | Secrets (never in git, never echoed) |
| `mew brief <topic>` | Ranked context pack from wiki + memory |
| `mew dispatch --agent mew-coder-simple --task "…"` | DeepSeek via LiteLLM proxy |
| `mew harness install / status / disable` | Hook management |
| `mew agent list / invoke / sync` | Agent array management |

### Graph-aware routing

| Command | Description |
| --- | --- |
| `mew route dry-run "<task>"` | Predict agent + model without dispatching |
| `mew route baseline` | Record current routing decisions as baseline |
| `mew route status` | Shadow-mode delta vs baseline |
| `mew route confidence` | Per-silo routing confidence from graph + ChromaDB |
| `mew route blast-radius "<node>"` | 2-hop BFS + semantic neighbourhood for a file |

### Project knowledge index

| Command | Description |
| --- | --- |
| `mew index build [--all]` | Build / rebuild ChromaDB index for locked project (or all) |
| `mew index status` | Per-project index freshness and size |
| `mew index search "<query>"` | Semantic search across project files |

### Ideation & loops

| Command | Description |
| --- | --- |
| `mew ideate "<question>" [--write-dir PATH]` | Dual-model GLM + Opus debate loop with synthesis |
| `mew loop start <type> [--anchor NODE]` | Start a supervised agent loop |
| `mew loop tick <id>` | Manual tick (usually called by agents) |
| `mew loop status <id>` | Predicate state, tick count, livelock risk |
| `mew loop list` | All active loops |
| `mew ledger migrate / tail / show / stats` | Dispatch ledger management |

---

*2026-07-08 overhaul changelog: `wiki/whats-new-2026-07-08.md`*  
*Graph-loop-engineering additions (2026-08-29): mew ideate, mew loop, mew ledger, mew route, mew index, ChromaDB project index, two-stage blast radius, project-based graph resolution, automated graphify + index hooks.*
