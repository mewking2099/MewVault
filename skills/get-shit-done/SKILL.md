---
name: get-shit-done
description: Spec-driven development loop with context management — prevents context rot on long-running features. Use when starting a new feature from requirements, or when a complex task needs a structured plan-then-execute loop with fresh context.
origin: gsd-build
---

# Get Shit Done

A spec-driven development loop designed to prevent context rot on complex features. Core insight: quality degrades as the context window fills. GSD solves this by planning in full context, then executing in fresh context.

**Use this when:** Starting a new feature from requirements (not a quick bug fix — use `systematic-debugging` for that).

**Relationship to other skills:**
- Broader than `writing-plans` + `executing-plans` — GSD includes requirements discovery, codebase mapping, and phased roadmaps
- More structured than `subagent-driven-development` — GSD manages context across sessions, not just within one

## The Six-Step Loop

### 1. Map Codebase (if existing project)

Before anything, understand what you're working with:
```
- Read key entry points and config files
- Map the component tree / module structure
- Identify conventions: naming, error handling, testing patterns
- Note what NOT to change
```
Output: a mental model of the codebase, stored in session or a context file.

### 2. Gather Requirements

Turn vague requests into specific requirements:
- What does "done" look like? (acceptance criteria)
- What are the constraints? (performance, backwards compat, deadlines)
- What's out of scope?
- What are the gray areas that need decisions?

Ask all questions in ONE message. Don't drip-feed questions.

### 3. Build Roadmap

Break the feature into independent phases, each small enough to execute in a fresh context window:

```markdown
## Roadmap: [Feature Name]

**Phase 1:** [Component — can be built and tested independently]
**Phase 2:** [Component — depends only on Phase 1 contract, not implementation]
**Phase 3:** [Integration]
```

Each phase = one context window. If a phase needs 3+ sessions to implement, split it.

### 4. Discuss Before Planning (per phase)

For each phase, surface decisions before planning:
- Layout choices, API shapes, error handling strategies
- Data structures, state management approach
- What reasonable defaults vs. what needs explicit decision

Output: a decisions document. This becomes the source of truth for the plan.

### 5. Plan Each Phase

Write a detailed implementation plan for the current phase:
- Files to create/modify
- Step-by-step tasks (bite-sized, 2–5 min each)
- Test-first: write failing tests before implementation
- Verification steps

Use `writing-plans` skill format for the plan document.

### 6. Execute in Fresh Context

**CRITICAL:** Start a new conversation for execution. Pass only:
- The plan document path
- The decisions document
- Any essential context (project conventions, key files)

Do NOT carry the full planning conversation into execution. This is what prevents context rot.

Use `executing-plans` or `subagent-driven-development` to implement.

## Context Management Rules

- **Plan in full context, execute in fresh context**
- When switching phases: start a new session, load plan + decisions only
- If you feel the context getting heavy (quality degrading, repeated mistakes): compact or start fresh
- Never "just add one more thing" to a phase — scope creep kills context efficiency

## Quick Trigger

When the user says "let's build [feature]" or "I need [complex thing]":
1. Ask: existing codebase or greenfield?
2. Map codebase (if existing)
3. One message with all questions
4. Build roadmap
5. Discuss Phase 1 decisions
6. Write plan
7. Tell user: "Ready. Start a fresh session and pass this plan: `proposals/active/<feature>/plan.md`"
