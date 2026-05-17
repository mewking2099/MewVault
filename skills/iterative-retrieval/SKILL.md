---
name: iterative-retrieval
description: Use when spawning subagents that need codebase context they cannot predict upfront — progressive context retrieval pattern that solves the subagent context problem
origin: ECC
---

# Iterative Retrieval

Solves the "context problem" in multi-agent workflows: subagents don't know what context they need until they start working.

## The Problem

Standard approaches fail:
- **Send everything:** Exceeds context limits
- **Send nothing:** Agent lacks critical information
- **Guess what's needed:** Often wrong (especially when codebase uses unexpected naming)

## The Solution: 4-Phase Loop (max 3 cycles)

```
DISPATCH → EVALUATE → REFINE → (repeat or RETURN)
```

### Phase 1: DISPATCH — broad initial query

Start with high-level intent across wide file patterns:

```
patterns: ['src/**/*.ts', 'lib/**/*.ts']
keywords: ['authentication', 'user', 'session']
excludes: ['*.test.ts', '*.spec.ts']
```

Use Grep/Bash to collect candidate files.

### Phase 2: EVALUATE — score relevance

For each retrieved file, assess:
- Relevance score (0.0–1.0)
- Why it's relevant (or not)
- What context is still missing

Keep files with relevance ≥ 0.7. Note gaps explicitly.

### Phase 3: REFINE — improve based on gaps

- Add terminology from files you found (codebase may use "throttle" instead of "rate-limit")
- Exclude confidently irrelevant files
- Narrow patterns to promising directories

### Return: stop at "good enough"

Stop when you have 3–5 high-relevance files or after 3 cycles, whichever comes first. 3 high-relevance files beats 10 mediocre ones.

## Example

```
Task: "Fix the authentication token expiry bug"

Cycle 1:
  Search: "token", "auth", "expiry" in src/**
  Found: auth.ts (0.9), tokens.ts (0.8), user.ts (0.3)
  Gap: need "refresh" behavior

Cycle 2:
  Search: "refresh", "jwt" in src/**
  Found: session-manager.ts (0.95), jwt-utils.ts (0.85)
  Sufficient — stop

Result context: auth.ts, tokens.ts, session-manager.ts, jwt-utils.ts
```

## Integration

Use this pattern when writing subagent prompts:

```markdown
When retrieving context for this task:
1. Start with broad keyword search across src/
2. Score each file's relevance (0–1)
3. Identify what context is still missing
4. Refine search terms (pick up codebase terminology) and repeat
5. Stop at 3 high-relevance files or 3 cycles
6. Include only files with relevance ≥ 0.7 in your context
```

## Best Practices

- **Start broad, narrow progressively** — don't over-specify initial queries
- **Learn codebase terminology** — first cycle often reveals naming conventions
- **Track what's missing** — explicit gap identification drives refinement
- **Exclude confidently** — low-relevance files won't become relevant on re-query
