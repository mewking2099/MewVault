# Silo: software-projects — Code

Each project is its own git repo. Each project has its own CLAUDE.md, proposals/, and decisions/.

## Project structure

```
software-projects/<project>/
├── Project_Status.md
├── CLAUDE.md              # stack, current focus, artifacts
├── proposals/
│   ├── active/<feature>/  # MewKing in-flight state
│   └── archive/<feature>/ # completed features
├── decisions/             # project-scoped ADRs (NNNN-<slug>.md)
├── docs/ux/               # promoted UX artifacts
└── openapi.yaml           # (or schema.graphql, *.proto, README Commands)
```

## The Court — tier selection

Use `/plan <feature>` — Claude proposes Pounce / Stalk / MewKing.

| Tier | When | Stages |
|---|---|---|
| Pounce | Rename, typo, copy fix, lint | Execute → Commit |
| Stalk | Endpoint, component, refactor | Plan → Code → Commit |
| MewKing | Auth, billing, payments, subsystems | Brainstorm → Spec → Plan ✋ → TDD → Execute → Review → Finalize |

**✋ = approval gate.** Nothing proceeds past Plan without explicit sign-off.

## Key files for active work

> Update at every session wrap. This is the first thing read at session start — keeps token cost low.

<!-- List 3–5 files most likely needed next session. Example:
- `src/app/(panel)/[feature]/Shell.tsx` — main shell component
- `src/lib/store.ts` — state management
- `src/app/api/[resource]/route.ts` — API handler
-->

## Rules

- Never write code before `plan.md` is approved (MewKing).
- `status.yaml` tracks in-flight MewKing state — never in conversation memory.
- API contract changes: draft fragment at Spec stage, merge at Finalize.
- Test runners: Vitest + Playwright (Next/SvelteKit), Vitest (Astro).
