---
name: risk-map
triggers: [risk, what could go wrong, potential issues, before we start, is this safe]
description: Surface risks and mitigations before implementation begins
inject: on-trigger
---

# Skill: Risk Map

Before any MewKing or Stalk implementation, produce a risk table:

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ... | low/med/high | low/med/high | ... |

**Always check for:**
- Files that will be deleted or overwritten (data loss risk)
- Hook changes that could block all future sessions (lockout risk)
- Cross-silo writes (boundary violation risk)
- Secret exposure (credential leak risk)
- `raw/` directory writes (immutability violation)
- Changes to `mewwiki/` outside of sync (direct-write violation)

Flag any risk with Impact=high as a blocker — present it to the user before proceeding.
