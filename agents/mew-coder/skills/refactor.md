---
name: refactor
triggers: [refactor, clean up, simplify, reduce duplication, extract, rename]
description: Safe refactor with verification gate — no behaviour changes
inject: on-trigger
---

# Skill: Refactor

**Rule: refactoring must not change observable behaviour.**

Steps:
1. Read all files to be changed.
2. Confirm the refactor type: extract function / rename / deduplicate / simplify.
3. Make changes.
4. Run tests — they must all still pass.
5. Grep callers for renamed symbols — update all references.
6. Re-read changed files once more before reporting done.

**Do not introduce new features during a refactor.** If you spot something worth
improving beyond the scope, note it in the session wrap as a follow-up task.
