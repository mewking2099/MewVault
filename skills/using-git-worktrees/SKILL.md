---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace, or before executing implementation plans
origin: superpowers
---

# Using Git Worktrees

Ensure work happens in an isolated workspace. Prefer native worktree tools (Claude Code's `EnterWorktree`). Fall back to `git worktree` only when no native tool is available.

## Step 0: Detect Existing Isolation

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

Also check for submodules (GIT_DIR != GIT_COMMON is also true in submodules):
```bash
git rev-parse --show-superproject-working-tree 2>/dev/null
```

- **GIT_DIR != GIT_COMMON (and not a submodule):** Already in a linked worktree → skip to Step 3
- **GIT_DIR == GIT_COMMON:** Normal repo → continue to Step 1

## Step 1: Create Isolated Workspace

### 1a. Native Tool (preferred)
Use `EnterWorktree` if available. Native tools handle placement, branches, and cleanup automatically. Only proceed to 1b if no native tool exists.

### 1b. Git Worktree Fallback

**Directory priority:**
1. User's declared preference
2. Existing `.worktrees/` at project root
3. Existing `worktrees/` at project root
4. Default to `.worktrees/`

**Before creating (project-local directories):**
```bash
git check-ignore -q .worktrees 2>/dev/null || echo "MUST add to .gitignore first"
```

```bash
BRANCH_NAME="feature/my-work"
git worktree add .worktrees/$BRANCH_NAME -b $BRANCH_NAME
cd .worktrees/$BRANCH_NAME
```

## Step 3: Project Setup

Auto-detect and run:
```bash
[ -f package.json ] && npm install
[ -f Cargo.toml ] && cargo build
[ -f requirements.txt ] && pip install -r requirements.txt
[ -f go.mod ] && go mod download
```

## Step 4: Verify Clean Baseline

Run project tests. If tests fail, report and ask before proceeding.

## Red Flags

- Never create a worktree when Step 0 detects existing isolation
- Never use `git worktree add` when `EnterWorktree` is available
- Never skip `.gitignore` verification for project-local directories
- Never proceed with a failing baseline without explicit user consent
