---
name: web-artifacts-builder
triggers: [react artifact, web artifact, shadcn artifact, complex dashboard, multi-component UI, build a dashboard, interactive component]
description: Build elaborate multi-component React artifacts using React 18 + Tailwind + shadcn/ui. Use for complex UIs requiring state management, routing, or shadcn components — not for simple single-file HTML.
inject: on-trigger
claude_code_skills: [web-artifacts-builder]
source: anthropics/skills
---

# Skill: Web Artifacts Builder

Load and follow the `web-artifacts-builder` Claude Code skill for full React artifact guidance:

```
Skill({skill: "web-artifacts-builder"})
```

## MewVault context

- Artifacts are self-contained — don't reference project-local files from artifacts
- For design-studio work, align with Figma specs via the figma-spec skill first
- For idea-hub pitch demos, keep artifacts simple enough to be shared as standalone HTML
