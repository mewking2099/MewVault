"""mew abandon — mark a project as abandoned."""
import sys
from mew.workspace import find_workspace_root, find_project_status_files
from mew.utils import parse_frontmatter, write_frontmatter, today_str


def run_abandon(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    project_name = args.project
    status_files = find_project_status_files(workspace_root)

    match = None
    for silo_key, status_path in status_files:
        fm, body = parse_frontmatter(status_path)
        if (
            str(fm.get("project", "")).lower() == project_name.lower()
            or status_path.parent.name.lower() == project_name.lower()
        ):
            match = (silo_key, status_path, fm, body)
            break

    if not match:
        print(f"Project not found: {project_name}")
        sys.exit(1)

    silo_key, status_path, fm, body = match
    current_status = fm.get("status", "unknown")

    if current_status == "abandoned":
        print(f"{project_name} is already marked abandoned.")
        return

    reason = args.reason
    if not reason:
        try:
            reason = input("Reason for abandoning (one line, or Enter to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return

    fm["status"] = "abandoned"
    fm["abandoned_date"] = today_str()
    if reason:
        fm["abandoned_reason"] = reason

    write_frontmatter(status_path, fm, body)
    print(f"\nMarked {project_name} as abandoned.")
    if reason:
        print(f"  Reason: {reason}")
    print(f"  Run 'mew archive {project_name}' to move it out of active.")
    print()
