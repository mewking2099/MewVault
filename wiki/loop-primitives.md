# Loop Primitives

_Phase 4 — four fixed loop types. Fuzzy-predicate loops deferred to Phase 5._

## The four fixed loop types

| loop_type | Predicate: met when | Max ticks (default) |
|---|---|---|
| `spec_build_verify` | All `- [x]` criteria in spec + `.tests-pass` marker (or `test_pass` in ledger) | 8 |
| `plan_approve_execute` | `plan_approved: true` in Project_Status.md AND all `- [x]` deliverables in plan.md | 6 |
| `idea_lifecycle` | `status: promoted` or `status: archived` in `ideas/<slug>/status.md` | 12 |
| `wrap_prime` | `log.md` mtime ≥ session start AND next-session brief file exists | 4 |

## Universal caps (livelock guards)

- `max_ticks` — hard ceiling per loop type. On breach: `terminated_reason = max_ticks`.
- `max_no_progress_ticks` = **3** — if `content_hash` of tick output matches the last 3 consecutive ticks: `terminated_reason = no_progress_cap`. Escalates to human with a diagnostic dump.

Override in `~/.mew/loop-caps.yaml`:
```yaml
default_max_ticks: 8
max_no_progress_ticks: 3
loop_type_caps:
  spec_build_verify: 8
  plan_approve_execute: 6
  idea_lifecycle: 12
  wrap_prime: 4
```

Any cap change is a heuristic change — document in this file and bump `graph_epoch`.

## Livelock detection

Two-part check:
1. **Content-hash streak**: `content_hash` of tick output matches for `max_no_progress_ticks` consecutive ticks → `no_progress_cap`. Cycle alone is not livelock; cycle + no-progress is.
2. **Graph-cycle prefilter**: detects `loop_tick → dispatch → loop_tick` cycles in the ledger (same `loop_id`). Additive evidence only — logged alongside the hash check, not a standalone trigger.

## Wrap→prime advisory brief injection

When `wrap_prime` terminates on `predicate_met`, the brief file gets a provenance header:
```
<!-- provenance: loop_id=<id>, tick=<n>, generated=<ts>, advisory=true,
     note=contradiction-check against MASTER_SPEC required before use -->
```

**Rule (§A-7):** Briefs are always advisory. Never injected as authoritative context without contradiction-check against MASTER_SPEC.

## Concurrency: project-lock deferral

If a background tick fires while a human is active (project lock set):
- Pass `--defer-if-locked` to `mew loop tick` — the tick prints a deferral hint.
- The deferral is advisory; it does NOT skip writing the tick row.
- Automated tick firing via `ScheduleWakeup` should check the project lock before calling `mew loop tick`.

## CLI quick reference

```bash
# Start a loop
mew loop start wrap_prime --task "end session"

# Record a tick (inline output)
mew loop tick <loop_id> --output "wrote log.md and brief"

# Record a tick (file output)
mew loop tick <loop_id> --output-file path/to/output.md

# Inject context overrides for predicate
mew loop tick <loop_id> --output "..." --ctx "log_file=path/log.md" --ctx "session_start_ts=0"

# Inspect a loop
mew loop status <loop_id>

# List all loops
mew loop list
```

## Anti-pattern (enforced at planning time by mew-planner)

> **Never dispatch an agent in a retry loop against another agent's output on the same model family.**

This is the verifier-weaker-than-generator failure mode. If both verifier and generator resolve to the same model family, the loop cannot self-correct — it produces false `predicate_met` signals.

Detection: Phase 4 `mew loop start` checks `verifier_family_collision` when the loop type is `spec_build_verify` or `plan_approve_execute`. A collision halts start unless `--override` is passed.

## Cap change log

| Date | Change | Epoch |
|---|---|---|
| 2026-08-29 | Initial caps: default 8 ticks, 3 no-progress, per-type as above | 2 |
