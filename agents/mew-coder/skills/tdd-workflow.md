---
name: tdd-workflow
triggers: [implement, build, write, new component, new function, new feature, add]
description: Test-first implementation cycle for any new src/ or lib/ file
inject: on-trigger
---

# Skill: TDD Workflow

For any new source file in `src/` or `lib/`:

1. **Write the test first** — create `<name>.test.<ext>` adjacent to or in `tests/`
2. **Run tests** — they must fail (red)
3. **Write the implementation** — minimal code to pass
4. **Run tests again** — all green
5. **Refactor** — clean up, then green again

**Test checklist before reporting done:**
- [ ] Types pass (`tsc --noEmit` or equivalent)
- [ ] Tests pass (`npm test` / `pytest` / `cargo test`)
- [ ] No regressions in callers (grep for usages, re-read them)
- [ ] Linter clean

**Never skip the test file.** If a test file is impractical (e.g. CLI entry point),
note the reason explicitly in the session wrap.
