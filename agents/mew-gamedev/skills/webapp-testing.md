---
name: webapp-testing
triggers: [test the game, browser test, test this web game, playwright test, test the UI, verify the game works]
description: Test web-based game builds using Playwright — verify game UI, browser rendering, and interactive behaviour. Use for game-lab projects with a web frontend or browser-based prototype.
inject: on-trigger
claude_code_skills: [webapp-testing]
source: anthropics/skills
---

# Skill: Webapp Testing (Game Lab)

Load and follow the `webapp-testing` Claude Code skill for full Playwright instructions:

```
Skill({skill: "webapp-testing"})
```

## MewVault context

- Game projects are in `game-lab/<project>/`
- Web game exports are typically in `game-lab/<project>/export/web/`
- Experiments in `game-lab/_experiments/<name>/` — no MewKing gate required
- Screenshots go to `/tmp/` — include them in the session wrap for visual record
