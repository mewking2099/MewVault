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

    # process-inbox
    subparsers.add_parser("process-inbox", help="List wiki/_inbox/ and propose routing")

    # sync
    p_sync = subparsers.add_parser("sync", help="Git status across all repos")
    p_sync.add_argument("--commit", metavar="MSG", help="Interactively commit each repo")
    p_sync.add_argument("--push", action="store_true", help="Push after committing")

    # harness
    p_harness = subparsers.add_parser("harness", help="Manage the MewHarness hook runtime")
    p_harness.add_argument(
        "action",
        choices=["install", "status", "config", "disable", "proxy"],
        help="install: register hooks; status: show state; config: show env vars; disable: remove hooks; proxy: start LiteLLM proxy",
    )
    p_harness.add_argument("--path", type=Path, help="Workspace root override")
    p_harness.add_argument("key", nargs="?", help="Config key (for config action)")
    p_harness.add_argument("value", nargs="?", help="Config value (for config action)")

    # agent
    p_agent = subparsers.add_parser("agent", help="List or invoke specialist agents")
    p_agent_sub = p_agent.add_subparsers(dest="agent_action")
    p_agent_list = p_agent_sub.add_parser("list", help="List available agents")
    p_agent_invoke = p_agent_sub.add_parser("invoke", help="Invoke an agent by name")
    p_agent_invoke.add_argument("name", help="Agent name (e.g. mew-planner)")
    p_agent_invoke.add_argument("--task", metavar="TEXT", help="Task description to pass")

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
    elif command == "help":
        from mew.commands.help_cmd import run_help
        run_help(getattr(args, "topic", None))
