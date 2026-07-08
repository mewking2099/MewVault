"""mew package — assemble a client deliverable package from a UX project."""
import sys
import shutil
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths, find_project_status_files
from mew.utils import parse_frontmatter, today_str

CLIENT_ARTIFACTS = [
    ("02_synthesis/insights.md", "insights.md"),
    ("04_ui/figma-snapshot.md", "figma-snapshot.md"),
    ("04_ui/design-decisions.md", "design-decisions.md"),
    ("05_handoff/specs.md", "specs.md"),
    ("05_handoff/dev-notes.md", "dev-notes.md"),
]

MANIFEST_TEMPLATE = """\
---
type: client-package
project: {project}
format: {fmt}
created: {date}
artifacts:
{artifact_lines}
---

# {project} — Client Package

Assembled {date}.

## Contents
{artifact_list}

## Notes

- Figma file key: {figma_key}
- To push to Google Drive: say "push this package to Drive" in Claude Code (Drive MCP required).
"""


def run_package(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    silos = get_silo_paths(workspace_root)
    project_name = args.project
    fmt = args.format or "client"

    # Find the UX project
    status_files = find_project_status_files(workspace_root)
    match = None
    for silo_key, status_path in status_files:
        if silo_key != "design":
            continue
        fm, _ = parse_frontmatter(status_path)
        if (
            str(fm.get("project", "")).lower() == project_name.lower()
            or status_path.parent.name.lower() == project_name.lower()
        ):
            match = (status_path, fm)
            break

    if not match:
        print(f"UX project not found: {project_name}")
        print("mew package works with design-studio projects only.")
        sys.exit(1)

    status_path, fm = match
    project_dir = status_path.parent
    figma_key = fm.get("figma_file_key") or "(not set)"

    # Create package folder next to the project
    package_name = f"{project_name}-{fmt}-package"
    package_dir = project_dir.parent / package_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()

    # Copy artifacts
    copied = []
    missing = []
    for src_rel, dst_name in CLIENT_ARTIFACTS:
        src = project_dir / src_rel
        if src.exists() and src.stat().st_size > 0:
            shutil.copy(src, package_dir / dst_name)
            copied.append(dst_name)
        else:
            missing.append(src_rel)

    # --design mode: full handoff — PRODUCT.md, DESIGN.md, audit scores, decision log
    if getattr(args, "design", False):
        for extra in ("PRODUCT.md", "DESIGN.md"):
            src = project_dir / extra
            if src.exists():
                shutil.copy(src, package_dir / extra)
                copied.append(extra)
            else:
                missing.append(extra)

        # Audit summary from Project_Status.md fields (written by the design-session gauntlet)
        audit_lines = ["# Quality audit\n"]
        for field in ("last_audit", "audit_scores", "open_p0"):
            val = fm.get(field)
            if val is not None:
                audit_lines.append(f"- {field.replace('_', ' ')}: {val}")
        if len(audit_lines) > 1:
            (package_dir / "audit-summary.md").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")
            copied.append("audit-summary.md")

        # Decision log from mewwiki, filtered by project slug
        decisions_dir = workspace_root / "mewwiki" / "Operations" / "Decisions"
        if decisions_dir.exists():
            slug = project_dir.name.lower()
            hits = [p for p in sorted(decisions_dir.glob("*.md"))
                    if slug in p.name.lower() or slug in p.read_text(encoding="utf-8", errors="ignore").lower()]
            if hits:
                out = ["# Decision log\n"]
                for p in hits:
                    out.append(f"\n---\n\n<!-- {p.name} -->\n\n" + p.read_text(encoding="utf-8", errors="ignore").strip())
                (package_dir / "decisions.md").write_text("\n".join(out) + "\n", encoding="utf-8")
                copied.append(f"decisions.md ({len(hits)} decision(s))")

        # Assets manifest (list, not copies — assets can be huge)
        assets_dir = project_dir / "assets"
        if assets_dir.exists():
            listing = [f"- {p.relative_to(assets_dir)} ({p.stat().st_size // 1024} KB)"
                       for p in sorted(assets_dir.rglob("*")) if p.is_file()]
            if listing:
                (package_dir / "assets-manifest.md").write_text(
                    "# Assets manifest\n\n" + "\n".join(listing) + "\n", encoding="utf-8")
                copied.append("assets-manifest.md")

    # Write manifest
    artifact_lines = "\n".join(f"  - {f}" for f in copied) or "  (none)"
    artifact_list = "\n".join(f"- {f}" for f in copied) or "(none copied)"
    manifest = MANIFEST_TEMPLATE.format(
        project=project_name,
        fmt=fmt,
        date=today_str(),
        artifact_lines=artifact_lines,
        artifact_list=artifact_list,
        figma_key=figma_key,
    )
    (package_dir / "MANIFEST.md").write_text(manifest, encoding="utf-8")

    print(f"\nPackage assembled: {package_name}/")
    print(f"  Copied: {len(copied)} artifact(s)")
    for f in copied:
        print(f"    ✓ {f}")
    if missing:
        print(f"  Missing (not yet created):")
        for f in missing:
            print(f"    – {f}")

    if args.push_drive:
        print()
        print("  --push-drive: say 'push this package to Drive' in Claude Code.")
        print(f"  Path: {package_dir}")
    else:
        print(f"\n  To push to Drive: mew package {project_name} --format client --push-drive")
    print()
