---
name: mcp-builder
triggers: [build an MCP, create MCP server, MCP server, new MCP tool, add MCP, MCP integration]
description: Guide for creating high-quality MCP (Model Context Protocol) servers that connect external services to Claude. Use when building or extending any MCP server in mewvault/ or software-projects/.
inject: on-trigger
claude_code_skills: [mcp-builder]
source: anthropics/skills
---

# Skill: MCP Builder

Load and follow the `mcp-builder` Claude Code skill for full MCP implementation guide:

```
Skill({skill: "mcp-builder"})
```

## MewVault context

- MCP configs live in `.claude/settings.json` (mcpServers block) and `.mcp.json`
- Review `.mcp.json` before writing — instinct: verify before first commit
- New MCP servers for the vault go in `mewvault/mcp-configs/`
- Secrets (API keys for MCP tools) use `mew secret set KEY_NAME` — never hardcode
- After building, test the MCP server locally before adding it to settings
