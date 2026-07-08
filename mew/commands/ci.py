"""mew ci — install the CI safety-net workflow into code projects.

`mew ci install` copies templates/ci.yml.tmpl into every software-projects/*
that has a package.json and no existing workflow. Green CI = typecheck, lint,
tests, build all pass — readable without reading code.
"""
import shutil
import sys
from pathlib import Path

from mew.workspace import find_workspace_root

TEMPLATE = Path(__file__).parent.parent.parent / "templates" / "ci.yml.tmpl"


def run_ci(args) -> None:
    action = getattr(args, "ci_action", None) or "install"
    if action != "install":
        print("Usage: mew ci install [--project NAME]", file=sys.stderr)
        sys.exit(1)

    root = find_workspace_root()
    silo = root / "software-projects"
    only = getattr(args, "project", None)

    if not TEMPLATE.exists():
        print(f"Error: template missing: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    print("\nMewVault CI install\n")
    installed = skipped = 0
    for proj in sorted(p for p in silo.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        if only and proj.name != only:
            continue
        if not (proj / "package.json").exists():
            print(f"  skip (no package.json): {proj.name}")
            continue
        dest = proj / ".github" / "workflows" / "ci.yml"
        if dest.exists():
            print(f"  ok (exists): {proj.name}")
            skipped += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATE, dest)
        print(f"  installed: {proj.name}/.github/workflows/ci.yml")
        installed += 1

    print(f"\n  {installed} installed, {skipped} already present.")
    if installed:
        print("  Commit and push each project for the workflow to take effect.")
        print("  Then: green check on GitHub = verified; red = not done.\n")
    else:
        print()
