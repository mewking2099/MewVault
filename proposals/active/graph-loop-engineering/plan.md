---
tier: MewKing
plan_approved: true
current_phase: 4
feature: graph-loop-engineering
owner: Mohabbat
created: 2026-08-27
approved: 2026-08-29
status: IN PROGRESS
depends_on:
  - proposals/active/model-routing-enforcement/ISSUE.md
---

# Plan: Graph & Loop Engineering for MewVault Agent Orchestration

## Tier: MewKing
## Status: PENDING APPROVAL

## Overview

MewVault has a graphify per-silo knowledge graph and a growing agent array, but the routing layer never consults the graph, dispatches are not audited, and existing loops (session → wrap → prime, spec → build → verify, plan → approve → execute) run unmonitored. This plan lands three interlocking capabilities: (1) enforce model routing so verifier/generator differentiation is real, (2) unify a dispatch ledger with loop-tick nodes as a single graph-native schema for policy audit, (3) introduce blast-radius + complexity routing and instrumented loop primitives on top of that schema. No adaptive learning is proposed — this is heuristic surfacing and policy audit only.

## Non-negotiable framing

- This is **policy audit + heuristic surfacing**, not learning, not adaptive routing.
- The single load-bearing bet: **ledger schema (dispatch rows) and loop-tick nodes are ONE schema**, versioned by `graph_epoch`. Everything else derives from getting that schema right on day one.
- Instrument existing loops before inventing new ones.

---

## Phases

### Phase 0 — Model routing enforcement (blocking prerequisite)

**Goal:** Every agent dispatch runs on the model its manifest declares, or fails loud. Until this holds, every downstream loop is a rubber stamp because verifier and generator collapse onto the same Sonnet.

**Deliverables**
- Consolidate `proposals/active/model-routing-enforcement/ISSUE.md` (already scoped) into this MewKing plan's Phase 0 or leave as-is and cross-reference. Decision recorded in Open Decisions §D-0.
- Ship Option A end-to-end for all Claude-family agents (short-alias `model:` param passed on every `Agent()` call, per `mewvault/CLAUDE.md` §Agent dispatch table).
- Ship Option B for DeepSeek agents: `mew dispatch` routing via LiteLLM proxy wired into the dispatch flow so that `mew-coder-simple` and `mew-coder-reason` never fall back to Sonnet silently.
- Add a self-report line at the start of every agent turn: `[model=<actual>]` so shadow-mode analysis in later phases has ground truth for `model_actually_run`.
- Add a lint / preflight in `mew/commands/` that scans `.claude/agents/*` and warns if any manifest model has no dispatch path.

**Acceptance criteria (termination predicates)**
- [ ] 20 consecutive dispatches across ≥4 distinct agents log a `model_actually_run` value that matches the manifest's intended family (opus / sonnet / haiku / deepseek).
- [ ] Attempting to dispatch a DeepSeek agent with the LiteLLM proxy down returns an explicit error, not a silent Sonnet fallback.
- [ ] Option C (custom SDK dispatch layer) is explicitly deferred with a written rationale, or promoted to Phase 0.5 with its own acceptance criteria.

**Risks**
- Option C creep — mitigation: cap Phase 0 at Options A+B; Option C requires a separate MewKing addendum.
- Claude Code `Agent` tool short-alias limitation is upstream — mitigation: document the ceiling in `mewvault/CLAUDE.md` and treat sub-version pinning as an accepted limitation, not a bug to chase.

---

### Phase 1 — Unified ledger + loop-tick schema (B + C together)

**Goal:** Persist every dispatch and every loop tick as graph-native rows/nodes under one schema, versioned by `graph_epoch`. This is the load-bearing bet: schema wrong at row 1 pollutes all downstream analysis.

