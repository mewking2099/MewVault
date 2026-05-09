"""mew process-inbox — list wiki/_inbox/ files and propose routing for each."""
import sys
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths

CATEGORY_HINTS: dict[str, str] = {
    ".pdf": "reference — run Docling first, move original to _inbox/originals/",
    ".md": "concept or project-note",
    ".txt": "concept or reference",
    ".html": "reference",
    ".htm": "reference",
    ".csv": "reference",
    ".json": "reference",
    ".epub": "reference — convert to markdown first",
    ".docx": "reference — extract text first",
}


def run_process_inbox(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    silos = get_silo_paths(workspace_root)
    inbox = silos["wiki"] / "_inbox"

    if not inbox.exists():
        print("wiki/_inbox/ does not exist. Run: mew init")
        sys.exit(1)

    files = [
        f for f in sorted(inbox.iterdir())
        if f.is_file()
        and f.name != ".gitkeep"
        and f.parent == inbox
    ]

    if not files:
        print("wiki/_inbox/ is empty. Nothing to process.")
        return

    print(f"\nwiki/_inbox/ — {len(files)} item(s) pending\n")
    for i, f in enumerate(files, 1):
        hint = CATEGORY_HINTS.get(f.suffix.lower(), "unknown — inspect before routing")
        size_kb = f.stat().st_size // 1024
        size_str = f"{size_kb}KB" if size_kb > 0 else f"{f.stat().st_size}B"
        print(f"  {i}. {f.name}  ({size_str})")
        print(f"     → {hint}")
        print()

    print("Confirm routing in Claude: \"process the inbox\"")
    print("PDFs: Docling extracts to markdown first; original moves to _inbox/originals/.")
    print()
