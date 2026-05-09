"""Workspace root detection and silo path helpers."""
from pathlib import Path
from typing import Optional

SILO_DIR_NAMES = {
    "wiki": "wiki",
    "design": "design-studio",
    "software": "software-projects",
    "games": "game-lab",
}


def find_workspace_root(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from start (or CWD) to find the workspace root.

    The workspace root is the directory that contains a mewvault/ child
    which itself contains mew.py.
    """
    current = (start or Path.cwd()).resolve()

    for candidate in [current, *current.parents]:
        # We might be inside mewvault/ already
        if candidate.name == "mewvault" and (candidate / "mew.py").exists():
            return candidate.parent
        # Or the workspace root contains mewvault/
        mewvault_child = candidate / "mewvault"
        if mewvault_child.is_dir() and (mewvault_child / "mew.py").exists():
            return candidate

    return None


def get_silo_paths(root: Path) -> dict[str, Path]:
    return {
        "wiki": root / "wiki",
        "design": root / "design-studio",
        "software": root / "software-projects",
        "games": root / "game-lab",
        "mewvault": root / "mewvault",
    }


def find_project_status_files(root: Path) -> list[tuple[str, Path]]:
    """Return [(silo_key, Path)] for every Project_Status.md across all silos."""
    results = []
    silos = get_silo_paths(root)
    for silo_key, silo_path in silos.items():
        if silo_key == "mewvault":
            continue
        if not silo_path.exists():
            continue
        for f in sorted(silo_path.rglob("Project_Status.md")):
            results.append((silo_key, f))
    return results
