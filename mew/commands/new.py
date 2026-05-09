"""mew new — scaffold a new project from templates."""
import sys
import shutil
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths
from mew.utils import git_init, git_is_available, confirm, today_str

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def run_new(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    silos = get_silo_paths(workspace_root)
    name = args.name

    if args.type == "ux-project":
        _create_ux_project(silos["design"], name)
    elif args.type == "code-project":
        stack = args.stack or "next"
        _create_code_project(silos["software"], name, stack)
    elif args.type == "game-project":
        _create_game_project(silos["games"], name)
    elif args.type == "game-experiment":
        _create_game_experiment(silos["games"], name)
    elif args.type == "learning-path":
        _create_learning_path(silos["wiki"] / "learning", name)


def _scaffold(template_dir: Path, dest: Path, subs: dict) -> None:
    """Copy template_dir → dest, substituting {{key}} placeholders."""
    dest.mkdir(parents=True, exist_ok=True)
    if not template_dir.exists():
        return
    for src in template_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(template_dir)
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            continue
        text = src.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(f"{{{{{k}}}}}", v)
        dst.write_text(text, encoding="utf-8")


def _gitkeep(directory: Path) -> None:
    gk = directory / ".gitkeep"
    if not gk.exists():
        gk.touch()


def _create_ux_project(design_silo: Path, name: str) -> None:
    dest = design_silo / name
    if dest.exists():
        print(f"Error: already exists: {dest}")
        return

    subs = {"name": name, "date": today_str(), "project": name}
    _scaffold(TEMPLATES_DIR / "ux-project", dest, subs)

    for phase in ["00_discovery", "01_analysis", "02_synthesis", "03_audit", "04_ui", "05_handoff"]:
        phase_dir = dest / phase
        phase_dir.mkdir(exist_ok=True)
        _gitkeep(phase_dir)

    print(f"\nCreated UX project: design-studio/{name}/")
    print("  Edit Project_Status.md to set client and open_questions.")
    print()


def _create_code_project(software_silo: Path, name: str, stack: str) -> None:
    dest = software_silo / name
    if dest.exists():
        print(f"Error: already exists: {dest}")
        return

    template_dir = TEMPLATES_DIR / "code-project" / stack
    if not template_dir.exists():
        template_dir = TEMPLATES_DIR / "code-project"

    subs = {"name": name, "date": today_str(), "project": name, "stack": stack}
    _scaffold(template_dir, dest, subs)

    for d in ["proposals/active", "proposals/archive", "decisions", "docs/ux"]:
        sub = dest / d
        sub.mkdir(parents=True, exist_ok=True)
        _gitkeep(sub)

    # Each code project is its own git repo
    if git_is_available() and confirm(f"Initialize git repo for {name}?"):
        if git_init(dest):
            gi = dest / ".gitignore"
            if not gi.exists():
                gi.write_text(
                    "node_modules/\n.next/\ndist/\n.env\n.env.local\n.DS_Store\nThumbs.db\n",
                    encoding="utf-8",
                )
            print(f"  git init: software-projects/{name}/")

    print(f"\nCreated code project ({stack}): software-projects/{name}/")
    print("  Run /plan <feature> to start building.")
    print()


def _create_game_project(game_silo: Path, name: str) -> None:
    dest = game_silo / name
    if dest.exists():
        print(f"Error: already exists: {dest}")
        return

    subs = {"name": name, "date": today_str(), "project": name}
    _scaffold(TEMPLATES_DIR / "game-project", dest, subs)

    print(f"\nCreated game project: game-lab/{name}/")
    print("  Open in Godot 4. Run /teach godot to enter learning mode.")
    print()


def _create_game_experiment(game_silo: Path, name: str) -> None:
    dest = game_silo / "_experiments" / name
    if dest.exists():
        print(f"Error: already exists: {dest}")
        return

    dest.mkdir(parents=True, exist_ok=True)
    today = today_str()
    (dest / "Project_Status.md").write_text(
        f"---\nproject: {name}\nstatus: active\nstarted: {today}\ntype: game-experiment\n"
        f"next_action: \"\"\nlast_session: {today}\nlast_wrap: {today}\n---\n\n"
        f"# {name}\n\nThrowaway experiment.\n\n"
        f"To promote: `mew promote game-lab/_experiments/{name} --to game-project --name <new-name>`\n",
        encoding="utf-8",
    )

    print(f"\nCreated game experiment: game-lab/_experiments/{name}/")
    print(f"  Promote when ready: mew promote game-lab/_experiments/{name} --to game-project --name <name>")
    print()


def _create_learning_path(learning_dir: Path, topic: str) -> None:
    dest = learning_dir / topic
    if dest.exists():
        print(f"Error: already exists: {dest}")
        return

    subs = {"topic": topic, "date": today_str()}
    _scaffold(TEMPLATES_DIR / "learning-path", dest, subs)

    sessions_dir = dest / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    _gitkeep(sessions_dir)

    print(f"\nCreated learning path: wiki/learning/{topic}/")
    print(f"  Run /teach {topic} to start.")
    print()
