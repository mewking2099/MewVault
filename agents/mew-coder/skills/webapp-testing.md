---
name: webapp-testing
triggers: [test the app, playwright test, test this page, UI test, browser test, e2e test, test this UI]
description: Test local web applications using Playwright — verify frontend functionality, debug UI behavior, capture screenshots, view browser logs. Use when testing any web app in software-projects/ or when the user wants to verify UI behaviour.
inject: on-trigger
claude_code_skills: [webapp-testing]
source: anthropics/skills
---

# Skill: Webapp Testing

Load and follow the `webapp-testing` Claude Code skill for full Playwright instructions:

```
Skill({skill: "webapp-testing"})
```

## MewVault context

- App root is in `software-projects/<project>/`
- Dev server is usually `npm run dev`, `pnpm dev`, or `python -m uvicorn app:app`
- Screenshots go to `/tmp/` unless the project specifies otherwise
- Stay within the project silo — don't read other silos during test runs
- After testing, report findings in conversation. Don't auto-commit test scripts.
