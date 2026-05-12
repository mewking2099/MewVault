# Meeting Prep

Pull context for an upcoming meeting: attendee profiles, last meeting notes, open items, suggested agenda.

## Arguments

`$ARGUMENTS` is the meeting topic or person name (e.g. `/meeting-prep vodafone negotiation` or `/meeting-prep Sarah Chen`).

## Steps

Read the mewwiki path from `mewvault/.mewwiki`.

**1. Identify meeting**

If Google Calendar MCP is available, search for upcoming meetings that match `$ARGUMENTS` (by title or attendee). Surface the next match: date, time, attendees.

If Calendar MCP is not available: ask "When is the meeting and who's attending?" Skip gracefully.

**2. Load attendee profiles**

For each attendee name identified, check `mewwiki/Operations/People/<Name>.md`. Load role, org, recent notes.

If no profile exists, note: "No profile for <Name> — consider creating one after the meeting via /dump."

**3. Find last meeting note**

Search `mewwiki/Operations/Meetings/` for the most recent note matching the topic or attendees. Extract:
- Date of last meeting
- Decisions made
- Open action items (lines with `- [ ]`)

**4. Load project context** (if relevant)

If the meeting relates to an active project, read its `Project_Status.md` from the silo: current_phase, blockers, next_action.

**5. Output brief**

```
## Meeting Prep — <topic>
<date and time if known>

### Attendees
| Name | Role | Org |
|------|------|-----|
...

### Last meeting (<date>)
Decisions: ...
Open items: ...

### Project context
Phase: ... | Blockers: ...

### Suggested agenda
1. <open item from last meeting>
2. <current blocker>
3. ...
```

Keep it to one screen. Offer to open the People profiles in the editor if the user wants more detail.
