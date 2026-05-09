# MewVault v2.0 — MewKing Plan: `v2-mewharness`

**Tier**: MewKing  
**Created**: 2026-05-09  
**Status**: APPROVED  
**Supersedes**: v1.0 slash command layer (templates/commands/)  
**Source**: `raw/mewvault-v2-implementation-plan-FINAL.md` + ECC repo (`affaan-m/everything-claude-code`)

---

## Success Criteria

When this plan is complete:

1. `mew init` in a fresh workspace → installs hooks, agents, rules. No `.claude/commands/` generated.
2. `mew harness status` → shows all 5 hooks active, last fire times, MCP load per silo.
3. Opening Claude Code in the workspace → SessionStart fires → orientation brief appears in stdout.
4. Making a GDScript mistake → PostToolUse captures correction to `instincts/pending/` with `confidence=0.6`.
5. Writing code on a MewKing project without plan.md approval → PreToolUse exits code 2, hard blocks.
6. Closing Claude Code → SessionEnd fires → `log.md` entry written with auto-wrap marker.
7. `mew compact --semantic` → produces tiered map (ACTIVE THREADS / PROJECT STATES / INSTINCTS / ORPHANS).
8. `mew agent invoke mew-planner "plan auth flow"` → spawns Opus 4.6 agent, logs invocation.
9. `mew harness proxy start` → LiteLLM running on localhost:4000, MiMo reachable.
10. Old v1.0 slash command files in `.claude/commands/` → `mew init` warns and offers to delete.

---

## What Changes vs v1.0

| v1.0 | v2.0 | Impact |
|---|---|---|
| `templates/commands/*.md` | Deleted | `mew init` no longer generates `.claude/commands/` |
| Single Claude session | 7 specialist agents | `mew agent` command family |
| No hooks | 5-hook MewHarness runtime | `mew harness` command family + `hooks/` Node.js scripts |
| One model (Sonnet) | LiteLLM proxy → 4 models | `mew harness proxy` + `proxy/litellm-config.yaml` |
| Manual `concepts-learned.md` | Instinct pipeline | `mew instinct` command family + `instincts/` dirs |
| `mew dump` | `mew compact --semantic` | New flag on validate + new compact command |
| No workspace rules | `.claude/rules/` + `.cursor/rules/` | Rule directories installed by `mew init` |

**What stays unchanged**: All 15 existing commands, Python/argparse/pyyaml stack, Project_Status.md schema, secrets model, silo model, tier system, template system.

---

## Architectural Constraints

- Hook scripts must be Node.js (Claude Code hook system requires shell commands — Node.js is universally available on Windows/Mac/Linux without extra deps).
- Python CLI orchestrates Node.js hooks (generates/manages `hooks.json` and hook scripts). The two runtimes don't call each other at runtime — Python installs files, Node.js runs them.
- LiteLLM proxy is optional. All agents degrade gracefully to Claude Sonnet 4.6 if proxy is not running.
- Vector stores (Phase 4) are entirely optional in Phase 1–3. Hooks must not fail if MCP servers are absent.
- No new Python dependencies added in Phase 1. Node.js hooks are self-contained with only `fs`, `path`, `os`, `child_process` (stdlib).

---

## Phase 1 — Hook Runtime

**Priority: Highest. Everything else depends on hooks existing.**  
**Deliverable**: SessionEnd fires, log.md never lost. PreToolUse hard-gates secrets and raw/.

### 1.1 — Create hook script directory

```
mewvault/
  hooks/
    hooks.json           ← hook definitions (ECC bootstrap resolver pattern)
    session-start.js     ← auto-orient
    session-end.js       ← auto-wrap (writes log.md)
    pre-tool-use.js      ← MewKing gate + GateGuard + secrets + raw guard
    post-tool-use.js     ← instinct extraction trigger (async)
    pre-compact.js       ← semantic map save
```

### 1.2 — `hooks/hooks.json`

