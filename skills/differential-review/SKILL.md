---
name: differential-review
description: Security-focused review of code changes — PRs, commits, or diffs. Calculates blast radius, checks test coverage, and flags regressions. Use when reviewing a PR or commit for security impact, not for general code quality (use code-reviewer for that).
origin: trailofbits
---

# Differential Security Review

Security-focused code review for PRs, commits, and diffs.

**Differs from `code-reviewer`:** This skill focuses specifically on security regressions, blast radius, and attack scenarios. Use `code-reviewer` for general code quality; use this when security matters.

## Core Principles

1. **Risk-First:** Focus on auth, crypto, value transfer, external calls
2. **Evidence-Based:** Every finding backed by line numbers and attack scenario
3. **Adaptive:** Scale depth to codebase size (SMALL / MEDIUM / LARGE)
4. **Always produce a report:** Never summarize verbally only

## Codebase Size Strategy

| Size | Files changed | Strategy |
|------|--------------|----------|
| SMALL | <20 | Read all deps, full git blame |
| MEDIUM | 20–200 | 1-hop deps, priority files |
| LARGE | 200+ | Critical paths only |

## Risk Triggers

| Level | Triggers |
|-------|---------|
| HIGH | Auth, crypto, external calls, value transfer, validation removal |
| MEDIUM | Business logic, state changes, new public APIs |
| LOW | Comments, tests, UI, logging |

## Workflow

### Phase 0: Triage
```bash
git diff --stat HEAD~1  # or PR base
git log --oneline -10
```
- Count changed files → determine size strategy
- Classify each file by risk level

### Phase 1: Code Analysis
For each HIGH/MEDIUM file:
- Read the full diff
- Check git blame for prior state: `git blame -L <range> <file>`
- Identify: input validation changes, permission checks removed, new external calls

### Phase 2: Blast Radius
```bash
# Find callers of changed functions
rg "functionName" --type ts -l
```
- How many files call the changed function?
- Are any callers user-facing?

### Phase 3: Test Coverage
- Do new code paths have tests?
- Were security-relevant tests removed?
- No tests on HIGH risk change = elevated severity rating

### Phase 4: Report

Generate a markdown report:

```markdown
## Security Differential Review — <PR/commit>

**Risk level:** HIGH / MEDIUM / LOW
**Coverage:** DEEP / FOCUSED / SURGICAL

### Findings

| Severity | File | Line | Issue | Attack scenario |
|----------|------|------|-------|----------------|
| HIGH | auth.ts | 42 | JWT validation removed | ... |

### Regressions
- [list any security controls weakened]

### Missing test coverage
- [list untested risk areas]

### Verdict
APPROVE / REQUEST CHANGES / NEEDS DISCUSSION
```

## Rationalizations to Reject

| Excuse | Reality |
|--------|---------|
| "Small PR, quick review" | Heartbleed was 2 lines |
| "Just a refactor" | Refactors break invariants |
| "No tests = not my problem" | Flag and elevate severity |
