---
name: write-mewking-plan
triggers: [plan, architect, mewking, proposal, design the system, how should we build]
description: Produce a MewKing plan.md with phases, files, risks, and acceptance tests
inject: on-trigger
chains_to:
  - agent: mew-archivist
    skill: log-write
    trigger: on_complete
requires_approval: true
---

# Skill: Write MewKing Plan

When asked to plan a feature or architectural change:

1. Clarify scope — ask one question if intent is ambiguous.
2. Determine tier (Pounce / Stalk / MewKing). Only produce a plan.md for MewKing.
3. Write `proposals/active/<feature-slug>/plan.md` using this structure:

```markdown
# Plan: <feature>

## Tier: MewKing
## Status: PENDING APPROVAL

## Summary
One paragraph. What changes and why.

## Phases
### Phase N: <name>
- <deliverable>

## Files
### Created
- path/to/file — purpose
### Modified
- path/to/file — what changes
### Deleted
- path/to/file — why

## Risks
- <risk> — mitigation

## Success criteria
- [ ] <verifiable acceptance test>

## Rollback
How to undo this if it goes wrong.
```

4. Present the plan. Do NOT set `plan_approved: true` — the user does that.
5. After presenting, announce: "Set `plan_approved: true` in Project_Status.md to proceed."