Five hook definitions using the ECC dynamic plugin-root resolver inline. Hook IDs:
- `SessionStart` matcher `*` → `node hooks/session-start.js`
- `SessionEnd` matcher `*` → `node hooks/session-end.js` (async, non-blocking)
- `PreToolUse` matcher `Bash|Write|Edit|MultiEdit` → `node hooks/pre-tool-use.js` (timeout: 5s)
- `PostToolUse` matcher `Write|Edit|MultiEdit` → `node hooks/post-tool-use.js` (async, timeout: 10s)
- `PreCompact` matcher `*` → `node hooks/pre-compact.js`

The resolver pattern (from ECC): Each hook command is a `node -e "..."` inline that dynamically finds the mewvault root via `MEWVAULT_HOOK_ROOT` env var → walks up from `cwd` looking for `hooks/session-start.js` → falls back to `~/.mewvault`. `mew harness install` writes the resolved absolute path into `hooks.json` at install time, so runtime resolution is only a fallback.

**`mew harness install` writes this file to**: `<workspace_root>/.claude/hooks/hooks.json`

### 1.3 — `hooks/session-start.js`

Logic (in order):
1. Read `MEWVAULT_HOOK_ROOT` and `MEW_SESSION_START_MAX_TOKENS` (default: 6000).
2. Detect current silo from `process.env.PWD` or `process.cwd()`.
3. Load static vault rules from `.claude/rules/mew-common/` → write to stdout first (cache-eligible).
4. Load silo-specific rules from `.claude/rules/mew-<silo>/`.
5. Read `Project_Status.md` with field whitelist:
   ```js
   const WHITELIST = {
     code:   ['current_phase','stack','open_threads','tier','plan_approved'],
     design: ['current_phase','figma_file_key','greenlit','tier'],
     game:   ['current_phase','concepts_count','mechanics_count','tier'],
     wiki:   ['inbox_count','orphan_concepts'],
   };
   ```
6. Scan for ⚠ Unwrapped projects: any `log.md` with an open entry (no `auto-wrap` marker in last entry).
7. Read top-5 promoted instincts from `mewvault/instincts/promoted/*.json` → inject as structured context.
8. (Phase 4 addition) Query vector store for 5 relevant items if MCP available.
9. Write entire brief to stdout. Cap at `MEW_SESSION_START_MAX_TOKENS`.

### 1.4 — `hooks/session-end.js`

Logic:
1. Read session context from stdin (Claude Code passes transcript path in env).
2. Parse `CLAUDE_SESSION_TRANSCRIPT` path → extract last session's file activity.
3. Detect active project from cwd or transcript.
4. Write to `<project>/log.md`:
   ```
   - **YYYY-MM-DD HH:MM** — auto-wrap: <3-5 bullet summary from session> [auto-wrap]
   ```
5. If learning content detected (concepts-learned, lesson, wiki note): run lesson-wrap:
   a. Update `concepts-learned.md`
   b. Write session file to `wiki/concepts/<topic>/<concept>.md`
   c. Append to `Learning_Path.md`
   d. All three or rollback (write to temp files first, rename atomically).
6. If phase completion keyword in session: bump `current_phase` in `Project_Status.md`.
7. Write suggested commit message to `<workspace_root>/.claude/last-session-message.txt`.
8. Clear ⚠ Unwrapped flag (append `[auto-wrap]` marker to last log entry if missing).
9. (Phase 4 addition) Sync session facts to Anthropic Memory MCP.

### 1.5 — `hooks/pre-tool-use.js`

Receives tool name + input via stdin as JSON. Exit code 2 = hard block.

**Sub-logic A — MewKing Gate**:
```js
if (projectTier === 'MewKing' && !planApproved) {
  process.stderr.write('⛔ MewKing Gate: plan.md not approved.\n');
  incrementGateBlockCount();
  if (gateBlockCount >= 2) writeReviewRequired();
  process.exit(2);
}
```
Reads `Project_Status.md` from nearest project ancestor of `process.cwd()`.

**Sub-logic B — GateGuard Fact-Force** (from ECC):
Track first-edit-per-file in a session state file (`.claude/gateguard-session.json`). If this is the first write to a file this session AND no prior `Read` tool call for that file is detected in the transcript → warn (exit 0, stderr only). Hard block variant for MewKing projects.

