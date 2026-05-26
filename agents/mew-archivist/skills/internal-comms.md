---
name: internal-comms
triggers: [write an update, status report, project update, internal comms, team update, write a newsletter, incident report, weekly update]
description: Write internal communications — status reports, project updates, 3P updates (Progress/Plans/Problems), incident reports, FAQs, session wraps. Use whenever the user needs structured written communication about project state.
inject: on-trigger
claude_code_skills: []
source: anthropics/skills
---

# Skill: Internal Comms

Write clear, structured internal communications in formats that get read.

## When to use this skill

- 3P updates (Progress / Plans / Problems)
- Project status reports
- Session wrap summaries for stakeholders
- Incident reports
- FAQ documents
- Leadership or team updates
- Newsletter sections

## Formats

### 3P Update (Progress / Plans / Problems)

```
## [Project Name] — [Date]

**Progress** (what got done)
- [Completed item 1]
- [Completed item 2]

**Plans** (what's next)
- [Upcoming work 1]
- [Upcoming work 2]

**Problems** (blockers, risks, needs)
- [Blocker or open question]
```

### Project Status Report

```
## Status: [Project] — [Date]

**Overall**: [On track / At risk / Blocked]

**This week**: [2-3 bullet summary]

**Next week**: [2-3 planned actions]

**Blockers**: [None / list them]

**Decisions needed**: [None / list them with deadline]
```

### Incident Report

```
## Incident: [Brief title]

**Date/time**: [When it happened]
**Severity**: [Critical / High / Medium / Low]
**Status**: [Resolved / Investigating / Mitigated]

**What happened**: [2-3 sentences, factual]

**Impact**: [Who/what was affected, for how long]

**Root cause**: [What caused it]

**Resolution**: [What fixed it]

**Prevention**: [What we'll do to avoid recurrence]
```

### FAQ

```
## [Topic] — FAQ

**Q: [Question]**
A: [Direct answer. One paragraph max.]

**Q: [Question]**
A: [Direct answer.]
```

## Writing principles

- Lead with the most important thing — readers often stop at the first line
- Use bullet points for lists of 3+ items; prose for 1-2 items
- Active voice: "We shipped X" not "X was shipped"
- Specific over vague: "2 days late" not "slightly delayed"
- One paragraph per idea; white space is your friend

## MewVault context

- Session wraps → append to `log.md` with `[auto-wrap]` tag
- Status updates for mewking projects → update `Project_Status.md` fields, then write comms if needed
- Keep log.md entries to 2-3 bullet points — this is a log, not a report
