"""mew compact — generate a semantic context map for pre-compaction snapshots."""
import sys
from pathlib import Path
from mew.workspace import find_workspace_root
from mew.utils import today_str

MEWVAULT_DIR = Path(__file__).parent.parent.parent.resolve()


def run_compact(args) -> None:
    semantic = getattr(args, "semantic", False)
    budget = getattr(args, "budget", 4000)
    project_filter = getattr(args, "project", None)

    workspace_root = find_workspace_root(MEWVAULT_DIR.parent)
    sections = []

    # Active projects summary
    for silo_dir in ["software-projects", "design-studio", "game-lab"]:
        silo_path = workspace_root / silo_dir
        if not silo_path.exists():
            continue
        for proj_dir in sorted(silo_path.iterdir()):
            if not proj_dir.is_dir() or proj_dir.name.startswith("_"):
                continue
            if project_filter and proj_dir.name != project_filter:
                continue
            status_file = proj_dir / "Project_Status.md"
            if not status_file.exists():
                continue
            lines = status_file.read_text(encoding="utf-8").split("\n")
            excerpt = "\n".join(lines[:15])
            sections.append(f"### {silo_dir}/{proj_dir.name}\n\n```yaml\n{excerpt}\n```")

    # Wiki inbox count
    inbox = workspace_root / "wiki" / "_inbox"
    if inbox.exists():
        inbox_count = sum(1 for f in inbox.iterdir() if f.is_file() and f.suffix == ".md")
        if inbox_count:
            sections.append(f"### Wiki inbox\n\n{inbox_count} items pending.")

    # Recent log entries (last 5) per active project
    if semantic:
        for silo_dir in ["software-projects", "design-studio", "game-lab"]:
            silo_path = workspace_root / silo_dir
            if not silo_path.exists():
                continue
            for proj_dir in sorted(silo_path.iterdir()):
                if not proj_dir.is_dir() or proj_dir.name.startswith("_"):
                    continue
                if project_filter and proj_dir.name != project_filter:
                    continue
                log_file = proj_dir / "log.md"
                if not log_file.exists():
                    continue
                log_lines = [l for l in log_file.read_text(encoding="utf-8").split("\n")
                             if l.strip().startswith("-")]
                recent = log_lines[:5]
                if recent:
                    sections.append(f"### Recent log: {proj_dir.name}\n\n" + "\n".join(recent))

    output = f"# Semantic Compact — {today_str()}\n\n" + "\n\n".join(sections)

    # Enforce budget (chars = tokens * 4 approximately)
    max_chars = budget * 4
    if len(output) > max_chars:
        output = output[:max_chars] + "\n\n[... truncated to budget]"

    sys.stdout.write(output + "\n")