**Sub-logic C — Secrets Guardian**:
```js
const SECRET_PATTERNS = [/sk-[a-zA-Z0-9]{20,}/, /ghp_[a-zA-Z0-9]{36}/, /AKIA[A-Z0-9]{16}/, /API_KEY\s*=/, /password\s*=/i];
if (!isInsideSecretsDir(filePath) && matchesSecretPattern(content)) {
  process.stderr.write('⛔ Secret detected outside secrets/\n');
  process.exit(2);
}
```

**Sub-logic D — Immutable Paths**:
```js
if (filePath.includes('/raw/') || filePath.includes('/.obsidian/')) {
  process.stderr.write('⛔ Immutable path blocked.\n');
  process.exit(2);
}
```

**Sub-logic E — TDD Gate** (warning only):
If writing to `src/` or `lib/` and no sibling `*.test.*` or `__tests__/` file exists → stderr warning, exit 0.

### 1.6 — `hooks/post-tool-use.js`

Async (Claude Code does not wait). 10s timeout.

Receives tool result via stdin as JSON. Scans for correction patterns in the session transcript excerpt:
```js
const CORRECTION_PATTERNS = [
  /no,?\s*actually/i,
  /that'?s wrong/i,
  /not like that/i,
  /don'?t do that/i,
];
```
If matched:
- Extract topic from surrounding context (use simple keyword extraction, no LLM call).
- Write to `mewvault/instincts/pending/<silo>-<timestamp>.json` with `confidence: 0.6`.

### 1.7 — `hooks/pre-compact.js`

Calls `mew compact --semantic --budget 4000` as a child process. Writes output to:
`<workspace_root>/.claude/context-snapshots/<silo>-<YYYY-MM-DD>.md`

Keeps 5 most recent snapshots (deletes oldest).

### 1.8 — Rule template directories

```
mewvault/templates/rules/
  mew-common/
    vault-rules.md      ← Never write to raw/, never modify .obsidian/, secrets in secrets/ only
    tier-gates.md       ← Pounce/Stalk/MewKing tier definitions and approval gate rules
    secrets.md          ← Secret handling rules
  mew-design/
    design-rules.md     ← 6-phase UX model, Figma token rules, greenlit gate
  mew-code/
    code-rules.md       ← TDD workflow, verification loop, openapi.yaml contract rules
  mew-game/
    godot-rules.md      ← Godot 4 dual-registry, GDScript conventions, scene tree discipline
```

`mew harness install` copies these to `<workspace_root>/.claude/rules/`.

### 1.9 — `mew harness` command (`mew/commands/harness.py`)

Subcommands:
- `install` — write hooks.json to `.claude/hooks/`, copy agents/ and rules/ to `.claude/`
- `status` — list active hooks with last-fire-time, MCP load per silo (reads `.claude/hooks/hooks.json` + any hook state files)
- `config` — edit `MEW_SESSION_START_MAX_TOKENS`, active MCPs per silo, hook profile (minimal/standard/strict)
- `disable <hook-id>` — write a `.claude/hooks/disabled.json` list; hooks.json unchanged
- `proxy start/stop/status` — manage LiteLLM subprocess (Phase 2, stubbed here)

### 1.10 — Update `mew/commands/init.py`

- Remove `_install_claude_commands()` call.
- Add `_install_mewharness(workspace_root)`:
  - Calls `mew harness install` logic inline.
  - Warns if `.claude/commands/*.md` files exist from v1.0, prompts to delete.
- Add `--no-harness` flag to opt out (for testing).

### 1.11 — Update `mew/cli.py`

Add `harness` subparser with `action` positional and `hook` optional argument.

### Phase 1 Acceptance Test

```bash
cd <workspace_root>
mew init
# Verify: no .claude/commands/ created
# Verify: .claude/hooks/hooks.json exists
# Verify: .claude/rules/mew-common/vault-rules.md exists
mew harness status
# Verify: 5 hooks listed as "installed"
# Open Claude Code → verify SessionStart fires (check stdout for brief)
# Ctrl+C close → verify log.md entry written
# Attempt to write to raw/any-file.md → verify exit code 2 block
```

