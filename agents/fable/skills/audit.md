---
name: audit
description: Full codebase audit — reads the entire project, produces a structured report covering architecture, P0/P1/P2 issues, security surface, deps, observability, and test coverage. Output saved to wiki/audit-<date>.md.
type: workflow
triggers:
  - audit
  - code audit
  - codebase audit
  - audit the codebase
  - analyse the codebase
  - analyze the codebase
  - technical debt
  - architecture review
  - architecture audit
  - what's wrong with this codebase
  - deep dive
  - full review
  - production audit
  - audit report
inject: on-trigger
chains_to:
  - scale-plan
---

# $fable audit

## What this skill does

Produces a complete, structured audit of a software project. The output is a persistent `wiki/audit-<date>.md` that acts as the source of truth for all subsequent scale planning.

## When to invoke

- Before starting any MVP-to-production work
- After a major architecture change to baseline the new state
- When a project is inherited and nothing is documented

## Steps

### 1. Orient
- Read `Project_Status.md`, `CLAUDE.md`, and any `wiki/` docs that exist
- Note: stack, language, framework, deployment target, current phase

### 2. Read the codebase (full pass)
Work through each concern area in order. Do not skip any section even if it looks clean.

| Concern | What to read |
|---|---|
| Entry points | main file, server start, CLI entry |
| Data layer | DB schema, ORM models, migrations, query patterns |
| API surface | routes, controllers, middleware stack |
| Auth | session, JWT, OAuth, RBAC — any auth code |
| Business logic | core domain modules |
| Background jobs | queues, crons, workers |
| Config & secrets | how env vars are loaded, any hardcoded values |
| Dependencies | package.json / requirements.txt / go.mod — versions, last update |
| Tests | test files, coverage config, CI test step |
| Build & deploy | Dockerfile, CI/CD config, deploy scripts |
| Observability | logging calls, metrics, error tracking setup |

### 3. Classify findings

Every finding gets:
- **Priority**: P0 (blocks production) / P1 (first sprint) / P2 (within 3 months)
- **Location**: file path and line number if applicable
- **Impact**: what breaks or degrades if this isn't fixed
- **Fix approach**: 1–3 sentences on the right solution
- **Effort**: S (<2h) / M (half-day) / L (1–2 days) / XL (>2 days)

### 4. Write the report

Save to `wiki/audit-YYYY-MM-DD.md` using the audit report structure from the fable system prompt.

### 5. Post-audit

- Update `Project_Status.md`: set `last_audit` to today's date
- Tell the user: total P0/P1/P2 counts, overall verdict (Green/Amber/Red), recommended next command (`$fable scale-plan`)

## Triage mode (`$fable triage`)

When a full audit isn't needed: scan only for P0s. Time-box to 15 minutes of reading. Output a short `wiki/triage-<date>.md` with P0s only and a one-line verdict.
