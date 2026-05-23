"""mew help — command reference."""

MAIN_HELP = """
mew — MewVault CLI v2.0

Commands:
  init            Bootstrap the workspace (silos, CLAUDE.md files, git repos)
  status          Show project status across all silos
  new             Scaffold a new project or learning path
  validate        Check all Project_Status.md files for schema compliance
  secret          Manage secrets (get, set, list, rotate)
  dump            Token-budgeted project context snapshot
  promote         Promote projects across silos (UX→Code, wiki→UX, experiment→game)
  abandon         Mark a project as abandoned
  rename          Rename a project folder and update its Project_Status.md
  rebuild-status  Regenerate a missing or corrupted Project_Status.md
  archive         Move a project to _archive/ with per-silo behavior
  package         Assemble a client deliverable package from a UX project
  process-inbox   List wiki/_inbox/ and propose routing for each file
  sync            Git status across all repos, with optional commit or PR
  harness         Install and manage the MewHarness hook runtime
  agent           List or invoke specialist agents
  instinct        Manage the instinct pipeline (promote, prune, export)
  compact         Generate a semantic context map for pre-compaction snapshots
  help            Show this help or detail for a specific command

Hooks are now automatic — SessionStart, SessionEnd, PreToolUse, PostToolUse, and
PreCompact fire without slash commands. Run 'mew harness install' once to activate.

Run 'mew help <command>' for details on any command.
Run 'mew help triggers' for the full conversational triggers reference.
"""

TRIGGERS_HELP = """
Conversational Triggers (just say these to Claude):

  "process the inbox"                   Wiki ingestion pipeline
  "sync figma"                           Pull Figma snapshot for current UX project
  "refresh figma in <project>"           Update design tokens in code project CLAUDE.md
  "record this as a decision"            Draft ADR in decisions/
  "advance the phase" / "phase complete" Phase transition in UX project
  "inject findings into <project>"       UX audit → code project backlog
  "package for the client"               Assemble client deliverable package
  "promote this to a code project"       UX → code promotion
  "promote this experiment"              game-lab/_experiments → game project
  "archive this project"                 Archive with retro (code/games) or status update
"""