---

## Phase 2 — Agent Array + Model Routing

**Priority: High. Specialist agents + cost reduction.**  
**Deliverable**: All 7 agents installed. `mew agent invoke` works. LiteLLM proxy routes to MiMo.

### 2.1 — Agent template files

```
mewvault/templates/agents/
  mew-planner.md     ← model: claude-opus-4-6, tools: [Read, Write, Glob]
  mew-designer.md    ← model: claude-sonnet-4-6, tools: [Read, Write, Glob, WebSearch]
  mew-coder.md       ← model: mimo-v2-pro, tools: [Read, Write, Glob, Bash, Grep]
  mew-gamedev.md     ← model: mimo-v2-pro, tools: [Read, Write, Glob, Bash]
  mew-learner.md     ← model: claude-sonnet-4-6, tools: [Read, Write, Glob]
  mew-archivist.md   ← model: claude-haiku-4-5, tools: [Read, Glob, Grep], max_tokens: 300
  mew-chief.md       ← model: claude-sonnet-4-6, tools: [Read, Glob]
```

Each file: YAML frontmatter (`name`, `model`, `tools`, `description`) + system prompt.  
`mew harness install` copies these to `<workspace_root>/.claude/agents/`.

### 2.2 — LiteLLM proxy config

```
mewvault/proxy/
  litellm-config.yaml    ← model routing: Anthropic models + MiMo-V2-Pro
  start-proxy.ps1        ← Windows: litellm --config proxy/litellm-config.yaml --port 4000
  start-proxy.sh         ← Mac/Linux: same
```

`mew init --mimo <api-key>` flag: calls `mew secret set MIMO_API_KEY`, generates `litellm-config.yaml` with key injected via `os.environ/MIMO_API_KEY`.

### 2.3 — `mew agent` command (`mew/commands/agent.py`)

- `mew agent list` — read `<workspace_root>/.claude/agents/*.md`, parse frontmatter, print table of name/model/silo scope.
- `mew agent invoke <agent> <task>` — spawn `claude --agent <agent>` subprocess with task. Log invocation to `.claude/agent-log.jsonl` (agent name, task excerpt, timestamp).

### 2.4 — Wire `mew-chief` as SessionStart entry point

Update `hooks/session-start.js` step 9: if `mew-chief` agent is installed and `MEW_USE_CHIEF=1`, emit a structured brief that includes a delegation suggestion (not a full chief invocation — that would require interactive mode).

### Phase 2 Acceptance Test

```bash
mew harness install
ls .claude/agents/
# Verify: 7 .md files present
mew agent list
# Verify: table with name/model/tools
mew harness proxy start
mew harness proxy status
# Verify: mimo-v2-pro reachable at localhost:4000
```

---

## Phase 3 — Instinct Pipeline

**Priority: Medium-High. Self-improvement loop.**  
**Deliverable**: Corrections auto-captured. SessionStart injects promoted instincts.

### 3.1 — Instinct infrastructure

```
mewvault/
  instincts/
    pending/    ← new instincts awaiting confidence threshold
    promoted/   ← active instincts injected by SessionStart
```

Both directories ship with `.gitkeep` (committed). JSON files in `pending/` and `promoted/` are gitignored (personal vault data, cross-machine via `mew instinct export/import`).

Add to `mewvault/.gitignore`:
```
instincts/pending/*.json
instincts/promoted/*.json
```

### 3.2 — Update `hooks/post-tool-use.js`

Full instinct extraction logic:
1. Parse stdin JSON for tool name + result.
2. Read last 10 messages from transcript excerpt (passed in `CLAUDE_TRANSCRIPT_EXCERPT` env or stdin).
3. Match correction patterns.
4. If matched: write `instincts/pending/<silo>-<project_hash>-<timestamp>.json`.
5. Check if same `(silo, topic, wrong_assumption)` tuple already exists in pending → bump confidence to 0.8 → auto-promote.

Project hash: `sha256(git remote url)[0:8]` if git remote exists, else `sha256(absolute project path)[0:8]`.

