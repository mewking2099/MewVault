---
name: claude-api
triggers: [claude API, anthropic SDK, claude integration, add claude, build with claude, claude feature, prompt caching]
description: Build, debug, and optimize Claude API / Anthropic SDK apps. Use when code imports anthropic or @anthropic-ai/sdk, or when adding/tuning any Claude feature (caching, tool use, streaming, batch). Skip for OpenAI or other providers.
inject: on-trigger
claude_code_skills: [claude-api]
source: anthropics/skills
---

# Skill: Claude API

Load and follow the `claude-api` Claude Code skill for full Anthropic SDK guidance:

```
Skill({skill: "claude-api"})
```

## MewVault context

- API keys are stored in `mewvault/secrets/` — retrieve via `mew secret get ANTHROPIC_API_KEY`
- Never hardcode keys or echo them in responses
- All Claude API apps built here should include prompt caching
- Prefer Sonnet for implementation tasks, Opus for architecture/reasoning calls
