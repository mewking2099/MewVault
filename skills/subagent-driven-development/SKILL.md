---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
origin: superpowers
---

# Subagent-Driven Development

Execute a plan by dispatching a fresh subagent per task, with two-stage review after each: spec compliance first, then code quality.

**Core principle:** Fresh subagent per task + two-stage review = high quality, fast iteration.

**Continuous execution:** Do not pause between tasks to check in. Execute all tasks from the plan without stopping. The only reasons to stop: BLOCKED status you cannot resolve, genuine ambiguity, or all tasks complete.

## When to Use

- You have a written implementation plan
- Tasks are mostly independent
- You want to stay in the current session (use `executing-plans` for a fresh session)

## The Process

### 1. Load Plan
Read plan file, extract all tasks with full text, create a task list with TodoWrite.

### 2. Per-Task Loop

For each task:

**a) Implementer subagent**
```
Dispatch with: task text + relevant file context + constraints
Wait for: implementation + self-review summary
```

**b) Spec reviewer subagent**
```
Dispatch with: task spec + implemented code diff
Confirm: does code match every requirement in the spec?
If gaps: send back to implementer, re-review
```

**c) Code quality reviewer subagent**
```
Dispatch with: implemented code
Check: naming, readability, no dead code, follows project conventions
If issues: send back to implementer, re-review
```

**d) Mark task complete** in TodoWrite.

### 3. Final Review

After all tasks: dispatch a final code reviewer across the entire implementation.

### 4. Finish

Use `verification-before-completion` before claiming done.

## Model Selection

| Role | Model |
|------|-------|
| Mechanical implementation (1-2 files, clear spec) | Haiku |
| Multi-file, judgment required | Sonnet |
| Architecture, design, review | Opus |

## Subagent Prompt Rules

- **Never pass session history** — construct exactly what the subagent needs
- **One clear goal** — implementation or review, not both
- **State constraints explicitly** — which files NOT to touch
- **Specify output format** — what should the subagent return?
