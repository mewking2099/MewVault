# Project New

Scaffold a new project in the correct silo and create its mewwiki mirror immediately.

## Arguments

`$ARGUMENTS` may contain a project slug (e.g. `/project-new rate-calc`). If empty, ask.

## Steps

**1. Gather info** (ask for anything not provided in $ARGUMENTS)
- Slug (kebab-case, e.g. `rate-calc`)
- Full name (human-readable)
- Silo: `software`, `design`, or `game`
- Stack (if software): `next`, `astro`, or `sveltekit`
- North star: one sentence — what does "done" look like?
- Tier: `pounce` (small), `stalk` (multi-session), `mewking` (architecture)

Ask all at once — one message, numbered list. Wait for answers before proceeding.

**2. Scaffold the silo project**

Run the appropriate `mew new` command:
- Software: `python mew.py new code-project <slug> --stack <stack>`
- Design: `python mew.py new ux-project <slug>`
- Game: `python mew.py new game-project <slug>`

Report the output.

**3. Create mewwiki mirror immediately** (don't wait for sync)

Read the mewwiki path from `mewvault/.mewwiki`.

Create `mewwiki/Projects/<slug>/index.md`:
```markdown
---
project: <slug>
silo: <silo>
status: active
stack: <stack or empty>
tier: <tier>
current_phase: kickoff
last_session: <today YYYY-MM-DD>
synced: <today YYYY-MM-DD>
---

# <Full name>

**Status**: active
**Phase**: kickoff
**North star**: <north star>

## Blockers
_None_

## Open Questions
_None_

## Log
→ [[<slug>/log|Full log]]
```

Create `mewwiki/Projects/<slug>/log.md`:
```markdown
---
project: <slug>
---

# <Full name> Log

Append-only. Newest on top.

## Entries

- **<today>** — Project created. North star: <north star>
```

**4. Update Brain/North Star.md**

Append to the Active Projects section:
```
- [[Projects/<slug>/index|<Full name>]] — <north star>
```

**5. Confirm**

Print:
```
Project created: <slug>
Silo: <silo path>
Wiki mirror: mewwiki/Projects/<slug>/
Next: cd into the silo and start work. Run /wrap-up when done.
```
