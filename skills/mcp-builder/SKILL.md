---
name: mcp-builder
description: Guide for creating MCP (Model Context Protocol) servers to connect LLMs with external services. Use when building an MCP server to integrate an API or service, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
origin: anthropics
---

# MCP Server Development Guide

Build MCP servers that let Claude interact with external services through well-designed tools.

## Four-Phase Process

### Phase 1: Research and Plan

**Understand the API:**
- Read the full API docs — not just endpoints, but rate limits, auth, pagination
- Identify the 5–10 operations users will want most (not all endpoints)
- Design tool names with consistent prefixes: `github_create_issue`, `github_list_repos`

**Tool design principles:**
- Return focused, relevant data — not entire API response blobs
- Provide actionable error messages: "Rate limit exceeded. Retry after 60s" not "429"
- Support pagination for list operations (`limit`, `cursor` params)
- One tool = one clear action; avoid multi-purpose tools

### Phase 2: Implement

**Python (FastMCP — recommended for simplicity):**
```python
from fastmcp import FastMCP

mcp = FastMCP("my-service")

@mcp.tool()
def list_items(limit: int = 20, cursor: str | None = None) -> dict:
    """List items from My Service. Returns items and next_cursor."""
    response = api_client.get("/items", params={"limit": limit, "cursor": cursor})
    return {"items": response["data"], "next_cursor": response.get("cursor")}

if __name__ == "__main__":
    mcp.run()
```

**TypeScript (MCP SDK):**
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "my-service", version: "1.0.0" });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "list_items",
    description: "List items from My Service",
    inputSchema: { type: "object", properties: { limit: { type: "number" } } }
  }]
}));
```

### Phase 3: Configure

Add to `.claude/mcp.json`:
```json
{
  "mcpServers": {
    "my-service": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": { "API_KEY": "${MY_SERVICE_API_KEY}" }
    }
  }
}
```

Or for Node:
```json
{
  "command": "node",
  "args": ["/path/to/server/index.js"]
}
```

### Phase 4: Test

```bash
# Test tool listing
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python server.py

# Test a specific tool
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_items","arguments":{}},"id":2}' | python server.py
```

## Common Mistakes

- **Too many tools:** Start with 5–10 core operations, not a full API mirror
- **No pagination:** Every list operation needs limit + cursor
- **Generic errors:** "Error: 404" → "Resource not found: check that the item ID exists"
- **Secrets in config:** Always use env vars, never hardcode API keys
- **Blocking I/O in TypeScript:** Use `async/await` throughout

## MewVault Note

After building, add the server to `mewvault/.claude/settings.json` under `mcpServers`. Run `mew harness install` to sync settings.
