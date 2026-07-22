"""mew lock / mew unlock — project focus guard.

Usage:
  mew lock <project-path>   Lock Claude to a single project directory.
  mew lock --status         Show what is currently locked.
  mew unlock                Remove the lock.
"""
import sys
from pathlib import Path
from mew.workspace import find_workspace_root


LOCK_FILENAME = ".active-project"


def _lock_file(workspace_root: Path) -> Path:
    return workspace_root / "mewvault" / LOCK_FILENAME


def run_lock(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    lock_file = _lock_file(workspace_root)

    if getattr(args, "status", False):
        if lock_file.exists():
            locked = lock_file.read_text(encoding="utf-8").strip()
            print(f"Locked to: {locked}")
        else:
            print("No project lock active. All silos are accessible.")
        return

    if not getattr(args, "project", None):
        if lock_file.exists():
            locked = lock_file.read_text(encoding="utf-8").strip()
            print(f"Locked to: {locked}")
        else:
            print("No project lock active.")
        return

    target = Path(args.project).resolve()
    if not target.exists():
        print(f"Error: path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    lock_file.write_text(str(target), encoding="utf-8")
    print(f"Locked to: {target}")
    print("Claude will block writes outside this directory.")
    print("Run 'mew unlock' to release.")


def run_unlock(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    lock_file = _lock_file(workspace_root)
    if lock_file.exists():
        locked = lock_file.read_text(encoding="utf-8").strip()
        lock_file.unlink()
        print(f"Unlocked. (was: {locked})")
        print("All silos are now accessible.")
    else:
        print("No project lock was active.")
