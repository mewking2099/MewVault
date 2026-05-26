---
name: frontend-design
triggers: [game UI design, design the game UI, UI for the game, game menu design, game HUD design]
description: Create production-grade UI for game menus, HUDs, and overlays. Use when designing any visual interface for a game project in game-lab/.
inject: on-trigger
claude_code_skills: [frontend-design]
source: anthropics/skills
---

# Skill: Frontend Design (Game Lab)

Load and follow the `frontend-design` Claude Code skill for full design + implementation guidance:

```
Skill({skill: "frontend-design"})
```

## MewVault context

- Game UI assets go in `game-lab/<project>/assets/`
- For Godot projects, UI designs inform GDScript CanvasLayer/Control node layouts
- Keep designs exportable as PNG/SVG for import into Godot
- Game feel > pixel perfection — prefer responsive, readable over elaborate
