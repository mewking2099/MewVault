---
name: frontend-design
triggers: [design this UI, make this look good, frontend design, style this, UI design, build this component, make it beautiful]
description: Create distinctive, production-grade frontend interfaces with high design quality. Use when building web components, pages, or apps that need polished styling — even if the user doesn't say "design" explicitly.
inject: on-trigger
claude_code_skills: [frontend-design]
source: anthropics/skills
---

# Skill: Frontend Design

Load and follow the `frontend-design` Claude Code skill for full design + implementation guidance:

```
Skill({skill: "frontend-design"})
```

## MewVault context

- Software projects live in `software-projects/<project>/src/`
- Default stacks: Next.js + Tailwind, SvelteKit + Tailwind, or Astro + Tailwind
- Follow the project's established stack — check `Project_Status.md` for stack field
- Design tokens and component conventions go in `software-projects/<project>/wiki/`
- For Yaana Design System work, check the Figma file key in Project_Status.md first
