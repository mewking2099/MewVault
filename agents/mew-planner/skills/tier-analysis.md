---
name: tier-analysis
triggers: [what tier, which tier, pounce or stalk, is this mewking, classify this task]
description: Classify a task as Pounce / Stalk / MewKing with reasoning
inject: on-trigger
---

# Skill: Tier Analysis

Classify the requested change using these criteria:

| Tier | Duration | Risk | Examples |
|---|---|---|---|
| Pounce | < 2h | Low | Bug fix, small feature, docs update |
| Stalk | Multi-session | Medium | New feature spanning files, refactor |
| MewKing | Architecture | High | New silo, hook system change, DB schema, auth redesign |

**MewKing triggers (any of these = MewKing):**
- Changes to hook files (`hooks/*.js`)
- New CLI commands affecting harness
- Changes to how secrets are stored or accessed
- Cross-silo structural changes
- Anything touching `mewwiki/` sync logic
- Breaking changes to `Project_Status.md` schema

Output format:
```
Tier: <Pounce | Stalk | MewKing>
Reason: <one sentence>
Gate: <what's required before starting>
```
