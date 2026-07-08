"""CLI argument parsing and command dispatch."""
import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mew",
        description="MewVault — federated AI workspace manager",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show help")

    subparsers = parser.add_subparsers(dest="command")

    # init
    p_init = subparsers.add_parser("init", help="Bootstrap the workspace")
    p_init.add_argument("--path", type=Path, help="Workspace root (default: parent of mewvault/)")
    p_init.add_argument("--no-git", action="store_true", help="Skip git init for silos")

    # status
    p_status = subparsers.add_parser("status", help="Show project status")
    p_status.add_argument("--domain", metavar="SILO", help="Filter to one silo")
    p_status.add_argument("--project", metavar="NAME", help="Single project deep view")
    p_status.add_argument("--stale", type=int, metavar="DAYS", help="Projects not touched in N+ days")
    p_status.add_argument("--blocked", action="store_true", help="Blocked projects only")
    p_status.add_argument("--quick", action="store_true", help="Vault overview format")

    # new
    p_new = subparsers.add_parser("new", help="Scaffold a new project")
    p_new.add_argument(
        "type",
        choices=["ux-project", "code-project", "game-project", "game-experiment", "learning-path"],
    )
    p_new.add_argument("name", help="Project name (kebab-case recommended)")
    p_new.add_argument("--stack", choices=["next", "astro", "sveltekit"], help="Code project stack")

    # validate
    p_validate = subparsers.add_parser("validate", help="Check schema compliance")
    p_validate.add_argument("--fix", action="store_true", help="Offer to repair fixable issues")
    p_validate.add_argument("--slim", action="store_true",
                            help="Scan CLAUDE.md files for verbose sentences and suggest tighter rewrites")

    # secret
    p_secret = subparsers.add_parser("secret", help="Manage secrets")
    p_secret.add_argument("action", choices=["get", "set", "list", "rotate"])
    p_secret.add_argument("key", nargs="?", help="Secret key name")
    p_secret.add_argument("--scope", help="Project scope (default: workspace)")
    p_secret.add_argument("--backend", choices=["env", "keychain"], default="env")

    # dump
    p_dump = subparsers.add_parser("dump", help="Token-budgeted context snapshot")
    p_dump.add_argument("project", help="Project name")
    p_dump.add_argument("--budget", type=int, default=16000, help="Character budget (default: 16000)")
    p_dump.add_argument("--include", choices=["phase", "decisions"], action="append", default=[])

    # promote (all three flows)
    p_promote = subparsers.add_parser("promote", help="Promote projects across silos")
    p_promote.add_argument("source", help="Source: <ux-name> | wiki/ | game-lab/_experiments/<name>")
    p_promote.add_argument("--to", metavar="NAME", help="Destination name (UX→Code) or 'game-project'")
    p_promote.add_argument("--name", metavar="NAME", help="New project name (wiki→UX, experiment→game)")
    p_promote.add_argument("--topic", metavar="TAG", help="Wiki tag to search (wiki→UX only)")
    p_promote.add_argument("--stack", choices=["next", "astro", "sveltekit"], default="next")

    # abandon
    p_abandon = subparsers.add_parser("abandon", help="Mark a project as abandoned")
    p_abandon.add_argument("project", help="Project name")
    p_abandon.add_argument("--reason", metavar="TEXT", help="Reason (skips interactive prompt)")

    # rename
    p_rename = subparsers.add_parser("rename", help="Rename a project folder")
    p_rename.add_argument("old_name", help="Current project name")
    p_rename.add_argument("new_name", help="New project name (kebab-case)")

    # rebuild-status
    p_rebuild = subparsers.add_parser("rebuild-status", help="Regenerate a missing Project_Status.md")
    p_rebuild.add_argument("project", help="Project folder name")
    p_rebuild.add_argument("--type", choices=["ux-project", "code-project", "game-project"],
                           dest="type", help="Force project type")
    p_rebuild.add_argument("--stack", default="next", help="Stack (code projects, default: next)")

    # archive
    p_archive = subparsers.add_parser("archive", help="Move a project to _archive/")
    p_archive.add_argument("target", help="Project name or 'wiki/learning/<topic>'")

    # package
    p_package = subparsers.add_parser("package", help="Assemble a client deliverable package")
    p_package.add_argument("project", help="UX project name")
    p_package.add_argument("--format", choices=["client"], default="client")
    p_package.add_argument("--push-drive", action="store_true",
                           help="Print Drive push instructions (use Drive MCP in Claude Code)")
    p_package.add_argument("--design", action="store_true",
                           help="Full design handoff: + PRODUCT.md, DESIGN.md, audit scores, decision log, assets manifest")

    # process-inbox
    subparsers.add_parser("process-inbox", help="List wiki/_inbox/ and propose routing")

    # sync
    p_sync = subparsers.add_parser("sync", help="Git status across all repos")
    p_sync.add_argument("--commit", metavar="MSG", help="Interactively commit each repo")
    p_sync.add_argument("--push", action="store_true", help="Push after committing")
    p_sync.add_argument("--pr", action="store_true",
                        help="Create a GitHub PR from last-session-message.txt (requires gh CLI)")

    # harness
    p_harness = subparsers.add_parser("harness", help="Manage the MewHarness hook runtime")
    p_harness.add_argument(
        "action",
        choices=["install", "status", "config", "disable", "proxy"],
        help="install: register hooks; status: show state; config: show env vars; disable: remove hooks; proxy: manage LiteLLM proxy",
    )
    p_harness.add_argument("--path", type=Path, help="Workspace root override")
    p_harness.add_argument("--stop", action="store_true", help="Stop the running proxy (proxy action only)")
    p_harness.add_argument("--verbose", action="store_true",
                            help="Show whitelist fields per silo (status action only)")
    p_harness.add_argument("--active-mcps", action="store_true", dest="active_mcps",
                           help="Interactively select and activate MCP servers per silo (config action only)")
    p_harness.add_argument("key", nargs="?", help="Config key (for config action)")
    p_harness.add_argument("value", nargs="?", help="Config value (for config action)")

    # agent
    p_agent = subparsers.add_parser("agent", help="List or invoke specialist agents")
    p_agent_sub = p_agent.add_subparsers(dest="agent_action")
    p_agent_list = p_agent_sub.add_parser("list", help="List available agents")
    p_agent_invoke = p_agent_sub.add_parser("invoke", help="Invoke an agent by name")
    p_agent_invoke.add_argument("name", help="Agent name (e.g. mew-planner)")
    p_agent_invoke.add_argument("--task", metavar="TEXT", help="Task description to pass")
    p_agent_sub.add_parser("sync", help="Rebuild the agent routing index from skills/")
    p_agent_status = p_agent_sub.add_parser("status", help="Show recent agent dispatches from the ledger")
    p_agent_status.add_argument("--limit", type=int, default=20, help="Rows to show (default 20)")
    p_fetch = p_agent_sub.add_parser("fetch-skills", help="Fetch skills from online sources")
    p_fetch.add_argument("--from", dest="from_source", metavar="SOURCE", help="Named source (e.g. awesome-claude)")
    p_fetch.add_argument("--url", metavar="URL", help="Direct URL to a skill file")

    # instinct
    p_instinct = subparsers.add_parser("instinct", help="Manage the instinct pipeline")
    p_instinct_sub = p_instinct.add_subparsers(dest="instinct_action")
    p_instinct_sub.add_parser("status", help="Show pending and promoted instincts")
    p_instinct_promote = p_instinct_sub.add_parser("promote", help="Promote a pending instinct")
    p_instinct_promote.add_argument("id", help="Instinct ID")
    p_instinct_promote.add_argument("--confidence", type=float, help="Override confidence score")
    p_instinct_sub.add_parser("prune", help="Remove stale pending instincts")
    p_instinct_export = p_instinct_sub.add_parser("export", help="Export promoted instincts to JSON")
    p_instinct_export.add_argument("--out", metavar="FILE", help="Output file path")
    p_instinct_import = p_instinct_sub.add_parser("import", help="Import instincts from JSON")
    p_instinct_import.add_argument("file", help="JSON file to import from")

    # compact
    p_compact = subparsers.add_parser("compact", help="Generate a semantic context map")
    p_compact.add_argument("--semantic", action="store_true", help="Include semantic analysis")
    p_compact.add_argument("--budget", type=int, default=4000, help="Token budget (default: 4000)")
    p_compact.add_argument("--project", metavar="NAME", help="Scope to a specific project")

    # wiki
    p_wiki = subparsers.add_parser("wiki", help="MewWiki vault management")
    p_wiki_sub = p_wiki.add_subparsers(dest="wiki_action")
    p_wiki_init = p_wiki_sub.add_parser("init", help="Bootstrap a new mewwiki vault")
    p_wiki_init.add_argument("--path", type=Path, help="Vault path (default: workspace/../mewwiki)")
    p_wiki_sync = p_wiki_sub.add_parser("sync", help="Sync silo content to mewwiki")
    p_wiki_sync.add_argument("--wiki", type=Path, dest="wiki_path", help="Vault path override")
    p_wiki_sync.add_argument("--dry-run", action="store_true", dest="dry_run",
                             help="Show what would sync without writing")

    # memory
    p_memory = subparsers.add_parser("memory", help="Cross-session context store")
    p_memory_sub = p_memory.add_subparsers(dest="memory_action")
    p_mem_sync = p_memory_sub.add_parser("sync", help="Index workspace content into memory")
    p_mem_sync.add_argument("--silo", metavar="NAME", help="Limit to one silo")
    p_mem_search = p_memory_sub.add_parser("search", help="Full-text search memory")
    p_mem_search.add_argument("query", help="Search query")
    p_mem_search.add_argument("--silo", metavar="NAME", help="Limit to one silo")
    p_mem_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    p_mem_recall = p_memory_sub.add_parser("recall", help="Recent context for a silo")
    p_mem_recall.add_argument("--silo", metavar="NAME", help="Silo name")
    p_mem_recall.add_argument("--days", type=int, default=14, help="How many days back (default: 14)")
    p_mem_recall.add_argument("--limit", type=int, default=5, help="Max entries (default: 5)")
    p_mem_purge = p_memory_sub.add_parser("purge", help="Remove stale entries")
    p_mem_purge.add_argument("--before", metavar="DATE", help="ISO 8601 date cutoff")
    p_mem_purge.add_argument("--days", type=int, default=90, help="Delete entries older than N days (default: 90)")

    # usage
    p_usage = subparsers.add_parser("usage", help="Show Claude auth status and usage dashboard link")
    p_usage.add_argument("--open", action="store_true", help="Open claude.ai/settings in browser")
    p_usage.add_argument("--report", action="store_true", help="Per-day token report from Claude Code transcripts")
    p_usage.add_argument("--days", type=int, default=7, help="Report window in days (default 7)")

    # check
    subparsers.add_parser("check", help="Sanity-check the MewVault installation")

    # design
    p_design = subparsers.add_parser("design", help="Design-silo utilities")
    p_design_sub = p_design.add_subparsers(dest="design_action")
    p_tokens = p_design_sub.add_parser("tokens", help="Diff Figma variables against DESIGN.md")
    p_tokens.add_argument("--diff", action="store_true", help="(default behavior)")
    p_tokens.add_argument("--project", metavar="NAME", help="Design project name (default: cwd)")

    # ci
    p_ci = subparsers.add_parser("ci", help="Install CI safety-net workflows into code projects")
    p_ci_sub = p_ci.add_subparsers(dest="ci_action")
    p_ci_install = p_ci_sub.add_parser("install", help="Copy ci.yml into projects missing it")
    p_ci_install.add_argument("--project", metavar="NAME", help="Single project only")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Generate and open the vault HTML dashboard")
    p_dash.add_argument("--watch", type=int, metavar="SECONDS", help="Regenerate every N seconds")
    p_dash.add_argument("--no-open", action="store_true", dest="no_open", help="Don't open in browser")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Automated health monitor (token safety, hooks, indexes)")
    p_doctor.add_argument("--quiet", action="store_true", help="Print only problems")
    p_doctor.add_argument("--json", action="store_true", help="Machine-readable output")
    p_doctor.add_argument("--notify", action="store_true", help="macOS notification on warn/fail")

    # dispatch
    p_dispatch = subparsers.add_parser("dispatch", help="Send pure-generation task to a proxy agent")
    p_dispatch.add_argument("--agent", default="mew-coder-simple",
                            choices=["mew-coder-simple", "mew-coder-reason"],
                            help="Target agent (default: mew-coder-simple = DeepSeek V3, mew-coder-reason = DeepSeek R1)")
    task_group = p_dispatch.add_mutually_exclusive_group(required=False)
    task_group.add_argument("--task", metavar="PROMPT", help="Inline prompt string")
    task_group.add_argument("--task-file", metavar="PATH", help="Path to file containing the prompt")
    task_group.add_argument("--check", action="store_true", help="Test proxy availability only (exit 0=up, 3=down)")
    p_dispatch.add_argument("--write", metavar="PATH", help="Write output directly to file instead of stdout")
    p_dispatch.add_argument("--system", metavar="TEXT", help="Override system prompt (default: agent-tuned code prompt)")
    p_dispatch.add_argument("--no-system", action="store_true", dest="no_system", help="Send no system prompt")

    # help
    p_help = subparsers.add_parser("help", help="Show help")
    p_help.add_argument("topic", nargs="?", help="Command, 'slash', or 'triggers'")

    args = parser.parse_args()

    if args.command is None or (hasattr(args, "help") and args.help):
        from mew.commands.help_cmd import run_help
        run_help(None)
        return

    dispatch = {
        "init":           lambda: _run("init", args),
        "status":         lambda: _run("status", args),
        "new":            lambda: _run("new", args),
        "validate":       lambda: _run("validate", args),
        "secret":         lambda: _run("secret", args),
        "dump":           lambda: _run("dump", args),
        "promote":        lambda: _run("promote", args),
        "abandon":        lambda: _run("abandon", args),
        "rename":         lambda: _run("rename", args),
        "rebuild-status": lambda: _run("rebuild-status", args),
        "archive":        lambda: _run("archive", args),
        "package":        lambda: _run("package", args),
        "process-inbox":  lambda: _run("process-inbox", args),
        "sync":           lambda: _run("sync", args),
        "harness":        lambda: _run("harness", args),
        "agent":          lambda: _run("agent", args),
        "instinct":       lambda: _run("instinct", args),
        "compact":        lambda: _run("compact", args),
        "wiki":           lambda: _run("wiki", args),
        "memory":         lambda: _run("memory", args),
        "usage":          lambda: _run("usage", args),
        "check":          lambda: _run("check", args),
        "doctor":         lambda: _run("doctor", args),
        "dashboard":      lambda: _run("dashboard", args),
        "ci":             lambda: _run("ci", args),
        "design":         lambda: _run("design", args),
        "dispatch":       lambda: _run("dispatch", args),
        "help":           lambda: _run("help", args),
    }

    handler = dispatch.get(args.command)
    if handler:
        handler()
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


