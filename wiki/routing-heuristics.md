# Routing Heuristics

_Phase 2 — keyword-based prediction. See plan §A-8: no adaptive routing, no learned weights._

**graph_epoch at last change: 1**

## Agent selection

Keyword scoring over the task prompt. Each signal set is an exact substring match (case-insensitive).

| Signal set | Signals | Routes to |
|---|---|---|
| Review | review, critique, audit, analyse/analyze, assess, evaluate, check, inspect, look at, what's wrong, what is wrong, wrong with, find bug/issue/bugs/issues, security, vulnerability/ies, feedback, is this correct, is there a bug, does this work, any issues/problems, improve this, what do you think, problem/s with | `glm-code-reviewer` |
| Coder (verbs only — no nouns) | write, implement, create, build, generate, make, add, refactor, fix, rewrite, convert, migrate, update | `glm-coder` |

**Tie-breaking:** when review_score == coder_score, default to `glm-coder`.

## Blast-radius bucket

Single pass over prompt for large-radius and small-radius signals.

| Bucket | Condition |
|---|---|
| `large` | Any large-radius signal present AND large_score >= small_score |
| `small` | Any small-radius signal present AND small_score > large_score |
| `medium` | Neither condition met (default) |

Large-radius signals: migrate, migration, refactor, redesign, rename, move, delete, remove all, restructure, rearchitect, replace, upgrade, downgrade, breaking change

Small-radius signals: fix, bugfix, typo, comment, review, check, inspect, explain, describe, what is, how does, show me

## Complexity bucket

| Bucket | Condition |
|---|---|
| `complex` | word_count > 120 OR multi-step signal count >= 3 |
| `moderate` | word_count > 40 OR multi-step signal count >= 1 |
| `simple` | neither |

Multi-step signals: then, and then, after that, also, additionally, finally, step, phase, first, second, third, implement and, create and, build and, test and

## Silo confidence buckets

Written to `graphify-out/confidence.json` per silo by `mew route confidence`.

| Bucket | Condition |
|---|---|
| `high` | edge_density >= 0.05 AND orphan_ratio < 0.30 AND age < 48h |
| `medium` | all other cases with node_count >= 5 AND edge_density > 0 |
| `low` | edge_density == 0 AND node_count >= 100; OR orphan_ratio > 0.80; OR age > 168h |
| `insufficient` | node_count < 5; OR no graph.json; OR edge_density == 0 AND node_count < 100 |

**Default routing on `low` or `insufficient`:** `glm-coder`. Message emitted: `graph confidence <bucket>, using default routing`.

## Graph-aware blast-radius (Phase 3)

When `graphify-out/graph.json` is present:
1. **Seed nodes** — keyword tokens from task (≥4 chars, stop-words removed) matched against `norm_label` and `source_file` stem
2. **Neighborhood expansion** — BFS up to 2 hops via graph edges. Falls back to seed-only when graph has no edges
3. **Count → bucket** — ≤5 = small, ≤20 = medium, >20 = large

When no graph or `confidence = insufficient`, falls back to keyword-based bucket (heuristics.py).

## Complexity scoring (Phase 3)

`score = file_count × log2(community_span + 1) × type_diversity`

Where inputs come from the neighborhood node set:
- `file_count` = distinct `source_file` values
- `community_span` = distinct `community` integer IDs (cross-module coupling proxy)
- `type_diversity` = distinct `file_type` values (code/document/rationale)

Buckets: file_count > 15 OR score > 20 → complex; file_count > 5 OR score > 5 → moderate; else simple.

## Capability edge registry (Phase 3 §A-2)

Each agent has declared `node_types`, `task_classes`, `preferred_radius`, `preferred_complexity`. Written to `graphify-out/capability-edges.json` per silo via `mew route capability`.

**Constraint:** task_class must match — capability refines within a task class, never overrides the class determination from keyword scoring.

## Change log

| Epoch | Date | Change |
|---|---|---|
| 1 | 2026-08-29 | Initial heuristics — keyword scoring only, no weights |
| 2 | 2026-08-29 | Phase 3: graph-aware blast-radius + complexity; capability edge registry |
