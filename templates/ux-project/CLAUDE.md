# Project: {{name}} — UX

Stack: UX/UI (Figma)
Phase: 0 — Discovery

## What to read first

1. `Project_Status.md` — current phase, next action, open questions
2. Current phase folder (e.g., `00_discovery/`)
3. Most recent completed phase folder

Older phases: only on explicit request.

## Figma sync (Phase 4)

When Phase 4 starts, say "sync figma". Claude will:
1. Read `figma_file_key` from `Project_Status.md`.
2. Call Figma MCP to fetch component metadata.
3. Write a snapshot to `04_ui/figma-snapshot.md`.

The snapshot carries forward on UX→Code promotion.

Setup: `mew secret set FIGMA_TOKEN --scope {{name}}`
Then set `figma_file_key` in `Project_Status.md` to the key from your Figma URL.

## Impeccable (frontend UI work)

When working on HTML/CSS/JS prototypes in this project:

1. Run `node .agents/skills/impeccable/scripts/context.mjs` at session start
2. If `PRODUCT.md` is missing, run `$impeccable init` first
3. Use `$impeccable <command>` for all design improvements — see `mewvault/agents/mew-designer/skills/impeccable.md` for the full command table

`PRODUCT.md` lives at the project root. Keep it updated when brand direction changes.

## Rules

- Phase transitions via "advance the phase" or on `/wrap` when artifacts look complete.
- Figma token: `mew secret set FIGMA_TOKEN --scope {{name}}`
- Findings severity in audit: critical | major | minor (required for inject flow).