### 3.3 — Update `hooks/session-start.js`

After step 6 (recovery detection), add:
- Read all `instincts/promoted/*.json`.
- Filter by `silo` matching current silo.
- Sort by `confidence` descending, take top 5.
- Inject as:
  ```
  ## Active Vault Instincts
  - [godot] Use _unhandled_input() not _input() for non-propagating events (0.85)
  - [code] Always run verification-loop before commit (0.92)
  ```

### 3.4 — `mew instinct` command (`mew/commands/instinct.py`)

- `status` — read pending/ and promoted/, print table with id/silo/topic/confidence/status.
- `promote <id>` — move JSON from pending/ to promoted/, set `status: promoted`.
- `prune` — delete files in pending/ where `created` > 30 days ago AND `confidence < 0.5`.
- `export` — write all pending/ + promoted/ as single JSON array to stdout or `--out <file>`.
- `import <file>` — read JSON array, merge into pending/ (skip duplicates by id).

### 3.5 — Migrate v1.0 `concepts-learned.md`

`mew harness install` scans for `concepts-learned.md` files in known project paths. If found:
- Reads each bullet point.
- Writes a corresponding `instincts/promoted/<project_hash>-migrated-<n>.json` with `confidence: 0.75, source: "migrated-from-concepts-learned"`.
- Appends a migration notice to the concepts-learned.md: `<!-- migrated to instinct pipeline YYYY-MM-DD -->`.

### 3.6 — `mew compact` command (`mew/commands/compact.py`)

- `mew compact --semantic` — reads log.md files (last 3 entries each), Project_Status.md files (one-line summary), promoted instincts, and orphan wikilink scan.
- Formats output as:
  ```
  [ACTIVE THREADS]
  <project>: <last_3_log_entries>

  [PROJECT STATES]
  <project> | <phase> | <last_action>

  [INSTINCTS]
  <top_5_promoted>

  [ORPHANS]
  <referenced_but_missing_wikilinks>
  ```
- `--budget <tokens>` — truncate output to token budget (approx 4 chars/token).
- `--silo <name>` — filter to one silo.
- `--semantic` — full map with all sections (default if no flags).

### Phase 3 Acceptance Test

```bash
# In a game session: make a GDScript mistake, user says "No, actually..."
ls mewvault/instincts/pending/
# Verify: JSON file created with confidence: 0.6
mew instinct status
# Verify: pending instinct listed
mew instinct promote <id>
ls mewvault/instincts/promoted/
# Verify: moved to promoted
# Open new Claude Code session → verify instinct appears in SessionStart brief
mew compact --semantic
# Verify: all 4 sections present, within token budget
```

---

## Phase 4 — Vector Stores

**Priority: Medium. Semantic memory for growing vault.**  
**Deliverable**: Three-store architecture live. Semantic search working per silo.

### 4.1 — MCP config files

```
mewvault/mcp-configs/
  memory-mcp.json      ← @modelcontextprotocol/server-memory config
  doobidoo.json        ← mcp-memory-service config (SQLite path, embedding model)
  chromadb.json        ← ChromaDB community MCP server config
```

`mew harness config --active-mcps` reads these and writes the appropriate subset to `<workspace_root>/.claude/settings.json` `mcpServers` block based on current silo.

### 4.2 — Update `hooks/session-end.js`

After log.md write, add (guarded by try/catch — never fail session-end):
- If wiki silo: call doobidoo MCP to index session summary.
- If code/game silo: call ChromaDB MCP to re-index modified files (read `.claude/modified-files-<session>.json` written by PostToolUse accumulator).

### 4.3 — Update `hooks/session-start.js`

After instinct injection, add:
- If wiki silo and doobidoo MCP available: query for 5 most relevant concepts.
- If code/game silo and ChromaDB MCP available: query for 5 most relevant code chunks.
- Inject as `## Relevant Context (semantic)`.
- If MCP unavailable: skip silently (no error).

### 4.4 — `mew harness config --active-mcps`

Reads `mewvault/mcp-configs/*.json`, prompts user to select which to activate per silo type. Writes to `<workspace_root>/.claude/settings.json`.

