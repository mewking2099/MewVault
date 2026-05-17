---
name: ci-cd-pipeline-builder
description: Detect the project stack and generate a CI/CD pipeline configuration. Use when setting up GitHub Actions, generating a pipeline for a new project, or debugging CI failures.
origin: community
---

# CI/CD Pipeline Builder

Auto-detect the project stack and generate a production-ready CI/CD pipeline.

## When to Use

- Setting up CI/CD for a new project
- Migrating from one CI provider to another
- Debugging a failing pipeline
- Adding deployment steps to an existing pipeline

## Step 1: Detect Stack

```bash
# Package manager
ls package.json pnpm-lock.yaml yarn.lock bun.lockb 2>/dev/null
# Framework
grep -i "next\|vite\|astro\|svelte\|nuxt" package.json 2>/dev/null | head -5
# Language
ls *.py pyproject.toml requirements.txt go.mod Cargo.toml 2>/dev/null
# Test runner
grep -i "vitest\|jest\|pytest\|cargo test\|go test" package.json 2>/dev/null
# Deployment target
ls vercel.json .vercel netlify.toml railway.json fly.toml Dockerfile 2>/dev/null
```

## Step 2: Present pipeline plan

Before generating:
```
Detected stack:
- Runtime: Node.js 20 / pnpm
- Framework: Next.js
- Tests: Vitest
- Deploy target: Vercel

Pipeline plan:
- Trigger: push to main, PRs
- Jobs: lint → typecheck → test → build → deploy
- Cache: pnpm store, Next.js build cache

Generate? [y/n]
```

## Step 3: Generate

### GitHub Actions — Next.js + pnpm + Vercel

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm test --run
      - run: pnpm build

  deploy:
    needs: ci
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: --prod
```

### GitHub Actions — Python + pytest

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}" }
      - run: pip install -e ".[dev]"
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v4
```

## Step 4: Secrets setup

List all required secrets for the generated pipeline:
```
Required GitHub secrets:
- VERCEL_TOKEN
- VERCEL_ORG_ID
- VERCEL_PROJECT_ID

Set via: gh secret set VERCEL_TOKEN
```

## Debugging CI Failures

```bash
# View recent run logs
gh run list --status failure --limit 5
gh run view <run-id> --log-failed

# Re-run failed jobs only
gh run rerun <run-id> --failed
```

Distinguish flaky tests (re-run to confirm) from real failures (investigate before re-running).
