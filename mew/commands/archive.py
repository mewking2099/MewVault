"""mew archive — move a project to _archive/ with per-silo behavior."""
import sys
import shutil
import subprocess
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths, find_project_status_files
from mew.utils import parse_frontmatter, write_frontmatter, today_str, confirm, git_is_available, secure_file


def run_archive(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    silos = get_silo_paths(workspace_root)
    target = args.target  # e.g. "sample-brand" or "wiki/learning/rust"

    # Handle wiki/learning/<topic> separately
    if target.startswith("wiki/learning/") or target.startswith("wiki\\learning\\"):
        _archive_learning_path(silos["wiki"], target.split("/")[-1].split("\\")[-1])
        return

    # Find among tracked projects
    status_files = find_project_status_files(workspace_root)
    match = None
    for silo_key, status_path in status_files:
        fm, body = parse_frontmatter(status_path)
        if (
            str(fm.get("project", "")).lower() == target.lower()
            or status_path.parent.name.lower() == target.lower()
        ):
            match = (silo_key, status_path, fm, body)
            break

    if not match:
        print(f"Project not found: {target}")
        print("For learning paths: mew archive wiki/learning/<topic>")
        sys.exit(1)

    silo_key, status_path, fm, body = match
    project_dir = status_path.parent

    silo_paths = {
        "design": silos["design"],
        "software": silos["software"],
        "games": silos["games"],
    }
    silo_root = silo_paths.get(silo_key, project_dir.parent)
    archive_dir = silo_root / "_archive" / project_dir.name
    archive_dir.parent.mkdir(parents=True, exist_ok=True)

    if archive_dir.exists():
        print(f"Error: archive destination already exists: {archive_dir}")
        sys.exit(1)

    print(f"\nArchiving {target} → {archive_dir.relative_to(workspace_root)}")
    if not confirm("Proceed?"):
        print("Aborted.")
        return

    # Update status before moving
    fm["status"] = "archived"
    fm["archived_date"] = today_str()
    write_frontmatter(status_path, fm, body)

    # Move the folder (git mv if in a git repo)
    in_git = (silo_root / ".git").exists()
    if in_git and git_is_available():
        result = subprocess.run(
            ["git", "-C", str(silo_root), "mv",
             str(project_dir.relative_to(silo_root)),
             str(archive_dir.relative_to(silo_root))],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  git mv: {project_dir.name} → _archive/{project_dir.name}")
        else:
            print(f"  git mv failed ({result.stderr.strip()}) — using plain move.")
            shutil.move(str(project_dir), str(archive_dir))
    else:
        shutil.move(str(project_dir), str(archive_dir))
        print(f"  Moved to _archive/{project_dir.name}")

    print(f"\nArchived. Files preserved at {archive_dir}")
    print()


def _archive_learning_path(wiki_silo: Path, topic: str) -> None:
    learning_path = wiki_silo / "learning" / topic
    if not learning_path.exists():
        print(f"Learning path not found: wiki/learning/{topic}")
        sys.exit(1)

    archive_dir = wiki_silo / "learning" / "_archive" / topic
    archive_dir.parent.mkdir(parents=True, exist_ok=True)

    if archive_dir.exists():
        print(f"Error: already archived: {archive_dir}")
        sys.exit(1)

    print(f"\nArchiving learning path: wiki/learning/{topic}")
    if not confirm("Set registry to read-only and move to _archive?"):
        print("Aborted.")
        return

    # Move the folder
    shutil.move(str(learning_path), str(archive_dir))

    # Make registry read-only
    registry = archive_dir / "concepts-learned.md"
    if registry.exists():
        try:
            secure_file(registry)
            print(f"  Registry set to read-only.")
        except Exception:
            pass

    print(f"  Moved to wiki/learning/_archive/{topic}")
    print()