### 4.5 — Installation dependencies (documented, not automated)

Add to README v2.0:
```bash
# Anthropic Memory MCP
npx -y @modelcontextprotocol/server-memory

# doobidoo (wiki silo)
pip install mcp-memory-service

# ChromaDB (code/game silo)
pip install chromadb
# + install ChromaDB community MCP server

# Ollama (local embeddings, free)
# Pull: ollama pull nomic-embed-text
# tree-sitter + GDScript grammar: pip install tree-sitter
```

### Phase 4 Acceptance Test

```bash
# wiki silo session: open Claude Code
# Verify: SessionStart brief contains "Relevant Context (semantic)" section
# code session: open Claude Code
# Verify: SessionStart brief contains relevant code chunk
mew harness status
# Verify: active MCPs listed per silo
```

---

## Phase 5 — Token Optimization

**Priority: Medium. Cost reduction + context efficiency.**  
**Deliverable**: Prompt caching active. CLAUDE.md slimming tool working.

### 5.1 — Enforce injection order in `session-start.js`

Strict order already planned in 1.3. Verify implementation matches:
1. Static vault rules (cache-eligible prefix)
2. Static silo rules (cache-eligible prefix)
3. Dynamic project status (whitelisted fields only)
4. Semi-dynamic instincts
5. Dynamic vector context

Add a comment block at the top of session-start.js:
```js
// CACHE-OPTIMIZATION: Sections 1-2 must come before any dynamic content.
// Anthropic caches static prompt prefixes; reordering breaks cache hits.
```

### 5.2 — `mew validate --slim` flag

Update `mew/commands/validate.py`:
- Add `--slim` flag.
- Scan all `CLAUDE.md` files in workspace.
- Flag any sentence >20 words.
- Suggest tighter rewrites (heuristic: strip "you should be aware that", "it is important to note that", "please ensure that", etc.).
- Output as diff-style suggestions, never auto-apply.
- Print total estimated token savings (word count delta × 0.75 tokens/word approximation).

### 5.3 — Verify field whitelists

Audit `session-start.js` WHITELIST object. Ensure no silo leaks fields from another silo's domain. Add a test: run `mew harness status --verbose` and check that the injected field list matches the whitelist for a given silo.

### 5.4 — `max_tokens: 300` on `mew-archivist.md`

Ensure `mewvault/templates/agents/mew-archivist.md` YAML frontmatter includes:
```yaml
max_tokens: 300
```
And document that this prevents Haiku's tendency to over-explain in indexing responses.

### Phase 5 Acceptance Test

```bash
mew validate --slim
# Verify: flags verbose sentences in CLAUDE.md files, reports token savings
# Check Anthropic API response headers for cache_creation_input_tokens / cache_read_input_tokens
# Verify: subsequent sessions show cache_read > 0
```

---

## Phase 6 — MCP Integrations + ECC Skills

**Priority: Medium. Automate external workflows.**  
**Deliverable**: ECC skills wired. GitHub + Figma MCP integrated.

### 6.1 — Copy ECC skills

```
mewvault/skills/
  tdd-workflow/
    SKILL.md    ← from affaan-m/everything-claude-code skills/tdd-workflow/SKILL.md
  verification-loop/
    SKILL.md    ← from affaan-m/everything-claude-code skills/verification-loop/SKILL.md
  code-reviewer/
    SKILL.md    ← from affaan-m/everything-claude-code agents/code-reviewer.md (adapted)
```

Note: `code-reviewer` in ECC is an agent file, not a skill. Adapt it: strip the YAML frontmatter model/tools fields, keep the system prompt as the SKILL.md body. `mew-coder` invokes it inline rather than as a separate agent spawn.

`mew harness install` copies these to `<workspace_root>/.claude/skills/` (or wherever Claude Code loads skill files from).

### 6.2 — Update `session-start.js` — GitHub MCP

If `GITHUB_MCP_ENABLED=1` env var and GitHub MCP server is in `settings.json`:
- Fetch open issues for current silo's git remote repo.
- Filter issues with labels matching `current_phase` or `blocked`.
- Inject as:
  ```
  ## Open GitHub Issues (blocking current phase)
  - #42 Authentication fails on mobile Safari [bug, phase-3]
  ```
