---
name: executing-plans
description: Use when you have a written implementation plan to execute, with review checkpoints at each task
origin: superpowers
---

# Executing Plans

Load plan, review critically, execute all tasks, report when complete.

**Prefer `subagent-driven-development`** when subagents are available — it provides per-task review loops and higher quality output. Use this skill for simpler plans or when working without subagent support.

## Step 1: Load and Review Plan

1. Read the plan file completely
2. Identify any questions or concerns before starting
3. If concerns: raise with the user before proceeding
4. If clear: create TodoWrite from the task list and continue

## Step 2: Execute Tasks

For each task:
1. Mark as `in_progress` in TodoWrite
2. Follow each step exactly as written (plan steps are bite-sized for a reason)
3. Run all verifications specified in the step
4. Mark as `completed`

## Step 3: Complete

After all tasks are done and verified, use `verification-before-completion` before claiming success.

## When to Stop

**Stop immediately and ask when:**
- Missing dependency or tool that blocks a step
- Plan instruction is ambiguous and can't be inferred
- Verification fails repeatedly after investigating
- Plan has a critical gap preventing you from starting

Don't force through blockers — ask.

## Rules

- Never start implementation on main/master without explicit consent
- Follow plan steps exactly — don't skip verifications
- Commit frequently as the plan specifies
- Reference other skills (e.g. `tdd-workflow`) when the plan says to
