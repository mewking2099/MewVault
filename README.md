# MewVault

A federated AI workspace manager built for Claude Code. MewVault organises creative and technical work into independent git silos, enforces planning gates before code is written, and wires Claude Code hooks to inject context, guard secrets, and capture learned behaviour over time.

---

## Overview

MewVault separates concerns across four silos, each its own git repository:

```
workspace-root/
  wiki/               # Knowledge base, research, learning tracks
  design-studio/      # UX and design projects (Figma-integrated)
  software-projects/  # Code projects (Next.js, Astro, SvelteKit)
  game-lab/           # Godot games and experiments
  mewvault/           # This repo — CLI and hook runtime
```

The `mew` CLI is the single entry point for all workspace operations. The **MewHarness** hook runtime installs five Claude Code lifecycle hooks that enforce rules automatically — no manual reminders needed.

---

## Requirements

| | Windows | macOS |
|---|---|---|
| Python | 3.11+ — [python.org](https://python.org) or `winget install Python.Python.3.12` | 3.11+ — `brew install python` |
| Node.js | [nodejs.org](https://nodejs.org) or `winget install OpenJS.NodeJS.LTS` | `brew install node` |
| Git | [git-scm.com](https://git-scm.com) or `winget install Git.Git` | `brew install git` or Xcode CLI tools |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | `npm install -g @anthropic-ai/claude-code` |

---

## Installation

### Windows (PowerShell)

```powershell
# 1. Clone into your workspace root
cd C:\Users\<you>\workspace
git clone <this-repo> mewvault

# 2. Install the CLI
cd mewvault
pip install -e .

# 3. Register hooks and rule templates
mew harness install

# 4. Set the workspace root env var — add to your PowerShell profile
#    Open profile: notepad $PROFILE
$env:MEWVAULT_ROOT = 'C:\Users\<you>\workspace\mewvault'

# To persist across sessions, add this line to $PROFILE:
# $env:MEWVAULT_ROOT = 'C:\Users\<you>\workspace\mewvault'
```

**Verify install:**

```powershell
mew status
mew harness status
node --version   # must be present for hooks
```

### macOS (Terminal)

```bash
# 1. Clone into your workspace root
cd ~/workspace
git clone <this-repo> mewvault

# 2. Install the CLI
cd mewvault
pip3 install -e .

# 3. Register hooks and rule templates
mew harness install

# 4. Set the workspace root env var — add to ~/.zshrc or ~/.bash_profile
export MEWVAULT_ROOT="$HOME/workspace/mewvault"
source ~/.zshrc
```

**Verify install:**

```bash
mew status
mew harness status
node --version   # must be present for hooks
```

### After install (both platforms)

Restart Claude Code to activate the hooks. Open your workspace root in Claude Code — MewHarness will inject vault rules automatically on the first prompt.

---

## Upgrading

### Windows

```powershell
cd C:\Users\<you>\workspace\mewvault
git pull
pip install -e .
mew harness install   # re-registers hooks if new ones were added
```

### macOS

```bash
cd ~/workspace/mewvault
git pull
pip3 install -e .
mew harness install
```

---

## CLI Reference

### Workspace

| Command | Description |
|---|---|
| `mew status` | Vault overview across all silos |
| `mew status --domain wiki` | Filter to one silo |
| `mew status --project <name>` | Deep view of a single project |
| `mew status --stale 14` | Projects untouched for 14+ days |
| `mew status --blocked` | Projects with unresolved blocking threads |
| `mew validate` | Check all Project_Status.md files against schema |
| `mew validate --fix` | Offer to repair fixable issues |

### Projects

| Command | Description |
|---|---|
| `mew new ux-project <name>` | Scaffold a new design project |
| `mew new code-project <name> --stack next` | Scaffold a code project (next/astro/sveltekit) |
| `mew new game-project <name>` | Scaffold a full game project |
| `mew new game-experiment <name>` | Low-commitment prototype (no tier gate) |
| `mew new learning-path <name>` | Create a learning track in wiki/ |
| `mew rename <old> <new>` | Rename a project folder |
| `mew archive <name>` | Move a project to `_archive/` |
| `mew abandon <name>` | Mark a project abandoned with a reason |
| `mew rebuild-status <name>` | Regenerate a missing Project_Status.md |

### Promotions

| Command | Description |
|---|---|
| `mew promote <ux-name> --to <code-name>` | Promote a UX project to a code project |
| `mew promote game-lab/_experiments/<name>` | Promote an experiment to a full game project |
| `mew promote wiki/ --topic <tag>` | Surface wiki research into a UX project |

### Git

| Command | Description |
|---|---|
| `mew sync` | Show git status across all silo repos |
| `mew sync --commit "message"` | Interactively commit each repo with changes |
| `mew sync --commit "message" --push` | Commit and push |

### Secrets

Secrets are stored outside git. Never commit them.

| Command | Description |
|---|---|
| `mew secret set KEY_NAME` | Store a new secret |
| `mew secret get KEY_NAME` | Inject a secret as an env variable |
| `mew secret list` | List stored key names (not values) |
| `mew secret rotate KEY_NAME` | Rotate a stored secret |

### Context & Compaction

| Command | Description |
|---|---|
| `mew dump <project>` | Token-budgeted context snapshot for a project |
| `mew dump <project> --budget 8000` | Custom character budget |
| `mew compact` | Generate a semantic context map for the workspace |
| `mew compact --project <name>` | Scope to a single project |

### Inbox & Packages

| Command | Description |
|---|---|
| `mew process-inbox` | List `wiki/_inbox/` and propose routing |
| `mew package <ux-project>` | Assemble a client deliverable package |
| `mew package <ux-project> --push-drive` | Print Drive MCP push instructions |

### Instincts

The instinct pipeline captures learned behaviours from correction signals detected by hooks.

| Command | Description |
|---|---|
| `mew instinct status` | Show pending and promoted instincts |
| `mew instinct promote <id>` | Promote a pending instinct to active |
| `mew instinct prune` | Remove stale pending instincts |
| `mew instinct export --out file.json` | Export promoted instincts |
| `mew instinct import file.json` | Import instincts from JSON |

### Harness

| Command | Description |
|---|---|
| `mew harness install` | Register hooks and install rule templates |
| `mew harness status` | Show hook registration and instinct counts |
| `mew harness config` | Show harness env var configuration |
| `mew harness disable` | Remove all MewHarness hooks from settings.json |
| `mew harness proxy` | Print LiteLLM proxy start instructions |

**Harness env vars:**

| Variable | Default | Description |
|---|---|---|
| `MEWVAULT_ROOT` | *(required)* | Absolute path to the `mewvault/` directory |
| `MEW_SESSION_START_MAX_TOKENS` | `6000` | Character budget for context injected at session start |

Set persistently:

```powershell
# Windows — add to $PROFILE
$env:MEWVAULT_ROOT = 'C:\Users\<you>\workspace\mewvault'
$env:MEW_SESSION_START_MAX_TOKENS = '6000'
```

```bash
# macOS — add to ~/.zshrc or ~/.bash_profile
export MEWVAULT_ROOT="$HOME/workspace/mewvault"
export MEW_SESSION_START_MAX_TOKENS=6000
```

**LiteLLM proxy** (`mew harness proxy` prints the correct command):

```powershell
# Windows — run the printed PowerShell script
& 'C:\Users\<you>\workspace\mewvault\proxy\start-proxy.ps1'
```

```bash
# macOS — run the printed shell script
bash ~/workspace/mewvault/proxy/start-proxy.sh
```

---

## MewHarness Hooks

Five Claude Code lifecycle hooks run automatically:

| Event | Script | What it does |
|---|---|---|
| `UserPromptSubmit` | `session-start.js` | Injects vault rules, project status, and instincts at the start of every prompt |
| `Stop` | `session-end.js` | Writes an auto-wrap log entry and suggested commit message |
| `PreToolUse` | `pre-tool-use.js` | Enforces MewKing gate, blocks secrets in writes, guards `raw/` paths, fires TDD warning |
| `PostToolUse` | `post-tool-use.js` | Accumulates session activity, detects correction signals for the instinct pipeline |
| `PreCompact` | `pre-compact.js` | Runs semantic compact, writes context snapshots, preserves latest snapshot post-compaction |

---

## Tier Gates

Every project has a `tier` field in its `Project_Status.md`. The tier controls how much autonomy Claude has before writing code.

### Pounce — small tasks (< 2 hours)
No plan required. Claude writes directly.

### Stalk — multi-session features
Claude proposes an approach in chat. User approves verbally. Claude writes after approval.

### MewKing — architecture or risky changes
Hard gate. Claude may **not** write any code until `plan_approved: true` in `Project_Status.md`.

1. Claude creates `proposals/active/<feature>/plan.md` and presents it.
2. User reviews and sets `plan_approved: true`.
3. Claude proceeds.

The `pre-tool-use.js` hook enforces this at the OS level (exit code 2). After two blocked attempts, `proposals/active/<feature>/REVIEW_REQUIRED.md` is written automatically.

---

## Slash Commands

Four commands are understood by Claude inside a MewVault session:

| Command | Description |
|---|---|
| `/start [silo] [project]` | Open vault overview, optionally drill into a silo or project |
| `/wrap` | End the session, update log.md, return to vault overview |
| `/plan <feature>` | Propose a tier and begin the planning flow |
| `/teach [topic]` | Enter pedagogical mode for a learning track |

---

## Project Layout

Each project follows a standard structure:

```
<silo>/<project>/
  Project_Status.md     # tier, current_phase, stack, open_threads, plan_approved
  proposals/active/     # MewKing plans
  src/                  # Source code
  tests/                # Tests
  raw/                  # Specs, PRDs — immutable, never edited
  wiki/                 # Architecture decisions
  log.md                # Session log
```

`raw/` directories are read-only. The `pre-tool-use.js` hook blocks any write attempt to a `raw/` path.

---

## File System Rules

- Never edit files outside the current project root without explicit instruction.
- `raw/` anywhere in the workspace is immutable.
- `.obsidian/` is off-limits — Obsidian manages its own config.
- Secrets live only in `mewvault/secrets/` and are gitignored.
- Cross-silo promotes require an explicit `mew` command confirmed by the user.
- `wiki/_inbox/` is never auto-processed — wait for user trigger.

---

## Session Discipline

- Every session ends with `/wrap`. `log.md` is updated before closing.
- Every new wiki note needs at least one inbound link before the session ends.
- Every factual claim cites its source: `(source: raw/file.ext)`.
- Commits are never auto-created. Use `mew sync --commit` when ready.
