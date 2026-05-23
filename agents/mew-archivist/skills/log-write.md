---
name: log-write
triggers: [write the log, log entry, record this, document what happened]
description: Write a single log entry to a project's log.md
inject: on-trigger
---

# Skill: Log Write

Write a single entry to `<project>/log.md`.

**Section format** (default):
```markdown
## YYYY-MM-DD — <title>

**Completed:**
- <bullet>

**Next session:**
- <next action>
```

**Bullet format** (for minor entries):
```
- **YYYY-MM-DD** — <one-line summary> [auto-wrap]
```

Rules:
- Always prepend (newest first)
- Never edit or delete existing entries
- If the log doesn't exist, create it with `# <Project> — Session Log\n\n## Entries\n\n`