**Deliverables**
- Schema definition file: `mewvault/mew/ledger/schema.sql` (or `.py` if using Pydantic + SQLite CTEs) covering:
  - `dispatch` rows: `(task_hash, graph_epoch, dispatch_ts)` composite PK, `agent`, `model_intended`, `model_actually_run`, `silo`, `project_lock`, `tools_used[]`, `tokens_in`, `tokens_out`, `outcome_class`, `parent_dispatch_ts` (for nested `Agent()` calls).
  - `loop_tick` nodes: `(loop_id, tick_n, graph_epoch)` PK, `loop_type` (spec_build_verify | plan_approve_execute | idea_lifecycle | wrap_prime | custom), `predicate_state`, `content_hash`, `embedding_ref`, `no_progress_streak`, terminates on `terminated_reason ∈ {predicate_met, max_ticks, no_progress_cap, human_escalation, error}`.
  - Foreign keys: `loop_tick.dispatch_ts → dispatch.dispatch_ts` (a tick may spawn 0..N dispatches; a dispatch belongs to 0..1 ticks).
- Migration harness: `mew ledger migrate` command, idempotent, with `graph_epoch` bump on any schema change.
- Storage engine: **SQLite with recursive CTEs** as the default. Kuzu is the documented escape hatch — see Architecture Decisions §A-3.
- Outcome verification taxonomy (documented in `mewvault/wiki/ledger-outcome-taxonomy.md`), ranked highest → lowest confidence:
  1. `test_pass` — CI or `pytest`/`vitest` green after the dispatch's changes
  2. `graph_diff_match` — post-dispatch `graphify update` produced the predicted delta
  3. `human_accept` — user typed `approved` / merged the PR / advanced the phase
  4. `self_report` — agent claimed success with no external verification (lowest)
- Instrument existing dispatches: back-fill `mew dispatch`, the `Agent()` wrapper, and the wrap→prime handoff to write ledger rows. No new loop primitives yet.
- Read-only surface: `mew ledger tail`, `mew ledger show <task_hash>`, `mew ledger stats`. No routing queries yet.

**Acceptance criteria (termination predicates)**
- [ ] 100 real dispatches recorded end-to-end (composite PK holds, no null `model_actually_run`, no null `graph_epoch`).
- [ ] A schema migration from epoch N → N+1 runs cleanly on a populated DB in dev; row counts preserved.
- [ ] `mew ledger stats` reports outcome-class distribution and % of dispatches with each verification tier.
- [ ] At least one existing loop (recommend: wrap → prime) is fully instrumented with `loop_tick` rows for 10 consecutive sessions.

**Risks**
- Schema-first / feature-later feels slow — mitigation: this is the entire non-negotiable bet from Synthesis 3; do not shortcut.
- Composite PK collisions if `task_hash` is derived from prompt text only — mitigation: hash `(prompt, agent, silo, graph_epoch)` together; document in schema.
- SQLite hits its ceiling on variable-length path queries — mitigation: engine trigger documented (§A-3); Kuzu migration path pre-mapped.
- Prompt-injection surface via ledger read-back into future briefs — Phase 1 does NOT read ledger into any prompt. Read-back is Phase 3, gated on §D-3.

---

### Phase 2 — Baseline measurement + graph confidence surface (no router yet)

**Goal:** Before writing any routing code, establish the actual mis-routing rate and per-silo graph confidence. Skipping this = building on a phantom.

**Deliverables**
- `mew route --dry-run <task>` — shadow-mode only. Predicts (agent, model, silo, blast-radius bucket, complexity bucket). Records prediction to ledger. Does NOT dispatch.
- Human choice capture: when the user then dispatches something (via any path), reconcile against the last dry-run prediction on that task_hash and record `predicted_vs_actual` divergence.
- Per-silo graph confidence score written into `graphify-out/confidence.json` per silo. Inputs: node count, edge density, recency of last `graphify update`, orphan ratio. Buckets: `high | medium | low | insufficient`.
- Silo auto-lock (Synthesis 1 decision D): when a dispatch reads from a silo other than the locked one, ledger records the cross-silo read; a warning is surfaced. No enforcement yet.
- Baseline report: `mew route baseline` — after ≥100 recorded dispatches with paired dry-run predictions, produces the mis-routing rate breakdown by silo, task class, and confidence bucket.

**Acceptance criteria (termination predicates)**
- [ ] 100 dispatches with paired `mew route --dry-run` predictions logged.
- [ ] Baseline report shows mis-routing rate per silo and per confidence bucket, with a written interpretation.
- [ ] At least one silo is identified as `insufficient` confidence (expected: game-lab experiments with <10 files) and explicitly documented as "default routing only" going forward.

