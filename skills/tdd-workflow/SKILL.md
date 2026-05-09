# TDD Workflow

Enforce test-first development for any code change in src/ or lib/.

## Trigger

Invoked automatically by the PreToolUse hook warning, or explicitly by the user.

## Steps

1. **Identify the unit** — what is the smallest testable behavior being added or changed?

2. **Check for existing tests** — grep for `<basename>.test.<ext>` and `<basename>.spec.<ext>` adjacent to the file, and in `__tests__/` or `tests/` parent directories.

3. **If no test exists** — write the test file first:
   - One `describe` block per module
   - At least one failing test (Red phase)
   - Name the test to describe the behavior, not the implementation

4. **Write the minimal implementation** to make the test pass (Green phase).

5. **Refactor** — improve code without changing behavior; re-run tests to confirm green.

6. **Never skip** — if a test file genuinely cannot be written (e.g., pure glue code with no logic), note the reason explicitly in the session wrap.

## Rules

- Test files live adjacent to source or in `__tests__/` / `tests/` — never in `raw/`.
- Tests are part of the PR. Do not commit implementation without tests.
- The PreToolUse hook warns (exit 0, stderr) — it does not block. Use this skill to act on the warning.
