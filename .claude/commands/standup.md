# Standup

Morning brief. Surfaces everything you need to start the day.

## Steps

Run these in parallel, then format the brief:

**1. North Star**
Read `mewwiki/Brain/North Star.md`. Extract active focus and project list. The mewwiki path is in `mewvault/.mewwiki`.

**2. Active projects**
Read `Project_Status.md` for each active project across silos (software-projects/, design-studio/, game-lab/). For each: slug, status, current_phase, next_action, blockers.

**3. Inbox**
Count files in `mewwiki/_inbox/`. List the names if ≤5, else just count.

**4. Open PRs**
Run `gh pr list --state open --json number,title,headRefName,isDraft` for each silo that has a GitHub remote (check with `git -C <silo> remote -v`). Skip silos with no remote.

**5. Google Calendar** (skip gracefully if not connected)
If a Google Calendar MCP is available, call it for today's events. Format as time + title.

## Output format

```
## Standup — <date>

### Focus
<north star active focus>

### Active Projects
| Project | Phase | Next action | Blockers |
|---------|-------|-------------|----------|
...

### Today
<calendar events if available, else omit section>

### Open PRs
<pr list or "none">

### Inbox
<count> item(s) in mewwiki/_inbox/ waiting for review.
<names if ≤5>
```

Keep it scannable. No prose paragraphs. The whole brief should fit in a terminal screen.
