"""mew rebuild-status — regenerate a missing or corrupted Project_Status.md."""
import sys
import shutil
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths
from mew.utils import today_str, confirm

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

SILO_TYPE_MAP = {
    "design": "ux-project",
    "software": "code-project",
    "games": "game-project",
}


def run_rebuild_status(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    silos = get_silo_paths(workspace_root)
    project_name = args.project

    # Locate the project folder
    project_dir, detected_type = _find_project(workspace_root, silos, project_name)
    if not project_dir:
        print(f"Project folder not found: {project_name}")
        print("Searched in: design-studio/, software-projects/, game-lab/")
        sys.exit(1)

    project_type = args.type or detected_type
    if not project_type:
        print(f"Could not detect project type for {project_name}.")
        print("Specify with: mew rebuild-status <name> --type ux-project|code-project|game-project")
        sys.exit(1)

    status_path = project_dir / "Project_Status.md"
    if status_path.exists():
        print(f"Project_Status.md already exists for {project_name}.")
        if not confirm("Overwrite?"):
            print("Aborted.")
            return

    template_path = TEMPLATES_DIR / project_type / "Project_Status.md"
    if not template_path.exists():
        print(f"Template not found: templates/{project_type}/Project_Status.md")
        sys.exit(1)

    # Read template and substitute
    text = template_path.read_text(encoding="utf-8")
    subs = {
        "name": project_name,
        "date": today_str(),
        "project": project_name,
        "stack": args.stack or "next",
    }
    for k, v in subs.items():
        text = text.replace(f"{{{{{k}}}}}", v)

    status_path.write_text(text, encoding="utf-8")
    print(f"\nRebuilt Project_Status.md for {project_name} ({project_type}).")
    print(f"  Edit {status_path} to fill in actual values.")
    print()


def _find_project(root: Path, silos: dict, name: str):
    for silo_key, silo_path in silos.items():
        if silo_key in ("mewvault", "wiki"):
            continue
        candidate = silo_path / name
        if candidate.is_dir():
            return candidate, SILO_TYPE_MAP.get(silo_key)
        # Search one level deep
        if silo_path.exists():
            for child in silo_path.iterdir():
                if child.is_dir() and child.name.lower() == name.lower():
                    return child, SILO_TYPE_MAP.get(silo_key)
    return None, None