**Risks**
- Users skip `--dry-run` because it feels ceremonial — mitigation: make the wrap-time summary include a "you had N dispatches, 0 predictions this session" nudge for the first two weeks.
- Ground-truth-for-correctness is noisy (cost proxy / diff quality / retry count all have known bias) — mitigation: report all three separately, do not synthesize a single "accuracy %" number.
- Cross-silo tasks (dsaas + yaana-DS) fail the single-silo assumption — mitigation: ledger records `silo_read_set[]`; router in Phase 3 asks the user rather than picking silently. See §D-2.

---

### Phase 3 — Blast-radius + complexity routing on live dispatch

**Goal:** With the ledger, baseline, and confidence surface in place, ship real routing that uses graph neighborhood (blast radius) and complexity score together — never radius alone. Fail loud on low confidence; never silently.

**Deliverables**
- Capability edges added **inside** the graphify graph as a new edge type: `capability(agent → node_type | task_class)`, versioned by `graph_epoch`. Not a sidecar file. (Architecture Decisions §A-2.)
- Blast-radius predictor: graph-neighborhood expansion from predicted target nodes (2-hop default, tunable). Records `predicted_radius` and later `actual_radius` (from post-dispatch graphify delta) as distinct fields in the ledger. Never conflated.
- Complexity score: file-count × dependency-depth × cyclomatic-hint from graph node metadata. Weighting is a fixed heuristic, documented in `wiki/routing-heuristics.md`.
- Two-stage retrieval for routing context (Synthesis 3): **graph-neighborhood first, then vector rerank**. Graph answers "what is adjacent to the task's target nodes?"; doobidoo vector answers "have we done this before?".
- Explicit fallback: if silo confidence is `low` or `insufficient`, the router emits `graph confidence low, using default routing (<default agent>)` — a visible, ledgered message, never silent.
- Cold-start bootstrap: new silos inherit a global prior distribution derived from the aggregate ledger, decaying as local dispatches accumulate. Surface state as `calibrating` in `mew route status`.
- Cross-silo scope guard: routing may READ any silo's graph only via a federation function `route.read_graph(silo, task_hash)` that records the cross-silo read into the ledger. Direct file reads across the project lock remain blocked by the existing hook.

**Acceptance criteria (termination predicates)**
- [ ] Router recommendations agree with baseline heuristics on ≥N% of a held-out slice of the Phase 2 sample (N to be set in §D-3 before phase start — do NOT invent a number here).
- [ ] Every dispatch under Phase 3 records both `predicted_radius` and `actual_radius`; divergence report available via `mew route drift`.
- [ ] Low-confidence fallback message is visible and ledgered in ≥1 test scenario per confidence bucket.
- [ ] Cross-silo read via `route.read_graph` is logged distinctly from same-silo reads.

**Risks**
- Radius/complexity weights are picked from a small sample — mitigation: keep weights in `wiki/routing-heuristics.md`, versioned; changes bump `graph_epoch`.
- Users perceive router as authoritative — mitigation: every recommendation is prefixed `[router suggests]` with a one-line rationale; user override is the norm, not the exception.
- Graphify snapshot→streaming mismatch (Synthesis 3 open question): loop-tick nodes are written mid-session but graphify is batch-rebuild — mitigation: Phase 3 does NOT write loop-tick nodes back into graphify's `graph.json`. Ledger is the sole home for tick rows. Migration to streaming is deferred (see §Deferrals).

---

### Phase 4 — Instrumented loop primitives + termination discipline

**Goal:** With routing and ledger stable, add first-class support for the loops that already exist in the codebase — spec → build → verify (TDD), plan → approve → execute (MewKing), seed → exploring → validated → promoted (idea-hub). Never invent new loops here; instrument the ones already running.

