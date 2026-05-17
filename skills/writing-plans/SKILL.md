---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
origin: superpowers
---

# Writing Plans

Write comprehensive implementation plans that assume the implementer has zero codebase context. Document which files to touch, what to write, how to test it, and how to commit. Bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

**In mewvault:** Save plans to `proposals/active/<feature>/plan.md` (matches the MewKing gate convention).

## Scope Check

If the spec covers multiple independent subsystems, split into sub-plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure Section

Before listing tasks, map out which files will be created or modified and each file's responsibility. Design units with clear boundaries. Prefer smaller, focused files. Files that change together should live together.

## Task Granularity

Each step is one action (2–5 minutes):
- "Write the failing test" — one step
- "Run it to confirm it fails" — one step
- "Write minimal implementation" — one step
- "Run tests to confirm green" — one step
- "Commit" — one step

## Plan Document Template

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]

**Architecture:** [2–3 sentences on approach]

**Tech Stack:** [Key technologies]

---

## File Map
- Create: `path/to/new-file.ts` — [responsibility]
- Modify: `path/to/existing.ts` — [what changes]

---

### Task 1: [Component Name]

**Files:**
- Create: `exact/path/file.ts`
- Test: `tests/exact/path/file.test.ts`

- [ ] **Step 1: Write the failing test**
  ```typescript
  // test code
  ```
- [ ] **Step 2: Verify it fails** — `pnpm test path/to/test`
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify it passes** — `pnpm test path/to/test`
- [ ] **Step 5: Commit** — `git commit -m "feat: ..."`
```

## After Writing

Tell the user: "Plan ready at `proposals/active/<feature>/plan.md`. Use `executing-plans` or `subagent-driven-development` to implement it."

For MewKing projects: the plan must be approved (`plan_approved: true` in Project_Status.md) before implementation begins.
