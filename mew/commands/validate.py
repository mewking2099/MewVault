"""mew validate — check schema compliance of all Project_Status.md files."""
import sys
from pathlib import Path
from typing import Optional
from mew.workspace import find_workspace_root, find_project_status_files
from mew.utils import parse_frontmatter

REQUIRED_FIELDS = ["project", "status", "next_action"]
VALID_STATUSES = {"active", "greenlit", "blocked", "archived", "abandoned"}
RECOMMENDED_FIELDS = ["last_session", "last_wrap", "started"]


def run_validate(args, workspace_root: Optional[Path] = None) -> None:
    if workspace_root is None:
        workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    status_files = find_project_status_files(workspace_root)

    if not status_files:
        print("  No Project_Status.md files found — workspace looks fresh.")
        return

    errors: list[str] = []
    warnings: list[str] = []

    for silo_key, status_path in status_files:
        fm, _ = parse_frontmatter(status_path)
        project_id = fm.get("project", status_path.parent.name)

        for field in REQUIRED_FIELDS:
            if field not in fm:
                errors.append(f"  [{project_id}] missing required field: '{field}'")

        status_val = fm.get("status")
        if status_val is not None and status_val not in VALID_STATUSES:
            errors.append(
                f"  [{project_id}] invalid status '{status_val}' — must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

        for field in RECOMMENDED_FIELDS:
            if field not in fm:
                warnings.append(f"  [{project_id}] missing recommended field: '{field}'")

    total = len(status_files)
    error_count = len(errors)
    warn_count = len(warnings)

    if not errors and not warnings:
        print(f"  All {total} project(s) valid. ✓")
        return

    if errors:
        print(f"  Errors ({error_count}):")
        for e in errors:
            print(e)

    if warnings:
        print(f"  Warnings ({warn_count}):")
        for w in warnings:
            print(w)

    print(f"\n  {total} project(s) checked. {error_count} error(s), {warn_count} warning(s).")

    if errors:
        sys.exit(1)