def _run(command: str, args: argparse.Namespace) -> None:
    if command == "init":
        from mew.commands.init import run_init
        run_init(args)
    elif command == "status":
        from mew.commands.status import run_status
        run_status(args)
    elif command == "new":
        from mew.commands.new import run_new
        run_new(args)
    elif command == "validate":
        from mew.commands.validate import run_validate
        run_validate(args)
    elif command == "secret":
        from mew.commands.secret import run_secret
        run_secret(args)
    elif command == "dump":
        from mew.commands.dump import run_dump
        run_dump(args)
    elif command == "promote":
        from mew.commands.promote import run_promote
        run_promote(args)
    elif command == "abandon":
        from mew.commands.abandon import run_abandon
        run_abandon(args)
    elif command == "rename":
        from mew.commands.rename_cmd import run_rename
        run_rename(args)
    elif command == "rebuild-status":
        from mew.commands.rebuild_status import run_rebuild_status
        run_rebuild_status(args)
    elif command == "archive":
        from mew.commands.archive import run_archive
        run_archive(args)
    elif command == "package":
        from mew.commands.package import run_package
        run_package(args)
    elif command == "process-inbox":
        from mew.commands.process_inbox import run_process_inbox
        run_process_inbox(args)
    elif command == "sync":
        from mew.commands.sync import run_sync
        run_sync(args)
    elif command == "harness":
        from mew.commands.harness import run_harness
        run_harness(args)
    elif command == "agent":
        from mew.commands.agent import run_agent
        run_agent(args)
    elif command == "instinct":
        from mew.commands.instinct import run_instinct
        run_instinct(args)
    elif command == "compact":
        from mew.commands.compact import run_compact
        run_compact(args)
    elif command == "wiki":
        from mew.commands.wiki import run_wiki
        run_wiki(args)
    elif command == "memory":
        from mew.commands.memory import run_memory
        run_memory(args)
    elif command == "usage":
        from mew.commands.usage import run_usage
        run_usage(args)
    elif command == "check":
        from mew.commands.check import run_check
        run_check(args)
    elif command == "doctor":
        from mew.commands.doctor import run_doctor
        run_doctor(args)
    elif command == "dashboard":
        from mew.commands.dashboard import run_dashboard
        run_dashboard(args)
    elif command == "ci":
        from mew.commands.ci import run_ci
        run_ci(args)
    elif command == "design":
        from mew.commands.design import run_design
        run_design(args)
    elif command == "dispatch":
        from mew.commands.dispatch import run_dispatch
        run_dispatch(args)
    elif command == "help":
        from mew.commands.help_cmd import run_help
        run_help(getattr(args, "topic", None))
