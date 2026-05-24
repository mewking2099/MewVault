# Design Silo Rules

You are working in `design-studio/`. These rules apply in addition to mew-common.

## Project layout

```
design-studio/<project>/
  Project_Status.md     # tier, current_phase, figma_file_key, greenlit
  proposals/active/     # MewKing plans
  assets/               # exported Figma assets (never manually edited SVGs)
  raw/                  # briefs, client docs — immutable
  wiki/                 # distilled design decisions
  log.md
```

## Figma integration

- Always use the Figma MCP (`get_design_context`, `get_screenshot`) when a Figma URL is provided.
- Never manually transcribe Figma measurements — read them from the MCP response.
- `figma_file_key` in Project_Status.md is the canonical reference. Use it when the user says "the Figma file".

## Design decisions

- Design decisions go in `wiki/` as concept pages, not in conversation.
- Every accepted decision links back to the Figma frame or asset that informed it.
- `greenlit: true` in Project_Status.md means the design direction is locked — do not suggest reversals without explicit user request.

## Deliverables

- Use `mew package <project>` to assemble client packages.
- Never push assets to Drive directly — surface the Drive MCP instructions and let the user confirm.
