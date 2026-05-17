---
name: github-ops
description: GitHub repository operations — issue triage, PR management, CI/CD debugging, release management, and security monitoring using the gh CLI. Use when the user wants to manage GitHub issues, PRs, CI status, or releases without switching context.
origin: ECC
---

# GitHub Operations

Manage GitHub repositories using the `gh` CLI. Focus: community health, CI reliability, contributor experience.

## When to Activate

- Triaging issues (classifying, labeling, responding, deduplicating)
- Managing PRs (review status, CI checks, stale PRs, merge readiness)
- Debugging CI/CD failures
- Preparing releases and changelogs
- Monitoring Dependabot and security alerts
- User says "check GitHub", "triage issues", "review PRs", "release", "CI is broken"

**Requires:** `gh auth login` completed.

## Issue Triage

Classify by type (bug, feature-request, question, documentation, duplicate, invalid, good-first-issue) and priority (critical, high, medium, low).

```bash
# Search for duplicates
gh issue list --search "keyword" --state all --limit 20

# Add labels
gh issue edit <number> --add-label "bug,high-priority"

# Comment
gh issue comment <number> --body "Thanks for reporting. Could you share reproduction steps?"
```

## PR Management

```bash
# Check CI status
gh pr checks <number>

# Check mergeability
gh pr view <number> --json mergeable

# Find stale PRs (no activity in 7+ days)
gh pr list --json number,title,updatedAt --jq '.[] | select(.updatedAt < "2026-05-10")'
```

Stale policy:
- Issues with no activity in 14+ days: add `stale` label, comment asking for update
- PRs with no activity in 7+ days: comment asking if still active

## CI/CD Debugging

```bash
# List recent failures
gh run list --status failure --limit 10

# View failed logs
gh run view <run-id> --log-failed

# Re-run failed jobs only
gh run rerun <run-id> --failed
```

Distinguish flaky tests from real failures. For real failures: identify root cause before re-running.

## Release Management

```bash
# List merged PRs since last release
gh pr list --state merged --base main --search "merged:>2026-05-01"

# Create release with auto-generated notes
gh release create v1.2.0 --title "v1.2.0" --generate-notes
```

## Security Monitoring

```bash
# Check Dependabot alerts
gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[].security_advisory.summary'

# Check secret scanning
gh api repos/{owner}/{repo}/secret-scanning/alerts --jq '.[].state'
```

Flag critical/high severity alerts immediately.

## Quality Gate

Before completing any GitHub operations task: all triaged issues have labels, no PRs >7 days without comment, CI failures have been investigated (not just re-run), releases have accurate changelogs.
