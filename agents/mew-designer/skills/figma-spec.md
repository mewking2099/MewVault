---
name: figma-spec
triggers: [figma, design spec, component spec, get the design, check figma, figma file]
description: Extract component specs from Figma via MCP and produce handoff notes
inject: on-trigger
---

# Skill: Figma Spec

When a Figma URL or file key is provided:

1. Use the Figma MCP `get_design_context` tool with the node ID or file key.
2. Never manually transcribe measurements — read them from the MCP response.
3. Extract: dimensions, spacing, colors, typography, border-radius, shadows.
4. Produce a component spec in this format:

```markdown
## Component: <name>

**Dimensions:** W × H
**Spacing:** padding: top right bottom left

### Colors
- Background: #...
- Text: #...
- Border: #...

### Typography
- Font: <family>, <size>px, weight <weight>
- Line height: <value>

### States
- Default: ...
- Hover: ...
- Disabled: ...

### Notes
- <any design intent not captured by numbers>
```

5. Write the spec to `<project>/wiki/component-<name>.md`.
6. Link it from the project's `wiki/index.md`.