COMMAND_HELP = {
    "init": """
mew init [--path <workspace-root>] [--no-git]

Bootstraps the entire workspace from zero:
  - Creates wiki/, design-studio/, software-projects/, game-lab/
  - Writes CLAUDE.md files from templates for each silo
  - Creates mewvault/secrets/ with restricted permissions (gitignored)
  - Optionally initializes git repos for wiki, design-studio, game-lab
    (each code project gets its own git repo via 'mew new code-project')
  - Runs mew validate to confirm everything is correct

Options:
  --path <dir>   Workspace root directory (default: parent of mewvault/)
  --no-git       Skip git initialization

Usage:
  cd Jan/ && python mewvault/mew.py init
  python mew.py init --path /path/to/workspace
""",
    "status": """
mew status [options]

Shows project status across all silos. Default: vault overview format.

Options:
  --domain <silo>    Filter to one silo: wiki | design | software | games
  --project <name>   Deep view for a single project
  --stale <days>     Show only projects not touched in N+ days
  --blocked          Show only blocked projects
  --quick            Vault overview format (cached output used by /start)

Examples:
  mew status
  mew status --domain design
  mew status --project acme-rebrand
  mew status --stale 7 --blocked
""",
    "new": """
mew new <type> <name> [--stack next|astro|sveltekit]

Scaffold a new project from templates.

Types:
  ux-project       design-studio/<name>/  with 6-phase structure (00_discovery … 05_handoff)
  code-project     software-projects/<name>/  with proposals/, decisions/, docs/ux/
  game-project     game-lab/<name>/  with Godot 4 structure + registries
  game-experiment  game-lab/_experiments/<name>/  throwaway prototype
  learning-path    wiki/learning/<name>/  with registry, session log, resources

Examples:
  mew new ux-project acme-rebrand
  mew new code-project acme-web --stack next
  mew new game-project space-shooter
  mew new game-experiment bullet-pattern
  mew new learning-path rust
""",
    "validate": """
mew validate [--fix] [--slim]

Checks all Project_Status.md files across the workspace:
  - Required fields: project, status, next_action
  - Valid status values: active | greenlit | blocked | archived | abandoned
  - Recommended fields: last_session, last_wrap, started (warnings, not errors)

--fix:  (not yet implemented) offer to repair fixable issues
--slim: scan all CLAUDE.md files for verbose sentences and suggest tighter rewrites.
        Reports diff-style suggestions and estimated token savings. Never auto-applies.

Exit code 1 if any errors found.
""",
    "secret": """
mew secret <action> [key] [--scope <project>] [--backend env|keychain]

Manage secrets stored in mewvault/secrets/<scope>.env (gitignored, owner-only).

Actions:
  set <key>     Store a secret (prompts for value, never echoed)
  get <key>     Confirm a secret exists (value never printed)
  list          List secret key names in scope
  rotate <key>  Update a secret value

Options:
  --scope <name>    Project scope (default: workspace). Per-project Figma tokens
                    use --scope <project-name>.
  --backend         env (default, cross-platform) | keychain (macOS only, optional)

Examples:
  mew secret set FIGMA_TOKEN --scope acme-rebrand
  mew secret list --scope acme-rebrand
  mew secret rotate OPENAI_API_KEY
""",
    "dump": """
mew dump <project> [--budget <chars>] [--include phase|decisions]

Assembles a token-budgeted context snapshot for use in Claude Code sessions.

Budget is in characters (rough: 4 chars ≈ 1 token).
Default: 16,000 chars (~4k tokens).

Contents (truncated to budget):
  1. Project_Status.md (full)
  2. Last 3 decision records
  3. Current phase artifacts (title + first 200 chars)
  4. Open questions

Examples:
  mew dump acme-rebrand
  mew dump mewvault-web --budget 8000 --include decisions
""",
    "abandon": """
mew abandon <project> [--reason "..."]

Marks a project as abandoned in its Project_Status.md. Prompts for a reason
if --reason is not given. Does not move files — run 'mew archive' after.

Example:
  mew abandon old-prototype --reason "pivoted to different approach"
""",
    "rename": """
mew rename <old-name> <new-name>

Renames a project folder and updates the project: field in Project_Status.md.
Uses 'git mv' if the silo is a git repo, otherwise a plain filesystem rename.

Example:
  mew rename acme-rebrand acme-brand-refresh
""",
    "rebuild-status": """
mew rebuild-status <project> [--type ux-project|code-project|game-project] [--stack next]

Regenerates a Project_Status.md from the appropriate template. Useful when the
status file is missing or corrupted. Prompts before overwriting if file exists.

The project type is auto-detected from the silo (design→ux, software→code,
games→game). Use --type to override.

Example:
  mew rebuild-status old-project --type code-project
""",
    "archive": """
mew archive <project>
mew archive wiki/learning/<topic>

Moves a project to _archive/ within its silo and sets status: archived.
Uses 'git mv' if the silo is a git repo.

For learning paths, also sets the concepts-learned.md registry to read-only.

Examples:
  mew archive sample-brand
  mew archive wiki/learning/rust
""",
    "package": """
mew package <project> [--format client] [--push-drive]

Assembles a client deliverable package from a UX project. Copies available
handoff artifacts (insights, figma-snapshot, design-decisions, specs, dev-notes)
into a '<project>-client-package/' folder alongside the project.

--push-drive: prints Drive push instructions for use with the Drive MCP in
Claude Code. Does not push automatically.

Example:
  mew package sample-brand --format client --push-drive
""",
    "promote": """
mew promote <source> [--to <name>] [--name <name>] [--topic <tag>] [--stack ...]

Three promotion flows:

  UX → Code (default):
    mew promote <ux-name> --to <code-name> [--stack next]
    Pre-condition: greenlit: true OR current_phase: 5 in Project_Status.md.
    Scaffolds code project, copies UX artifacts to docs/ux/, seeds CLAUDE.md.

  Wiki → UX:
    mew promote wiki/ --topic <tag> --name <ux-name>
    Searches wiki/ for notes tagged with <tag>, scaffolds a UX project,
    copies matching notes to 00_discovery/.

  Experiment → Game project:
    mew promote game-lab/_experiments/<exp> --name <new-name>
    Scaffolds a tracked game project, seeds session notes into sessions/.

Examples:
  mew promote sample-brand --to sample-web --stack next
  mew promote wiki/ --topic bangla-ux --name bangla-keyboard
  mew promote game-lab/_experiments/bullet-test --name space-shooter
""",
    "process-inbox": """
mew process-inbox

Lists all files in wiki/_inbox/ (excluding originals/) and suggests a routing
category for each based on file extension.

Output is for human review — actual processing and file movement happen in Claude
via the "process the inbox" conversational trigger.

PDFs: Docling extraction runs first; original is moved to _inbox/originals/.
""",
    "sync": """
mew sync [--commit "<msg>"] [--push] [--pr]

Default (no flags): read-only git status across all silo repos.

--commit "<msg>"  Interactive mode: for each repo with changes, show diff
                  and prompt y/n/skip to commit with the given message.
--push            After committing, also push to the remote.
--pr              Create a GitHub PR from .claude/last-session-message.txt.
                  Uses the current branch name as the PR title. Extracts #N
                  issue numbers from the body and appends Closes #N links.
                  Requires the 'gh' CLI to be installed and authenticated.

Examples:
  mew sync
  mew sync --commit "session: design review 2026-05-04"
  mew sync --commit "chore: weekly wrap" --push
  mew sync --pr
""",
    "harness": """
mew harness <action> [--path <workspace>] [--verbose] [--active-mcps]

Manage the MewHarness hook runtime — 5 hooks that power v2.0 automation.

Actions:
  install   Register all 5 hooks in .claude/settings.json, copy rule templates
  status    Show hook registration state, rule dirs, instinct counts
  config    Print harness env vars and active MCPs
  disable   Remove MewHarness hooks from .claude/settings.json
  proxy     Manage the LiteLLM agent proxy (start / stop)

Flags:
  --verbose       (status) Also print the Project_Status.md field whitelist per silo
  --active-mcps   (config) Interactively select MCP servers to activate per silo

Hooks registered:
  UserPromptSubmit  → session-start.js  (rules + status + instincts + semantic context)
  Stop              → session-end.js    (auto-wrap log entry + commit message)
  PreToolUse        → pre-tool-use.js   (MewKing gate, secrets, raw/ guard, TDD)
  PostToolUse       → post-tool-use.js  (activity accumulation, instinct signals)
  PreCompact        → pre-compact.js    (semantic compact, context snapshots)

Examples:
  mew harness install
  mew harness status --verbose
  mew harness config --active-mcps
  mew harness disable
""",
    "agent": """
mew agent list
mew agent invoke <name> [--task "description"]

List or invoke specialist agents. Each agent runs as a Claude Code sub-agent
via: claude --model <alias> --append-system-prompt <template> [--print <task>]

No proxy required. Works with Claude Code subscription or ANTHROPIC_API_KEY.

Agents:
  mew-planner    opus    Architecture, MewKing plans
  mew-designer   sonnet  UX, Figma review, component specs
  mew-coder      sonnet  Implementation, refactoring, test generation
  mew-gamedev    sonnet  GDScript, game mechanics, Godot patterns
  mew-learner    sonnet  Concept distillation, research ingest
  mew-archivist  haiku   Session wrap, log writes, git messages
  mew-chief      sonnet  Cross-silo orchestration, triage, routing

Examples:
  mew agent invoke mew-archivist --task "write the session log for today"
  mew agent invoke mew-planner --task "plan the token pipeline refactor"
  mew agent invoke mew-coder          # interactive session as mew-coder
""",
    "instinct": """
mew instinct <action>

Manage the instinct pipeline — behavioral corrections auto-captured by PostToolUse.

Actions:
  status              Show pending and promoted instincts with confidence scores
  promote <id>        Move a pending instinct to promoted/ (injected by SessionStart)
  promote <id> --confidence 0.9   Promote with a confidence override
  prune               Remove pending instincts older than 14 days, conf < 0.8
  export [--out file] Export all promoted instincts to JSON
  import <file>       Import instincts from a JSON export

Lifecycle:
  PostToolUse writes pending/ (confidence: 0.6) on rapid-rewrite signals
  'mew instinct promote' moves to promoted/ when you confirm the correction
  SessionStart injects top-5 promoted instincts into every session brief

Examples:
  mew instinct status
  mew instinct promote code-rewrite-abc12345-1234567890
  mew instinct prune
  mew instinct export --out my-instincts.json
""",
    "compact": """
mew compact [--semantic] [--budget <tokens>] [--project <name>]

Generate a semantic context map for pre-compaction snapshots.
Called automatically by pre-compact.js; can also be run manually.

--semantic      Include recent log entries (last 5) per project
--budget N      Token budget, default 4000 (chars = N * 4)
--project name  Scope output to one project

Output goes to stdout; pre-compact.js writes it to
.claude/context-snapshots/<silo>-<date>.md

Examples:
  mew compact --semantic
  mew compact --semantic --budget 2000 --project acme-web
""",
}


def run_help(topic) -> None:
    if topic is None:
        print(MAIN_HELP)
        return

    if topic == "triggers":
        print(TRIGGERS_HELP)
        return

    detail = COMMAND_HELP.get(topic)
    if detail:
        print(detail)
        return

    print(f"Unknown topic: '{topic}'")
    print("Try: mew help | mew help slash | mew help triggers | mew help <command>")
