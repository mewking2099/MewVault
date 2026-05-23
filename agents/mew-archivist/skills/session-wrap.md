---
name: session-wrap
triggers: [wrap, wrap up, end session, done for the day, finishing up]
description: Full session-end sequence — log, status, sync, commit suggestion
inject: on-trigger
---

# Skill: Session Wrap

Run these steps in order:

**1. Ask what happened** (if not already provided)
"What changed this session? Give me a one-line summary."

**2. Write the log entry** to the active project's `log.md`:
```
## YYYY-MM-DD — <session title>

**Completed:**
- <bullet>

**Next session:**
- <next action>
```
Prepend to the file (newest first). Never edit existing entries.

**3. Update Project_Status.md:**
- `last_session`: today's date (YYYY-MM-DD)
- `next_action`: what was identified above
- `last_wrap`: today's date

**4. Run wiki sync:**
```bash
python mew.py wiki sync
```

**5. Check inbox:** list any unrouted `mewwiki/_inbox/` items.

**6. Suggest commit message** and write to `.claude/last-session-message.txt`:
```
<type>(<scope>): <imperative summary>
```