- If GitHub MCP unavailable: skip silently.

### 6.3 — Update `mew/commands/sync.py`

If `--pr` flag added: use GitHub MCP to create PR from last-session-message.txt as body. Link any issue numbers detected in the commit message.

### 6.4 — Update `templates/agents/mew-designer.md`

System prompt addition for Phase 4 (high-fi):
```
At Phase 4, use the Figma MCP tool get_design_context with the project's figma_file_key
from Project_Status.md. Extract design tokens (colors, typography, spacing).
Write tokens to <project>/tokens/design-tokens.css.
```

### 6.5 — Update `mew/commands/promote.py` (ux→code path)

After creating code project, if Figma MCP available:
- Read `figma_file_key` from source UX project's `Project_Status.md`.
- Call Figma MCP `get_variable_defs`.
- Append design tokens as a comment block to the new code project's `CLAUDE.md`.

### Phase 6 Acceptance Test

```bash
ls .claude/skills/
# Verify: tdd-workflow/, verification-loop/, code-reviewer/ present
# Open Claude Code in game session with GitHub MCP connected
# Verify: SessionStart shows open issues for current_phase
mew promote <ux-project> --to <code-project>
# If Figma MCP connected: verify design tokens in new project's CLAUDE.md
```

---

## Phase 7 — Cross-Platform + Ship

**Priority: Must-do before sharing.**  
**Deliverable**: Cursor rules parity. Repo clean. Full dogfood.

### 7.1 — Cursor rule templates

```
mewvault/templates/cursor-rules/
  mew-common/
    vault-rules.md    ← same content as .claude/rules/mew-common/vault-rules.md
  mew-game/
    godot-rules.md
  mew-design/
    design-rules.md
  mew-code/
    code-rules.md
```

`mew harness install` copies these to `<workspace_root>/.cursor/rules/`.

### 7.2 — `mew harness status` parity check

Add a check: for each file in `.claude/rules/mew-common/`, verify a matching file exists in `.cursor/rules/mew-common/`. If drift detected:
```
⚠ Rules parity drift detected:
  .claude/rules/mew-common/tier-gates.md → missing in .cursor/rules/
  Run: mew harness install --cursor-only to fix
```

### 7.3 — Clean up v1.0 artifacts

- Delete `mewvault/templates/commands/` directory (start.md, wrap.md, plan.md, teach.md).
- Update `mew/commands/init.py`: remove all references to `templates/commands/`.
- Update `mew/commands/help_cmd.py`: remove slash command section, add "Hooks are now automatic" note.
- Update `README.md`: v2.0 architecture section.

### 7.4 — Full dogfood test

```bash
# Fresh workspace init
mew init
# Verify: no .claude/commands/, all 5 hooks, all 7 agents, all 4 rule dirs
mew harness status
# Open Claude Code → SessionStart fires
# Create a new code project
mew new code-project test-project --stack next
# Use mew-planner to plan a MewKing feature
mew agent invoke mew-planner "add auth flow"
# Verify: plan.md created in proposals/active/
# Try to write code without approval → verify PreToolUse blocks
# Approve plan → write code → verify PostToolUse extracts no instincts
# Close Claude Code → verify SessionEnd writes log.md
mew harness status
# Verify: last fire times updated for all hooks
```

### 7.5 — README v2.0

Sections:
- What's new in v2.0 (hook runtime, agents, model routing)
- Installation: `pip install -e .` + `node --version` (18+ required) + `mew init`
- Optional: MiMo setup (`mew init --mimo <key>`)
- Optional: Vector stores (Phase 4 guide)
- Migration from v1.0

---

## File Change Summary

### New files (39 total)

