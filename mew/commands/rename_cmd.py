"""mew rename — rename a project folder and update its Project_Status.md."""
import sys
import subprocess
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths, find_project_status_files
from mew.utils import parse_frontmatter, write_frontmatter, git_is_available


def run_rename(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    old_name = args.old_name
    new_name = args.new_name
    status_files = find_project_status_files(workspace_root)

    match = None
    for silo_key, status_path in status_files:
        fm, body = parse_frontmatter(status_path)
        if (
            str(fm.get("project", "")).lower() == old_name.lower()
            or status_path.parent.name.lower() == old_name.lower()
        ):
            match = (silo_key, status_path, fm, body)
            break

    if not match:
        print(f"Project not found: {old_name}")
        sys.exit(1)

    silo_key, status_path, fm, body = match
    project_dir = status_path.parent
    new_dir = project_dir.parent / new_name

    if new_dir.exists():
        print(f"Error: destination already exists: {new_dir}")
        sys.exit(1)

    # Move the folder (git mv if in a git repo, else plain rename)
    in_git = (project_dir.parent / ".git").exists()
    if in_git and git_is_available():
        result = subprocess.run(
            ["git", "-C", str(project_dir.parent), "mv", old_name, new_name],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"git mv failed: {result.stderr.strip()}")
            print("Falling back to plain rename.")
            project_dir.rename(new_dir)
        else:
            print(f"  git mv: {old_name} → {new_name}")
    else:
        project_dir.rename(new_dir)
        print(f"  Renamed: {old_name} → {new_name}")

    # Update Project_Status.md in the new location
    new_status_path = new_dir / "Project_Status.md"
    if new_status_path.exists():
        fm["project"] = new_name
        write_frontmatter(new_status_path, fm, body)
        print(f"  Updated project: field → {new_name}")

    print(f"\nRenamed {old_name} → {new_name}.")
    print()
