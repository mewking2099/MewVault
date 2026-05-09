"""mew dump — token-budgeted project context snapshot."""
import sys
from pathlib import Path
from mew.workspace import find_workspace_root, find_project_status_files
from mew.utils import parse_frontmatter


def run_dump(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    project_name = args.project
    budget = args.budget
    include = args.include or []

    # Find the project
    status_files = find_project_status_files(workspace_root)
    match = None
    for silo_key, status_path in status_files:
        fm, _ = parse_frontmatter(status_path)
        if (
            str(fm.get("project", "")).lower() == project_name.lower()
            or status_path.parent.name.lower() == project_name.lower()
        ):
            match = (silo_key, status_path, fm)
            break

    if not match:
        print(f"Project not found: {project_name}")
        sys.exit(1)

    silo_key, status_path, fm = match
    project_dir = status_path.parent
    output_parts: list[str] = []

    # 1. Project_Status.md (full)
    output_parts.append(f"# Project: {project_name}\n")
    output_parts.append(status_path.read_text(encoding="utf-8"))

    # 2. Last 3 decision records
    decisions_dir = project_dir / "decisions"
    if decisions_dir.exists():
        decision_files = sorted(decisions_dir.glob("*.md"), reverse=True)[:3]
        if decision_files:
            output_parts.append("\n---\n## Recent Decisions\n")
            for df in decision_files:
                output_parts.append(f"\n### {df.stem}\n")
                text = df.read_text(encoding="utf-8")
                output_parts.append(text[:500] + ("…" if len(text) > 500 else ""))

    # 3. Current phase (if UX project and requested)
    if "phase" in include:
        current_phase = fm.get("current_phase")
        if current_phase is not None:
            phase_dir = project_dir / f"0{current_phase}_*"
            for pd in project_dir.glob(f"0{current_phase}_*"):
                if pd.is_dir():
                    output_parts.append(f"\n---\n## Phase {current_phase}: {pd.name}\n")
                    for f in sorted(pd.glob("*.md"))[:5]:
                        text = f.read_text(encoding="utf-8")
                        output_parts.append(f"\n### {f.stem}\n{text[:200]}{'…' if len(text) > 200 else ''}\n")

    # 4. Open questions
    open_q = fm.get("open_questions", [])
    if open_q:
        output_parts.append("\n---\n## Open Questions\n")
        for q in open_q:
            output_parts.append(f"- {q}\n")

    # Assemble and truncate to budget
    output = "\n".join(output_parts)
    if len(output) > budget:
        output = output[:budget] + f"\n\n[Truncated to {budget} chars budget]"

    print(output)
