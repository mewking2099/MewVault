# Meeting Capture

Record a meeting: extract decisions, action items, and person observations, then file everything.

## Arguments

`$ARGUMENTS` may contain the meeting topic or person. If empty, ask.

## Steps

Read the mewwiki path from `mewvault/.mewwiki`.

**1. Gather meeting details**

Ask in one message (skip any already in $ARGUMENTS):
- Topic / meeting name
- Date (default: today)
- Attendees (names)
- What was discussed / decided
- Any action items

**2. Parse content**

From the user's answers, extract:
- **Decisions**: sentences with "we decided", "going with", "agreed to", resolved questions
- **Action items**: tasks, follow-ups (format as `- [ ] <task> — <owner>`)
- **Person observations**: notes about specific people (tone, concerns, goals, background)

**3. Write meeting note**

Create `mewwiki/Operations/Meetings/YYYY-MM/<topic-slug>.md` using the Meeting Note template:
```markdown
---
date: <date>
attendees: [<names>]
project: <project if applicable>
type: meeting
---
# <Topic> — <date>

## Decisions
- <decision 1>
- <decision 2>

## Action Items
- [ ] <task> — <owner>

## Notes
<raw notes>

## Follow-up
<next meeting or checkpoint>
```

**4. File decisions**

For each decision, create `mewwiki/Operations/Decisions/<project>-<slug>.md` using the Decision template. Link back to the meeting note with `[[Meetings/YYYY-MM/<topic-slug>]]`.

**5. Update People profiles**

For each person observation, append to `mewwiki/Operations/People/<Name>.md` (create if doesn't exist). Include date and context.

**6. Update project wiki** (if applicable)

If the meeting relates to an active silo project and contains an architectural or API decision, offer to write a note to the silo's `wiki/` so it flows into mewwiki on the next sync.

**7. Confirm**

Print what was written:
```
Meeting captured.
Note:      mewwiki/Operations/Meetings/YYYY-MM/<slug>.md
Decisions: <N> filed
People:    <names updated>
Sync:      will appear in Projects/<project>/ on next mew wiki sync
```