```
mewvault/hooks/hooks.json
mewvault/hooks/session-start.js
mewvault/hooks/session-end.js
mewvault/hooks/pre-tool-use.js
mewvault/hooks/post-tool-use.js
mewvault/hooks/pre-compact.js
mewvault/instincts/pending/.gitkeep
mewvault/instincts/promoted/.gitkeep
mewvault/proxy/litellm-config.yaml
mewvault/proxy/start-proxy.ps1
mewvault/proxy/start-proxy.sh
mewvault/mcp-configs/memory-mcp.json
mewvault/mcp-configs/doobidoo.json
mewvault/mcp-configs/chromadb.json
mewvault/templates/agents/mew-planner.md
mewvault/templates/agents/mew-designer.md
mewvault/templates/agents/mew-coder.md
mewvault/templates/agents/mew-gamedev.md
mewvault/templates/agents/mew-learner.md
mewvault/templates/agents/mew-archivist.md
mewvault/templates/agents/mew-chief.md
mewvault/templates/rules/mew-common/vault-rules.md
mewvault/templates/rules/mew-common/tier-gates.md
mewvault/templates/rules/mew-common/secrets.md
mewvault/templates/rules/mew-design/design-rules.md
mewvault/templates/rules/mew-code/code-rules.md
mewvault/templates/rules/mew-game/godot-rules.md
mewvault/templates/cursor-rules/mew-common/vault-rules.md
mewvault/templates/cursor-rules/mew-game/godot-rules.md
mewvault/templates/cursor-rules/mew-design/design-rules.md
mewvault/templates/cursor-rules/mew-code/code-rules.md
mewvault/skills/tdd-workflow/SKILL.md
mewvault/skills/verification-loop/SKILL.md
mewvault/skills/code-reviewer/SKILL.md
mewvault/mew/commands/harness.py
mewvault/mew/commands/agent.py
mewvault/mew/commands/instinct.py
mewvault/mew/commands/compact.py
mewvault/proposals/active/v2-mewharness/plan.md  ← this file
mewvault/proposals/active/v2-mewharness/status.yaml
```

### Modified files (4 total)

```
mewvault/mew/cli.py              ← add harness, agent, instinct, compact subparsers
mewvault/mew/commands/init.py    ← remove _install_claude_commands, add _install_mewharness
mewvault/mew/commands/validate.py ← add --slim flag
mewvault/mew/commands/sync.py    ← add --pr flag (Phase 6)
```

### Deleted files (4 total)

```
mewvault/templates/commands/start.md
mewvault/templates/commands/wrap.md
mewvault/templates/commands/plan.md
mewvault/templates/commands/teach.md
```

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Hook scripts fail silently | `session-end.js` never throws — all errors caught, written to `.claude/hook-errors.log` |
| MiMo API unavailable | All agents in litellm-config have `fallback: claude-sonnet-4-6`; proxy start is optional |
| PreToolUse false-positive blocks | `mew harness disable pre-tool-use` as escape hatch; gate_block_count visible in `mew harness status` |
| Vector stores unavailable | All vector queries wrapped in try/catch; session-start proceeds without them |
| Node.js not installed | `mew harness install` checks `node --version` and warns; Python CLI works without Node |
| instincts/pending grows unbounded | `mew instinct prune` removes expired low-confidence instincts; can be added to session-end |

---

## Open Questions (resolved before implementation)

1. **Hook transport format**: Claude Code passes hook data via stdin as JSON. Need to verify exact schema for PreToolUse (tool name + input) and PostToolUse (tool name + result + transcript excerpt). → Verify from Claude Code docs before implementing `pre-tool-use.js`.
2. **SessionEnd vs Stop**: Confirmed: `SessionEnd` fires on actual session termination. `Stop` fires after every response. log.md write goes in `SessionEnd`. Cost tracking goes in `Stop`. Both are implemented.
3. **Skills directory location**: Verify where Claude Code loads skills from (`.claude/skills/` or `~/.claude/skills/` or per project). → Check before Phase 6.
4. **`mew compact` as Python vs Node**: Implemented in Python (`mew/commands/compact.py`) since it reads markdown and YAML files — Python is better suited. `pre-compact.js` calls it as a subprocess.

---

## APPROVED

*(Write "APPROVED" on the line above to unlock implementation. mew-planner will then set plan_approved: true in status.yaml.)*
