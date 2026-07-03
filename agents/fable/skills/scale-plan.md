---
name: scale-plan
description: Converts a fable audit into a phased, sprint-ready production roadmap. Phases work into Phase 0 (pre-launch blockers), Phase 1 (first sprint), Phase 2 (stability), Phase 3 (scale). Output saved to wiki/scale-plan.md.
type: workflow
triggers:
  - scale plan
  - production plan
  - production ready
  - mvp to production
  - make this production ready
  - scale this project
  - scalability
  - refactor plan
  - refactor roadmap
  - upgrade plan
  - what do we need to do to ship
  - roadmap to production
inject: on-trigger
chains_to: []
---

# $fable scale-plan

## What this skill does

Takes the findings from `$fable audit` and turns them into a phased, prioritised roadmap. Every item is sequenced, effort-estimated, and placed in the sprint where it belongs. Output is `wiki/scale-plan.md`.

## When to invoke

- After `$fable audit` has been reviewed and accepted by the user
- When the user says "make this production ready" or equivalent
- Can run without a prior audit but quality degrades — recommend running audit first

## Prerequisites

- `wiki/audit-<date>.md` exists (run `$fable audit` if not)
- User has reviewed the audit and confirmed the P0 list is complete

## Steps

### 1. Load the audit

Read the most recent `wiki/audit-*.md`. If multiple exist, use the most recent date.

### 2. Define "production-ready" for this project

Ask the user one question if not already clear: **"What does production mean here — public users, internal team, regulated data, specific SLA?"**

This anchors Phase 0. A hobby project and a regulated fintech have different Phase 0s.

### 3. Phase the work

| Phase | Rule |
|---|---|
| Phase 0 | Every P0 from the audit. Nothing ships without this phase complete. |
| Phase 1 | All P1s. Must be done within the first 2 weeks of real traffic. |
| Phase 2 | P2s + any P1s that slipped. Due within 3 months of launch. |
| Phase 3 | Scaling work triggered by actual load — do not over-engineer ahead of data. |

### 4. Sequence within each phase

- Identify hard dependencies (B cannot start until A is done)
- Surface any items that block multiple other items (do these first)
- Flag any item that requires irreversible action (data migrations, schema changes, infra teardowns) — these need explicit user sign-off before execution

### 5. Effort summary

At the end of each phase, tally: total S + M + L + XL items and convert to a rough engineering-week estimate.

### 6. Write the plan

Save to `wiki/scale-plan.md` using the scale plan structure from the fable system prompt.

### 7. Post-plan

- Update `Project_Status.md`: set `scale_plan` to the path, set `next_action` to the first Phase 0 item
- Tell the user: Phase 0 item count, total effort estimate, first recommended action

## diff mode (`$fable diff <audit-date>`)

Compare `wiki/audit-<audit-date>.md` against a newer audit to show:
- Which P0/P1 issues are resolved
- Which new issues have appeared
- Whether the verdict improved

Output a short `wiki/audit-diff-<old>-vs-<new>.md`.
