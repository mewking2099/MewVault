# Tier Gates

Every project carries a tier field in Project_Status.md. The tier determines how much autonomy Claude has before writing code.

## Pounce (small tasks, <2 hours)

- No plan required.
- Write directly. Wrap at session end.

## Stalk (multi-session features)

- Propose approach in chat before starting.
- User approves in conversation (no formal plan.md required).
- Write after verbal approval.

## MewKing (architecture / risky changes)

- **Hard gate**: Claude may NOT write any code until `plan_approved: true` in Project_Status.md.
- Create `proposals/active/<feature>/plan.md`. Present it. Wait.
- The PreToolUse hook enforces this at OS level (exit code 2). Trying to bypass it will fail.
- After approval: set `plan_approved: true` in Project_Status.md, then proceed.
- Every MewKing session ends with a structured wrap: log entry + suggested commit message.

## Gate violations

- Each blocked attempt increments `gate_block_count` in Project_Status.md.
- After 2 blocks, `proposals/active/<feature>/REVIEW_REQUIRED.md` is written automatically.