**Deliverables**
- `mew loop start <loop_type> <task>` — opens a `loop_id`, writes tick 0 with `predicate_state` derived from the loop type's known predicate (see below).
- `mew loop tick <loop_id>` — records tick n+1. Computes `content_hash` (canonicalized diff/output) and `embedding_ref` (doobidoo). Increments `no_progress_streak` if content_hash matches tick n-1 OR embedding distance < ε.
- Termination predicates per loop type (fixed, non-negotiable — do NOT ship fuzzy loops in Phase 4):
  - **spec_build_verify:** all acceptance criteria in the spec have a passing test → terminate `predicate_met`.
  - **plan_approve_execute:** `plan_approved: true` AND every deliverable in the plan has an artifact link → `predicate_met`.
  - **idea_lifecycle:** `status ∈ {promoted, archived}` → `predicate_met`.
  - **wrap_prime:** wrap doc written AND next-session brief written → `predicate_met`.
- Universal caps (livelock guards, per Synthesis 2):
  - `max_ticks` per loop type (default 8; overridable in `~/.mew/loop-caps.yaml`).
  - `max_no_progress_ticks` = 3 → escalate to human with a diagnostic dump.
- Livelock detector: graph-cycle prefilter over the `loop_tick → dispatch → loop_tick` subgraph + content-hash/embedding-distance check on tick output. Cycle alone is not livelock; cycle + no-progress is.
- Advisory brief injection (Synthesis 2 resolved decision): wrap → prime survives, but as **advisory** with provenance `(session_id, model_actually_run, verified_vs_claimed)`, contradiction-checked against MASTER_SPEC before injection. Never authoritative context.
- Concurrency: `ScheduleWakeup` and any background tick fires the sequence `check project lock → if locked and human-active, defer one tick → log deferral to ledger`. See Synthesis 2.
- Anti-pattern declared in `mewvault/CLAUDE.md`: **never dispatch an agent in a retry loop against another agent's output on the same model family.** Enforced at planning time by mew-planner, not at runtime.

**Acceptance criteria (termination predicates)**
- [ ] Each of the four fixed loop types has a passing example run recorded in the ledger with an explicit termination reason (not just `max_ticks`).
- [ ] Livelock detector fires on a synthetic oscillation scenario (two ticks with matching content_hash) and correctly escalates.
- [ ] Wrap→prime brief injection includes provenance fields on every run for one week of sessions.
- [ ] ScheduleWakeup deferral is exercised at least once against a live project lock and logged.

**Risks**
- Fuzzy loops (refactor, "make it good", bug-hunt) demand fuzzy predicates — mitigation: explicitly deferred to a Phase 5 proposal (§Deferrals). Phase 4 ships only the four fixed loop types.
- Parallel one-shots often beat sequential loops (Synthesis 2) — mitigation: `mew loop start` prints a "consider parallel dispatch instead" hint when the loop type is one of the known parallelizable classes.
- Verifier-weaker-than-generator laundering — mitigation: Phase 0 must hold; if verifier and generator resolve to the same model family, ledger flags `verifier_family_collision: true` and the loop refuses to start without `--override`.

---

## Explicit deferrals (out of scope, with rationale)

- **Adaptive routing / learned policy.** Framing across all three syntheses: this is a personal vault, not a training set. Ledger drives heuristic surfacing only. Anywhere the codebase or docs use "learning" language, replace with "heuristic accumulation".
- **Mid-task re-routing.** Cut per Synthesis 1: handoff cost + style drift + ratchet exploit. Loops re-plan between ticks; individual dispatches run to completion on their chosen agent.
- **MASTER_SPEC as automatic loop-termination signal.** Deferred per Synthesis 3: observer-effect risk that users write specs to satisfy automation. Requires a separate decision doc before any implementation.
- **Kuzu migration.** Deferred until SQLite recursive-CTE query patterns are demonstrably insufficient. Trigger conditions documented in §A-3.
- **Fuzzy-loop primitives** (refactor, "make it good", exploratory bug-hunt). Deferred to a Phase 5 proposal — Phase 4 ships only loops with a clean predicate.
- **Graphify streaming rebuild.** Loop-tick nodes stay in the ledger, not in `graph.json`, until graphify supports incremental updates. Migration path is a separate MewKing.
- **Cross-silo routing intersection.** When a task genuinely spans two silos (e.g. dsaas + yaana-DS), the router asks the user rather than picking. Enforcement-level federation is deferred; Phase 3 only *records* cross-silo reads.
- **Option C (custom SDK dispatch layer) for model routing.** Phase 0 ships Options A+B; Option C requires its own MewKing addendum. This is called out here so it does not silently slip into Phase 0 scope.

