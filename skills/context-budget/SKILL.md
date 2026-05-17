---
name: context-budget
description: Audits Claude Code context window consumption — agents, skills, MCP servers, rules. Identifies bloat and produces prioritized token-savings recommendations.
origin: ECC
---

# Context Budget

Analyze token overhead across every loaded component and surface actionable optimizations.

## When to Use

- Session performance feels sluggish or output quality is degrading
- You've added many skills, agents, or MCP servers recently
- You want to know how much context headroom you actually have
- Planning to add more components and need to know if there's room

## How It Works

### Phase 1: Inventory

Estimate token consumption per component type (words × 1.3 for prose, chars ÷ 4 for code):

- **Skills** (`skills/*/SKILL.md`) — count tokens per file; flag files >400 lines
- **Rules** (`rules/**/*.md`) — count tokens per file; flag files >100 lines; detect content overlap
- **MCP Servers** — count configured servers and total tool count; estimate ~500 tokens per tool; flag servers wrapping simple CLIs (gh, git, npm, supabase, vercel)
- **CLAUDE.md chain** — count tokens; flag combined total >300 lines

### Phase 2: Classify

| Bucket | Criteria | Action |
|--------|----------|--------|
| Always needed | Referenced in CLAUDE.md, backs an active command | Keep |
| Sometimes needed | Domain-specific, not referenced in CLAUDE.md | Consider on-demand |
| Rarely needed | Overlapping content, no obvious project match | Remove or lazy-load |

### Phase 3: Detect Issues

- **Redundant skills** — skills that duplicate rule content or each other
- **MCP over-subscription** — >8 servers, or servers wrapping free CLIs
- **CLAUDE.md bloat** — verbose explanations that should be rules

### Phase 4: Report

```
Context Budget Report
═════════════════════════════════════

Total estimated overhead: ~XX,XXX tokens
Context window: 200K
Effective available: ~XXX,XXX tokens (XX%)

Component Breakdown:
  Skills:    N files    ~X,XXX tokens
  Rules:     N files    ~X,XXX tokens
  MCP tools: N tools    ~XX,XXX tokens
  CLAUDE.md: N files    ~X,XXX tokens

Top 3 optimizations:
1. [action] → save ~X,XXX tokens
2. [action] → save ~X,XXX tokens
3. [action] → save ~X,XXX tokens
```

## Quick Heuristics

- Each MCP tool costs ~500 tokens (schema overhead)
- Each SKILL.md costs ~200-800 tokens depending on length
- Rules files cost ~100-400 tokens each
- Removing 3 CLI-wrapping MCP servers can save 5,000–15,000 tokens

## MewVault-Specific Notes

- Check `mewvault/hooks/session-start.js` injection output — it should be capped at 6,000 chars
- The Figma, Google Drive, and memory MCPs are always-on — audit their tool counts periodically
- Skills in `mewvault/skills/` only cost tokens when invoked, not at session start
