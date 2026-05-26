---
name: github-issue-fix
triggers: [fix this github issue, triage issue, work on this issue, github issue, issue number, resolve issue, close issue]
description: 6-step pipeline to triage, fix, review, and PR a GitHub issue
inject: on-trigger
claude_code_skills: []
source: mewvault/custom
---

# GitHub Issue Fix Skill

6-step pipeline: **Triage → Plan → Fix → Review → PR → Comment**

Uses `gh` CLI for all GitHub operations. Requires `gh auth login` before first use.

## Prerequisites

```bash
gh auth status          # must show logged-in account
gh repo view            # confirm you're in the right repo
```

## Step 1 — Triage

Read the issue and classify it:

```bash
gh issue view <issue-number>
# or with repo: gh issue view <n> --repo owner/repo
```

Produce a triage report:
```
Issue #<n>: <title>
Type:     bug | feature | docs | question | chore
Severity: critical | high | medium | low
Labels:   <existing labels>
Affected: <likely files/modules based on description>
Effort:   S | M | L
```

If the issue is ambiguous — ask one clarifying question before proceeding.

## Step 2 — Plan

Based on triage, list:
- Exact files that need to change
- What each change does
- Any new files needed
- Tests to write or update

State the plan clearly before touching code. For `L` effort issues: pause here and confirm with user before continuing.

## Step 3 — Create branch + Fix

```bash
# Create a branch linked to the issue
gh issue develop <n> --name "fix/issue-<n>-<short-slug>" --checkout
# Falls back if not supported:
git checkout -b "fix/issue-<n>-<short-slug>"
```

Implement the fix. If new code is being written — follow the `tdd-workflow` skill:
1. Write the failing test first
2. Implement to make it pass
3. Verify no regressions: `npm test` / `pytest` / relevant test runner

## Step 4 — Code Review

Self-review changed files before creating the PR. Check:
- No unintended side effects
- Error paths handled
- No secrets or debug code left in
- Tests cover the fix

For any file in `software-projects/<project>/src/` or `lib/` — invoke `code-review` skill explicitly.

## Step 5 — Create PR

```bash
gh pr create \
  --title "fix: <brief description> (closes #<n>)" \
  --body "$(cat <<'EOF'
## Summary

Closes #<issue-number>.

<1-2 sentence description of what changed and why>

## Changes

- `<file>` — <what changed>
- `<file>` — <what changed>

## Test plan

- [ ] <what to verify manually>
- [ ] Existing tests pass

🤖 Generated with MewVault / mew-coder
EOF
)"
```

Add reviewers if team is set up: `--reviewer <handle>`

## Step 6 — Comment on issue

After PR is created, post a brief status update on the issue:

```bash
gh issue comment <n> --body "PR submitted: <pr-url>

Changes: <one-line summary>
Ready for review."
```

## Outcome checklist

- [ ] Issue triaged and classified
- [ ] Branch created from issue number
- [ ] Fix implemented with tests
- [ ] Code review passed
- [ ] PR created with structured description linking `closes #<n>`
- [ ] Comment posted on original issue

## MewVault context

- Only work in `software-projects/<project>/` — check `Project_Status.md` before starting
- MewKing tier requires `plan_approved: true` — for complex fixes, write a plan first
- Check `open_threads` in Project_Status.md — do not start if a blocking thread is unresolved
- After PR is merged, wrap the session: `log.md` entry + update `current_phase` if this closes a phase
- Never auto-push to `main` — always use a branch + PR

## Error handling

**Issue not found**: verify repo with `gh repo view`, check you have access
**`gh issue develop` not supported**: fall back to `git checkout -b fix/issue-<n>-<slug>`
**Tests failing**: fix the tests before creating the PR — never PR with failing tests
**Conflicts**: rebase against main before creating the PR: `git rebase origin/main`
