---
name: token-audit
triggers: [token audit, design tokens, check tokens, token inconsistency, token coverage]
description: Audit design token usage — missing aliases, unused tokens, coverage gaps
inject: on-trigger
---

# Skill: Token Audit

Audit the token layer of a design system project:

**1. Coverage check**
- Every component must use `--ui-*` aliases, not raw `--brand-*` or hex values.
- Scan `src/` for hardcoded hex: `grep -r "#[0-9a-fA-F]\{3,6\}" src/`
- Scan for direct brand var usage: `grep -r "var(--brand-\|var(--yaana-" src/`

**2. Alias completeness**
- Every component's CSS vars must have a corresponding `--ui-*` alias in `aliases.css`.
- List any component that references `var(--ui-*)` tokens not defined in `aliases.css`.

**3. Dark mode**
- Any color token used in a component must have a `[data-theme="dark"]` override if the project supports dark mode.

**Output:**
```
## Token Audit: <project>

### Missing aliases (N)
- --ui-foo-bar: not defined in aliases.css (used in Button.tsx)

### Hardcoded values (N)
- #3b82f6 in Card.tsx:42 (should be --ui-card-accent)

### Dark mode gaps (N)
- --ui-nav-bg has no dark override
```
