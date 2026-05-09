# Verification Loop

A structured self-check loop to run after any significant code change, before reporting the task complete.

## When to use

- After implementing a feature or bug fix
- After refactoring
- After any change that touches more than one file
- When the user asks "is this done?"

## Steps

1. **Re-read changed files** — confirm the actual diff matches the intent. Do not trust memory.

2. **Run type checks** — if the project has a type checker (tsc, mypy, pyright), run it and fix any new errors.

3. **Run tests** — run the relevant test suite. If tests fail, fix before reporting complete.

4. **Check for regressions** — grep for callers of any function/class you renamed or changed signature on. Confirm they are updated.

5. **Lint** — run the project's linter if configured. Fix auto-fixable issues.

6. **Cross-file consistency** — for multi-file changes: verify imports, exports, and type contracts are consistent across all changed files.

7. **Report** — only after all steps pass, report the task complete. If any step failed and you fixed it, note what was caught.

## Rules

- Never report "done" after step 1 only.
- If tests cannot run (missing setup, CI only), say so explicitly — do not claim success.
- Verification loop results belong in the session wrap, not in a separate doc.
