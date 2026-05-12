"""mew sync — git status across all silo repos, with optional interactive commit."""
import re
import sys
import shutil
import subprocess
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths
from mew.utils import confirm


def run_sync(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "pr", False):
        _create_pr(workspace_root)
        return

    silos = get_silo_paths(workspace_root)
    repos = _find_git_repos(workspace_root, silos)

    if not repos:
        print("No git repos found in workspace silos.")
        return

    if not args.commit:
        _show_status(repos)
        return

    _interactive_commit(repos, args.commit, push=args.push)


def _create_pr(workspace_root: Path) -> None:
    if not shutil.which("gh"):
        print("Error: 'gh' (GitHub CLI) not found. Install from https://cli.github.com/", file=sys.stderr)
        sys.exit(1)

    msg_file = workspace_root / ".claude" / "last-session-message.txt"
    body = msg_file.read_text(encoding="utf-8").strip() if msg_file.exists() else ""

    branch_result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    branch = branch_result.stdout.strip()
    if not branch:
        print("Error: could not determine current branch.", file=sys.stderr)
        sys.exit(1)

    if branch in ("main", "master"):
        print(f"Error: on branch '{branch}' — create a feature branch first.", file=sys.stderr)
        sys.exit(1)

    issue_nums = re.findall(r"#(\d+)", body)
    if issue_nums:
        closes = "\n\n" + "\n".join(f"Closes #{n}" for n in issue_nums)
        body = body + closes

    title = branch.replace("-", " ").replace("_", " ").strip()

    print(f"\nCreating PR: {title}")
    print(f"Branch: {branch}")
    if issue_nums:
        print(f"Links issues: {', '.join('#' + n for n in issue_nums)}")
    print()

    result = subprocess.run(
        ["gh", "pr", "create", "--title", title, "--body", body or "Session wrap."],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        pr_url = result.stdout.strip()
        print(f"PR created: {pr_url}")
    else:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def _find_git_repos(workspace_root: Path, silos: dict) -> list[Path]:
    repos = []
    # Check each silo root
    for key, path in silos.items():
        if key == "mewvault":
            continue
        if path.is_dir() and (path / ".git").exists():
            repos.append(path)

    # Check code projects (each has its own git repo)
    software = silos.get("software")
    if software and software.exists():
        for child in sorted(software.iterdir()):
            if child.is_dir() and (child / ".git").exists():
                repos.append(child)

    # Also check mewvault itself
    mewvault_path = silos.get("mewvault")
    if mewvault_path and mewvault_path.is_dir() and (mewvault_path / ".git").exists():
        repos.append(mewvault_path)

    return repos


def _show_status(repos: list[Path]) -> None:
    print("\nGit status across all repos:\n")
    for repo in repos:
        result = subprocess.run(
            ["git", "-C", str(repo), "status", "--short"],
            capture_output=True, text=True,
        )
        label = repo.relative_to(repo.parent.parent) if repo.parent != repo.parent.parent else repo.name
        has_changes = result.stdout.strip()
        marker = "*" if has_changes else "ok"
        print(f"  {marker} {label}")
        if has_changes:
            for line in result.stdout.strip().splitlines():
                print(f"      {line}")
    print()


def _interactive_commit(repos: list[Path], message: str, push: bool) -> None:
    print(f"\nInteractive commit: \"{message}\"\n")
    committed = []

    for repo in repos:
        result = subprocess.run(
            ["git", "-C", str(repo), "status", "--short"],
            capture_output=True, text=True,
        )
        if not result.stdout.strip():
            continue

        label = repo.name
        print(f"  {label}:")
        print(result.stdout.rstrip())

        if not confirm(f"  Commit {label}?"):
            print(f"  Skipped.\n")
            continue

        subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True)
        result = subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", message],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  Committed. ok")
            committed.append(repo)
        else:
            print(f"  Commit failed: {result.stderr.strip()}")

        if push and repo in committed:
            push_result = subprocess.run(
                ["git", "-C", str(repo), "push"],
                capture_output=True, text=True,
            )
            if push_result.returncode == 0:
                print(f"  Pushed. ok")
            else:
                print(f"  Push failed: {push_result.stderr.strip()}")
        print()

    print(f"Done. {len(committed)} repo(s) committed.")
