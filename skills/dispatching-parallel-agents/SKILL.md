---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
origin: superpowers
---

# Dispatching Parallel Agents

## Overview

Delegate independent tasks to specialized agents with isolated context. Each agent gets exactly the context it needs — nothing from your session history. This preserves your context for coordination work.

**Core principle:** One agent per independent problem domain. Let them work concurrently.

## When to Use

- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

**Don't use when:**
- Failures are related (fixing one might fix others)
- Agents would edit the same files
- You need to understand the full system state first

## The Pattern

### 1. Identify Independent Domains

Group work by what's broken or what needs to happen, ensuring true independence:
- Domain A: auth flow
- Domain B: payment processing
- Domain C: notification system

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** one file, subsystem, or problem domain
- **Clear goal:** what to accomplish
- **Constraints:** what NOT to touch
- **Expected output:** what to return in its summary

### 3. Dispatch in Parallel

```typescript
// In Claude Code, all three run concurrently
Agent({ description: "Fix auth tests", prompt: "..." })
Agent({ description: "Fix payment tests", prompt: "..." })
Agent({ description: "Fix notification tests", prompt: "..." })
```

### 4. Review and Integrate

- Read each summary
- Verify fixes don't conflict
- Run the full test suite
- Integrate all changes

## Agent Prompt Structure

Good prompts are focused, self-contained, and specific about output:

```markdown
Fix the 3 failing tests in src/agents/auth.test.ts:

1. "should refresh token on expiry" — expects new token in response
2. "should reject invalid tokens" — currently throws instead of returning 401
3. "should handle concurrent requests" — race condition

Your task:
1. Read the test file and understand what each test verifies
2. Identify root cause — timing issues or bugs?
3. Fix by [specific guidance]
4. Do NOT modify production auth.ts — fix tests only

Return: Summary of what you found and what you changed.
```

## Common Mistakes

- **Too broad:** "Fix all the tests" → agent gets lost
- **No context:** "Fix the race condition" → agent doesn't know where
- **No constraints:** agent might refactor everything
- **Vague output:** "Fix it" → you don't know what changed

## Verification

After agents return:
1. Review each summary — understand what changed
2. Check for conflicts — did agents edit the same files?
3. Run full suite — verify all fixes work together
4. Spot-check — agents can make systematic errors
