---
name: impeccable
triggers: [typography, typeset, color, colorize, layout, spacing, animate, motion, polish, critique, audit, bolder, quieter, distill, harden, clarify, adapt, optimize, delight, craft, shape, design review, anti-pattern, ai slop, responsive, accessibility, production ready, ui quality]
description: Invoke Impeccable design vocabulary commands for UI/UX work on frontend code
inject: on-trigger
chains_to: []
claude_code_skills: []
---

# Skill: Impeccable Design Tooling

Impeccable is the default UI/UX quality layer for all frontend work in MewVault.
Installed at `.agents/skills/impeccable/` relative to the project root.

## When to use

Use Impeccable any time the task involves:
- Typography, color, layout, spacing, motion on a real HTML/CSS/JS project
- Reviewing or auditing a frontend for quality, accessibility, or anti-patterns
- Polishing a prototype or page before handoff
- Building a new UI surface from scratch

## Command routing

| If the user says… | Run |
|---|---|
| "fix the typography / fonts feel off" | `$impeccable typeset` |
| "colors are flat / need more color" | `$impeccable colorize` |
| "spacing feels off / layout broken" | `$impeccable layout` |
| "add animations / motion" | `$impeccable animate` |
| "review this design / UX audit" | `$impeccable critique <target>` |
| "check accessibility / responsive" | `$impeccable audit <target>` |
| "final polish before shipping" | `$impeccable polish <target>` |
| "too safe / bland / boring" | `$impeccable bolder <target>` |
| "too busy / overwhelming" | `$impeccable quieter <target>` |
| "simplify this" | `$impeccable distill <target>` |
| "add edge cases / error states" | `$impeccable harden <target>` |
| "plan + build a new feature" | `$impeccable craft <feature>` |
| "plan UX before coding" | `$impeccable shape <feature>` |
| "feels generic / AI slop" | `$impeccable bolder` then `$impeccable critique` |

## Setup (run once per session before any command)

```bash
node .agents/skills/impeccable/scripts/context.mjs
```

If output says `NO_PRODUCT_MD` → run `$impeccable init` first to create PRODUCT.md.

## Hard rules

- Always run `context.mjs` before the first Impeccable command in a session
- If no PRODUCT.md exists in the project, run `$impeccable init` before any other command
- Never skip the register step (brand vs product) — it controls the entire design approach
- The absolute bans in SKILL.md apply to ALL frontend code written in MewVault:
  - No side-stripe borders (`border-left` > 1px as accent)
  - No gradient text (`background-clip: text`)
  - No glassmorphism by default
  - No identical card grids
  - No uppercase tracked eyebrows on every section
  - No `border-radius` > 16px on cards
  - No ghost-card pattern (border + wide box-shadow together)
