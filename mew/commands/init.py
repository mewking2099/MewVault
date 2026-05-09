"""mew init — bootstrap the workspace."""
import sys
import shutil
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths
from mew.utils import git_init, git_is_available, confirm, secure_file, today_str

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

SILOS = [
    {
        "key": "wiki",
        "dir": "wiki",
        "subdirs": [
            "_inbox",
            "_inbox/originals",
            "concepts",
            "projects",
            "learning",
            "decisions",
            "references",
            "daily",
        ],
        "claude_template": "wiki-CLAUDE.md",
        "gitignore": ".DS_Store\nThumbs.db\n*.tmp\n",
        "git": True,
    },
    {
        "key": "design",
        "dir": "design-studio",
        "subdirs": ["_templates"],
        "claude_template": "design-CLAUDE.md",
        "gitignore": ".DS_Store\nThumbs.db\n*.tmp\n",
        "git": True,
    },
    {
        "key": "software",
        "dir": "software-projects",
        "subdirs": [],
        "claude_template": "software-CLAUDE.md",
        "gitignore": None,
        "git": False,
    },
    {
        "key": "games",
        "dir": "game-lab",
        "subdirs": ["_experiments"],
        "claude_template": "games-CLAUDE.md",
        "gitignore": ".DS_Store\nThumbs.db\n*.tmp\n.godot/\nexport/\n",
        "git": True,
    },
]


def run_init(args) -> None:
    # Resolve workspace root
    if args.path:
        workspace_root = args.path.resolve()
    else:
        mewvault_dir = Path(__file__).parent.parent.parent.resolve()
        workspace_root = mewvault_dir.parent

    print(f"\nMewVault Init")
    print(f"Workspace root: {workspace_root}\n")

    if sys.version_info < (3, 11):
        print(f"Error: Python 3.11+ required.", file=sys.stderr)
        sys.exit(1)

    # Warn about existing silos
    silos = get_silo_paths(workspace_root)
    existing = [s["dir"] for s in SILOS if (workspace_root / s["dir"]).exists()]
    if existing:
        print(f"Warning: these silos already exist: {', '.join(existing)}")
        if not confirm("Continue? Existing files will not be overwritten."):
            print("Aborted.")
            return
        print()

    workspace_root.mkdir(parents=True, exist_ok=True)

    # Root CLAUDE.md
    _write_from_template(TEMPLATES_DIR / "root-CLAUDE.md", workspace_root / "CLAUDE.md")

    # Each silo
    for silo in SILOS:
        silo_path = workspace_root / silo["dir"]
        silo_path.mkdir(parents=True, exist_ok=True)

        for subdir in silo["subdirs"]:
            sub = silo_path / subdir
            sub.mkdir(parents=True, exist_ok=True)
            _touch_gitkeep(sub)

        _write_from_template(TEMPLATES_DIR / silo["claude_template"], silo_path / "CLAUDE.md")

        if silo["gitignore"] and not (silo_path / ".gitignore").exists():
            (silo_path / ".gitignore").write_text(silo["gitignore"], encoding="utf-8")

        print(f"  Created: {silo['dir']}/")

    # secrets/ inside mewvault
    mewvault_dir = Path(__file__).parent.parent.parent.resolve()
    secrets_dir = mewvault_dir / "secrets"
    secrets_dir.mkdir(exist_ok=True)

    secrets_gitignore = secrets_dir / ".gitignore"
    if not secrets_gitignore.exists():
        secrets_gitignore.write_text("*.env\n", encoding="utf-8")
    _touch_gitkeep(secrets_dir)

    try:
        secure_file(secrets_dir)
    except Exception:
        pass

    print(f"  Created: mewvault/secrets/ (gitignored, restricted permissions)")

    # Git init
    if not args.no_git and git_is_available():
        print()
        if confirm("Initialize git repos for wiki, design-studio, and game-lab?"):
            for silo in SILOS:
                if not silo["git"]:
                    continue
                silo_path = workspace_root / silo["dir"]
                if git_init(silo_path):
                    print(f"  git init: {silo['dir']}/")
                else:
                    print(f"  git init failed: {silo['dir']}/")

    # Install MewHarness hooks and rules (replaces legacy slash commands)
    _install_mewharness(workspace_root)

    # Validate
    print("\nValidating...")
    import argparse as _ap
    validate_args = _ap.Namespace(fix=False)
    from mew.commands.validate import run_validate
    run_validate(validate_args, workspace_root=workspace_root)

    print("\nWorkspace ready.\n")
    print("Next steps:")
    print("  1. Open wiki/ in Obsidian as a vault")
    print("  2. Open workspace root in Claude Code — /start is ready")
    print("  3. Run: python mew.py new ux-project <name>")
    print()


def _install_mewharness(workspace_root: Path) -> None:
    import argparse as _ap
    from mew.commands.harness import run_harness
    harness_args = _ap.Namespace(action="install", path=workspace_root)
    run_harness(harness_args)


def _write_from_template(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    if src.exists():
        shutil.copy(src, dst)


def _touch_gitkeep(directory: Path) -> None:
    gk = directory / ".gitkeep"
    if not gk.exists():
        gk.touch()