---

## Open decisions (must resolve before the labeled phase can start)

- **§D-0 (blocks Phase 0):** Consolidate `proposals/active/model-routing-enforcement/ISSUE.md` into this plan's Phase 0, or leave as a linked sibling proposal? Recommendation: leave as sibling, cross-reference. Owner to confirm.
- **§D-1 (blocks Phase 1):** Composite PK hash inputs — is `(prompt_text, agent, silo, graph_epoch)` sufficient, or must we also include `parent_dispatch_ts` to distinguish nested `Agent()` calls with identical prompts? Recommendation: include `parent_dispatch_ts`.
- **§D-2 (blocks Phase 2):** For cross-silo tasks, does the router fail loud and ask, lock to the intersection, or dispatch to a designated cross-silo agent (none currently exists)? Recommendation: fail loud and ask.
- **§D-3 (blocks Phase 3):** What is the acceptable router-vs-baseline agreement threshold? Do not invent this — set it after Phase 2 baseline data is in hand.
- **§D-4 (blocks Phase 3):** Can `mew-chief` verify `mew-coder` competently when both run on Sonnet? If not, the plan needs a differential-review skill against acceptance criteria before verifier-family-collision is auto-flagged as safe.
- **§D-5 (blocks Phase 4):** Prompt-injection surface for auto-injected briefs — is this a real risk on a single-user personal vault, or theoretical? Answer determines whether provenance-check is advisory or blocking.
- **§D-6 (cross-phase):** Does iterative retrieval measurably beat single-hop doobidoo on this corpus? If not, the two-stage retrieval in Phase 3 simplifies to graph-only.

---

## Architecture decisions (non-negotiable)

- **§A-1: Ledger and loop-tick share ONE schema.** They are joined by foreign key, versioned by `graph_epoch`, and migrated together. Splitting them = stranded oscillation detection (Synthesis 3).
- **§A-2: Capability edges live inside the graphify graph.** New edge type `capability(agent → node_type | task_class)`. No sidecar `capability.json`. Versioned with the graph.
- **§A-3: Storage is SQLite (recursive CTEs) by default; Kuzu is the escape hatch.** Migration trigger: any of (a) a single ledger query on the target machine exceeds 500ms after indexing; (b) a variable-length path query requires >3 recursive-CTE layers to express; (c) cycle detection over `loop_tick` needs graph-native traversal. Any one trigger opens a Kuzu MewKing addendum.
- **§A-4: Composite primary key on dispatch rows.** `(task_hash, graph_epoch, dispatch_ts)`. Set at row 1 or the entire analysis surface is polluted.
- **§A-5: `predicted_radius` and `actual_radius` are distinct columns.** Never overwritten, never conflated.
- **§A-6: Loop-tick nodes are ledger-native, not graphify-native.** Until graphify supports streaming, tick rows stay in SQLite. Graphify sees them only via export snapshots.
- **§A-7: Advisory-only cross-context.** Ledger read-back into briefs is always advisory, contradiction-checked against MASTER_SPEC, tagged with provenance. Never injected as authoritative context.
- **§A-8: Framing.** No file, prompt, comment, or doc in this feature uses the words "learn", "adaptive", "training", or "model improvement". This is heuristic accumulation and policy audit.

---

## Files

### Created
- `mewvault/proposals/active/graph-loop-engineering/plan.md` — this file
- `mewvault/mew/ledger/__init__.py` — package
- `mewvault/mew/ledger/schema.sql` — canonical schema (§A-1, §A-4)
- `mewvault/mew/ledger/migrations/` — versioned migrations, one file per `graph_epoch` bump
- `mewvault/mew/commands/ledger.py` — `mew ledger {migrate, tail, show, stats}`
- `mewvault/mew/commands/route.py` — `mew route {--dry-run, baseline, status, drift}`
- `mewvault/mew/commands/loop.py` — `mew loop {start, tick, status}`
- `mewvault/mew/routing/blast_radius.py` — graph-neighborhood expansion
- `mewvault/mew/routing/complexity.py` — complexity score heuristic
- `mewvault/mew/routing/confidence.py` — per-silo graph confidence
- `mewvault/mew/loops/predicates.py` — the four fixed termination predicates
- `mewvault/mew/loops/livelock.py` — cycle + content-hash detector
- `mewvault/wiki/ledger-outcome-taxonomy.md` — verification tier doc
- `mewvault/wiki/routing-heuristics.md` — versioned heuristic weights
- `mewvault/wiki/loop-primitives.md` — the four loop types + caps
- `graphify-out/confidence.json` (per silo) — written by `mew route confidence`

