---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
origin: superpowers
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Any technical issue: test failures, bugs, unexpected behavior, performance problems, build failures, integration issues.

**Use especially when:** under time pressure, "quick fix" seems obvious, you've already tried multiple fixes.

## The Four Phases

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read error messages completely** — stack traces, line numbers, error codes
2. **Reproduce consistently** — can you trigger it reliably? If not, gather more data, don't guess
3. **Check recent changes** — git diff, recent commits, new dependencies, config changes
4. **Gather evidence in multi-component systems:**

   ```bash
   # For each component boundary: log what enters and exits
   echo "=== Layer 1 state ===" && env | grep MY_VAR
   echo "=== Layer 2 state ===" && cat config.json
   ```

   Run once to gather evidence → analyze → then investigate the failing layer.

5. **Trace data flow** — where does the bad value originate? Trace backward through the call stack to the source. Fix at source, not at symptom.

### Phase 2: Pattern Analysis

1. Find working examples of similar code in the codebase
2. Read the reference implementation completely — don't skim
3. List every difference between working and broken, however small
4. Understand all dependencies, config, and assumptions

### Phase 3: Hypothesis and Testing

1. State clearly: "I think X is the root cause because Y"
2. Make the SMALLEST possible change to test the hypothesis
3. One variable at a time — don't fix multiple things at once
4. If it doesn't work: form a NEW hypothesis, don't stack more fixes

### Phase 4: Implementation

1. Create a failing test case first (use `tdd-workflow` skill)
2. Implement the single root-cause fix
3. Verify fix — tests pass, no regressions
4. **If 3+ fixes have failed:** STOP — this signals an architectural problem. Discuss with the user before attempting more.

## Red Flags — Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- Adding multiple changes at once
- "It's probably X" without tracing
- Any fix attempt without understanding the root cause
- Three+ failed fix attempts → question the architecture

## Quick Reference

| Phase | Key Activity | Exit Criteria |
|-------|-------------|---------------|
| 1. Root Cause | Read errors, reproduce, trace | Know WHAT and WHY |
| 2. Pattern | Find working examples, compare | Differences identified |
| 3. Hypothesis | Form theory, test minimally | Confirmed or new theory |
| 4. Implementation | Create test, fix, verify | Bug resolved, tests pass |
