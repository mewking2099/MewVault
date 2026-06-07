"""mew status — project status across all silos."""
import sys
import urllib.request
from datetime import datetime, date
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths, find_project_status_files
from mew.utils import parse_frontmatter


def _proxy_status() -> str:
    try:
        with urllib.request.urlopen("http://localhost:4000/health", timeout=2):
            return "running (DeepSeek routing active)"
    except Exception:
        return "offline (Claude handles all tasks)"


def run_status(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    if args.project:
        _print_project_detail(workspace_root, args.project)
        return

    if args.domain:
        _print_silo_view(workspace_root, args.domain, stale_days=args.stale, blocked_only=args.blocked)
        return

    _print_vault_overview(workspace_root, stale_days=args.stale, blocked_only=args.blocked)


def _print_vault_overview(root: Path, stale_days=None, blocked_only=False) -> None:
    silos = get_silo_paths(root)
    status_files = find_project_status_files(root)

    now = datetime.now()
    day_str = now.strftime("%a %b %d").lstrip("0").replace(" 0", " ")
    print(f"\nVault overview — {day_str}\n")

    # Group by silo key
    by_silo: dict[str, list[dict]] = {k: [] for k in ["wiki", "design", "software", "games"]}
    for silo_key, status_path in status_files:
        fm, _ = parse_frontmatter(status_path)
        if silo_key in by_silo:
            by_silo[silo_key].append(fm)

    # Wiki inbox count
    inbox_count = 0
    wiki_inbox = silos["wiki"] / "_inbox"
    if wiki_inbox.exists():
        inbox_count = sum(1 for f in wiki_inbox.iterdir() if f.is_file() and not f.name.startswith("."))

    # Learning track count
    learning_dir = silos["wiki"] / "learning"
    learning_count = 0
    if learning_dir.exists():
        learning_count = sum(
            1 for d in learning_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        )

    def silo_line(key: str, label: str) -> str:
        projects = by_silo.get(key, [])
        if not projects:
            return f"  {label:<10} • 0 projects"
        counts = {}
        for p in projects:
            s = p.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        parts = []
        for s in ("active", "greenlit", "blocked"):
            if counts.get(s):
                parts.append(f"{counts[s]} {s}")
        summary = ", ".join(parts) or "0 active"
        # Stale flag
        if stale_days:
            stale = _count_stale(projects, stale_days, now)
            if stale:
                summary += f" ({stale} stale)"
        return f"  {label:<10} • {summary}"

    # Unwrapped session detection
    unwrapped = []
    for _, status_path in status_files:
        fm, _ = parse_frontmatter(status_path)
        last_session = str(fm.get("last_session") or "")
        last_wrap = str(fm.get("last_wrap") or "")
        if last_session and last_wrap and last_session > last_wrap:
            unwrapped.append(fm.get("project", status_path.parent.name))

    if unwrapped:
        print(f"  ⚠ Unwrapped: {', '.join(unwrapped)}")

    print(f"  {'wiki':<10} • {inbox_count} inbox item{'s' if inbox_count != 1 else ''} pending")
    print(silo_line("design", "design"))
    print(silo_line("software", "software"))
    print(silo_line("games", "games"))
    print(f"  {'learning':<10} • {learning_count} track{'s' if learning_count != 1 else ''} active")
    print(f"  {'proxy':<10} • {_proxy_status()}")
    print()
    print("Drill in: name a silo. Or /wrap to leave.")
    print()


def _print_silo_view(root: Path, domain: str, stale_days=None, blocked_only=False) -> None:
    silo_alias = {
        "wiki": "wiki", "design": "design", "design-studio": "design",
        "software": "software", "software-projects": "software",
        "games": "games", "game-lab": "games",
    }
    silo_key = silo_alias.get(domain.lower())
    if not silo_key:
        print(f"Unknown silo: {domain}. Try: wiki, design, software, games")
        return

    silos = get_silo_paths(root)
    silo_path = {"wiki": silos["wiki"], "design": silos["design"],
                 "software": silos["software"], "games": silos["games"]}[silo_key]

    silo_label = {"wiki": "wiki", "design": "design-studio",
                  "software": "software-projects", "games": "game-lab"}[silo_key]

    print(f"\n{silo_label}:\n")

    if not silo_path.exists():
        print("  Silo not initialized. Run: mew init")
        return

    now = datetime.now()
    found = False

    for status_file in sorted(silo_path.rglob("Project_Status.md")):
        fm, _ = parse_frontmatter(status_file)
        status = fm.get("status", "unknown")

        if blocked_only and status != "blocked":
            continue

        project = fm.get("project", status_file.parent.name)
        phase = fm.get("current_phase", "")
        phase_status = fm.get("phase_status", "")
        last_session = fm.get("last_session")

        age_str = _age_str(last_session, now)

        if stale_days and not _is_stale(last_session, stale_days, now):
            continue

        phase_str = f"phase {phase} {phase_status}".strip() if phase != "" else ""
        print(f"  {str(project):<22} {phase_str:<28} {status:<14} {age_str}")
        found = True

    if not found:
        print("  No projects." + (" Try without --blocked or --stale." if blocked_only or stale_days else ""))

    print()
    print('Drill in: name a project. Or "back" for vault.')
    print()


def _print_project_detail(root: Path, project_name: str) -> None:
    for silo_key, status_path in find_project_status_files(root):
        fm, body = parse_frontmatter(status_path)
        if (
            str(fm.get("project", "")).lower() == project_name.lower()
            or status_path.parent.name.lower() == project_name.lower()
        ):
            print(f"\n{project_name}:\n")
            for k, v in fm.items():
                print(f"  {k}: {v}")
            if fm.get("open_questions"):
                print("\n  Open questions:")
                for q in fm["open_questions"]:
                    print(f"    - {q}")
            return

    print(f"Project not found: {project_name}")


def _age_str(last_session, now: datetime) -> str:
    if not last_session:
        return ""
    try:
        if isinstance(last_session, date) and not isinstance(last_session, datetime):
            last_dt = datetime(last_session.year, last_session.month, last_session.day)
        elif isinstance(last_session, datetime):
            last_dt = last_session
        else:
            last_dt = datetime.fromisoformat(str(last_session))
        days = (now - last_dt).days
        if days == 0:
            return "today"
        return f"{days}d ago"
    except (ValueError, TypeError):
        return str(last_session)


def _is_stale(last_session, stale_days: int, now: datetime) -> bool:
    age = _age_str(last_session, now)
    if not age or age == "today":
        return False
    try:
        return int(age.replace("d ago", "")) >= stale_days
    except ValueError:
        return False


def _count_stale(projects: list[dict], stale_days: int, now: datetime) -> int:
    return sum(1 for p in projects if _is_stale(p.get("last_session"), stale_days, now))
