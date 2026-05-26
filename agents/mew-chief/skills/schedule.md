---
name: schedule
triggers: [schedule this, remind me, set a reminder, every morning, recurring task, run this daily, cron job, set up a schedule, remind me to]
description: Schedule recurring or one-shot prompts using CronCreate. Use for session wrap reminders, daily standups, recurring research checks, or any timed task. Durable jobs persist across Claude restarts.
inject: on-trigger
claude_code_skills: []
source: mewvault/custom
---

# Schedule Skill

Schedule recurring or one-shot prompts via `CronCreate`. Jobs fire while Claude Code is idle.

> **Important**: Jobs auto-expire after 7 days (recurring) or fire-once (one-shot). Durable jobs survive restarts — stored in `.claude/scheduled_tasks.json`.

## Quick patterns

### Daily standup / session start reminder
```
cron: "0 9 * * 1-5"   → weekdays at 9am
cron: "7 9 * * *"     → every day at ~9am (off-the-minute to avoid fleet collision)
prompt: "Run mew standup for [project]"
durable: true
recurring: true
```

### Session wrap reminder (end of day)
```
cron: "0 18 * * 1-5"
prompt: "Remind me to /wrap the current session in mewvault"
durable: true
recurring: true
```

### One-shot reminder
```
cron: "30 14 26 5 *"   → today at 2:30pm (pin dom + month)
prompt: "Remind me to review the feasibility scan for [idea-slug]"
recurring: false
durable: false
```

### Recurring research check
```
cron: "0 10 * * 1"    → every Monday at 10am
prompt: "Check if there are new competitors for [idea-slug] and update competitor-map"
durable: true
recurring: true
```

## Cron expression reference

```
┌──────── minute (0-59)
│ ┌────── hour (0-23)
│ │ ┌──── day-of-month (1-31)
│ │ │ ┌── month (1-12)
│ │ │ │ ┌ day-of-week (0-6, 0=Sun)
│ │ │ │ │
* * * * *
```

Common expressions:
| Expression | Meaning |
|-----------|---------|
| `7 9 * * *` | Every day at ~9am |
| `0 9 * * 1-5` | Weekdays at 9am |
| `*/30 * * * *` | Every 30 minutes |
| `0 */2 * * *` | Every 2 hours |
| `0 18 * * 5` | Fridays at 6pm |

**Avoid `:00` and `:30` minutes** for approximate times — nudge a few minutes either side. Only use them when the user specifies an exact time.

## Durable vs session-only

| | Session-only (`durable: false`) | Durable (`durable: true`) |
|-|-|-|
| Survives restart | No | Yes |
| Use for | Reminders this session | Daily/weekly recurring jobs |
| Stored | Memory only | `.claude/scheduled_tasks.json` |

Use `durable: true` for any job the user expects to keep running across sessions.

## Managing jobs

After creating a job, save the returned ID:
```
Job ID: cron_abc123   ← keep this to delete later
```

List active jobs:
```
→ Use CronList to see all scheduled jobs
```

Delete a job:
```
→ Use CronDelete with the job ID
```

## MewVault scheduling patterns

### Auto-wrap reminder
Fires at end of work day to ensure sessions get wrapped and logged.
```
prompt: "Time to wrap — run /wrap for the current mewvault project and update log.md"
cron: "0 18 * * 1-5"
durable: true
```

### Idea inbox check
Weekly prompt to process any accumulated inbox items.
```
prompt: "Check idea-hub/_inbox/ — if there are any items, ask if I want to process the inbox"
cron: "0 10 * * 1"
durable: true
```

### Feasibility staleness check
Remind to refresh research after a set period.
```
prompt: "Check idea-hub/ideas/<slug>/feasibility.md — if last updated >14 days ago, suggest a refresh"
cron: "0 9 * * 3"
durable: true
```

## Notes

- Jobs only fire when Claude Code is **idle** (not mid-conversation)
- Recurring jobs auto-delete after **7 days** — re-create if needed beyond that
- One-shot jobs (`recurring: false`) auto-delete after firing
- If a job fires and the prompt is unclear — Claude will ask one clarifying question before acting