### Modified
- `mewvault/CLAUDE.md` — add the anti-pattern declaration (Phase 4), add `mew ledger`/`mew route`/`mew loop` to the command list, restate "no adaptive routing" framing
- `mewvault/mew.py` — register new command modules
- `.claude/agents/*/manifest.yaml` — no schema changes; ensure `model:` is consistent with the dispatch table in `mewvault/CLAUDE.md`
- Wrap → prime handoff (existing session-end hook) — emit ledger row + provenance-tagged advisory brief instead of raw injection
- `mew dispatch` — write ledger rows on every DeepSeek dispatch
- `.gitignore` — add `.mew-ledger.db*` (SQLite + WAL + SHM)

### Deleted
- None in this plan. Any deletion (e.g. legacy dispatch paths that bypass the ledger) will be proposed in a follow-up Pounce after Phase 1 lands.

---

## Risks (plan-level)

- **Scope creep from routing → learning.** Guarded by §A-8 framing rule; enforced by mew-planner reviews of any downstream proposal.
- **Schema migrations are expensive.** Guarded by shipping schema in Phase 1 before any consumer, and by `graph_epoch` versioning.
- **User loses trust if the router feels wrong early.** Guarded by explicit low-confidence fallback message (Phase 3), and by never routing silently.
- **Loop primitives get used for fuzzy tasks they weren't designed for.** Guarded by refusing `mew loop start` for any `loop_type` outside the fixed four; fuzzy loops explicitly deferred.
- **Verifier/generator collapse re-emerges after Phase 0.** Guarded by `verifier_family_collision` flag in Phase 4 loop-start check.

---

## Success criteria (plan-level, verifiable)

- [ ] Phase 0: 20 consecutive dispatches with correct `model_actually_run`.
- [ ] Phase 1: 100 dispatches recorded end-to-end with composite PK holding; one clean epoch migration.
- [ ] Phase 2: Baseline mis-routing report exists, per-silo confidence buckets populated, at least one silo flagged `insufficient`.
- [ ] Phase 3: `predicted_radius` vs `actual_radius` drift report available; low-confidence fallback exercised and ledgered.
- [ ] Phase 4: Each of the four fixed loop types has one full recorded run terminating on `predicate_met` (not on `max_ticks`); livelock detector fires on synthetic oscillation.
- [ ] Zero occurrences of "learn", "adaptive", "training" in shipped code, docs, or command output.
- [ ] Every phase's deliverables are cross-linked from `Project_Status.md` before the next phase starts.

---

## Rollback

Each phase is independently reversible; rollback is per-phase, not big-bang.

- **Phase 4 rollback:** disable `mew loop *` commands, keep ledger reads. Loops revert to un-instrumented (their pre-plan state).
- **Phase 3 rollback:** disable `mew route` recommendation output; keep `--dry-run` shadow mode and ledger writes. Manual dispatch continues.
- **Phase 2 rollback:** disable `mew route --dry-run`; remove `graphify-out/confidence.json`. Ledger unaffected.
- **Phase 1 rollback:** the nuclear case. Requires (a) exporting the ledger to a JSONL archive at `mewvault/.mew-ledger-archive/`, (b) removing `.mew-ledger.db`, (c) reverting the wrap→prime and `mew dispatch` instrumentation. Schema definitions stay in the repo for a future re-land.
- **Phase 0 rollback:** revert Agent-tool `model:` params and `mew dispatch` LiteLLM wiring. Documented as an anti-goal — Phase 0 rollback re-breaks every downstream loop and should only be considered if a critical upstream Claude Code change forces it.

Rollback is a described procedure, not an automated command. A human executes each step.
