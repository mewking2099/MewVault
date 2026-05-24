# Code Silo Rules

You are working in `software-projects/`. These rules apply in addition to mew-common.

## Project layout

```
software-projects/<project>/
  Project_Status.md     # tier, current_phase, stack, open_threads, plan_approved
  proposals/active/     # MewKing plans
  src/                  # source code
  tests/                # test files
  raw/                  # specs, PRDs — immutable
  wiki/                 # architecture decisions
  log.md
```

## Before writing code

- Check `current_phase` in Project_Status.md. If MewKing tier, `plan_approved` must be `true`.
- Check `open_threads` — do not start new work if a blocking thread is unresolved.
- For src/ and lib/ files, check whether a test file exists. If not, write the test first (TDD warning fires automatically via the PreToolUse hook).

## Stack conventions

- `next` → Next.js + Tailwind + TypeScript
- `astro` → Astro + Tailwind + TypeScript
- `sveltekit` → SvelteKit + Tailwind + TypeScript

Follow the stack's established patterns. Do not introduce new dependencies without noting them in the session wrap.

## Commits

- Never auto-commit. User pushes manually.
- Commit messages are suggested in `.claude/last-session-message.txt` after each session.
