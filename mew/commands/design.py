"""mew design — design-silo utilities.

`mew design tokens --diff [--project NAME]`
Compare Figma variables against the project's DESIGN.md and flag drift
("Figma changed, code didn't" — the silent handoff killer).

The Figma MCP is callable by Claude in-session, not by this CLI, so the flow
is two-step:
  1. No snapshot yet → this command prints the exact instruction for Claude
     to fetch `get_variable_defs` and save `assets/figma-variables.json`.
  2. Snapshot exists → diff it against DESIGN.md and print a drift table.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from mew.workspace import find_workspace_root

SNAPSHOT_REL = Path("assets") / "figma-variables.json"


def run_design(args) -> None:
    action = getattr(args, "design_action", None)
    if action == "tokens":
        _tokens(args)
    else:
        print("Usage: mew design tokens --diff [--project NAME]", file=sys.stderr)
        sys.exit(1)


def _find_project(root: Path, name: str | None) -> Path | None:
    silo = root / "design-studio"
    if name:
        p = silo / name
        return p if (p / "Project_Status.md").exists() else None
    # cwd-based detection
    cwd = Path.cwd().resolve()
    d = cwd
    while d != d.parent:
        if (d / "Project_Status.md").exists() and "design-studio" in str(d):
            return d
        d = d.parent
    return None


def _flatten_variables(data, prefix="") -> dict:
    """Flatten a nested variables JSON into {token_name: value_string}."""
    flat = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}/{k}" if prefix else str(k)
            if isinstance(v, (dict, list)):
                flat.update(_flatten_variables(v, key))
            else:
                flat[key] = str(v)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "name" in item:
                flat[str(item["name"])] = str(item.get("value", item.get("resolvedValue", "")))
            else:
                flat.update(_flatten_variables(item, prefix))
    return flat


def _tokens(args) -> None:
    root = find_workspace_root()
    project = _find_project(root, getattr(args, "project", None))
    if not project:
        print("Error: design project not found. Use --project NAME or run inside design-studio/<project>/.",
              file=sys.stderr)
        sys.exit(1)

    status_text = (project / "Project_Status.md").read_text(encoding="utf-8")
    key_match = re.search(r"^figma_file_key\s*:\s*(\S+)", status_text, re.M)
    figma_key = key_match.group(1) if key_match else None
    if figma_key and figma_key.lower() in ("null", "none", "~", '""', "''"):
        figma_key = None

    snapshot = project / SNAPSHOT_REL
    design_md = project / "DESIGN.md"

    print(f"\nToken drift — {project.name}\n")

    if not snapshot.exists():
        print("  No Figma variables snapshot yet. In a Claude Code session, say:")
        print()
        print(f'    "Fetch variables for the Figma file{f" {figma_key}" if figma_key else ""} via the Figma MCP')
        print(f'     (get_variable_defs) and save the JSON response to {project.name}/{SNAPSHOT_REL}"')
        print()
        print("  Then re-run: mew design tokens --diff")
        sys.exit(0)

    if not design_md.exists():
        print("  No DESIGN.md in the project root — run /impeccable init or /impeccable document first.")
        sys.exit(1)

    age_days = (datetime.now().timestamp() - snapshot.stat().st_mtime) / 86400
    if age_days > 14:
        print(f"  ⚠ Snapshot is {age_days:.0f} days old — consider re-fetching before trusting this diff.\n")

    try:
        figma_vars = _flatten_variables(json.loads(snapshot.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  Error reading snapshot: {e}", file=sys.stderr)
        sys.exit(1)

    design_text = design_md.read_text(encoding="utf-8")
    design_lower = design_text.lower()

    missing, mismatched, matched = [], [], 0
    for name, value in sorted(figma_vars.items()):
        short = name.split("/")[-1].strip().lower()
        if not short:
            continue
        if short not in design_lower:
            missing.append((name, value))
        elif value and value.lower() not in design_lower:
            mismatched.append((name, value))
        else:
            matched += 1

    print(f"  Figma variables: {len(figma_vars)} · matched in DESIGN.md: {matched} · "
          f"value drift: {len(mismatched)} · missing: {len(missing)}\n")

    if mismatched:
        print("  Value drift (token exists in DESIGN.md but Figma value not found):")
        for name, value in mismatched[:20]:
            print(f"    ~ {name} = {value}")
        print()
    if missing:
        print("  In Figma but not in DESIGN.md:")
        for name, value in missing[:20]:
            print(f"    + {name} = {value}")
        print()
    if not mismatched and not missing:
        print("  No drift detected. Figma and DESIGN.md agree.\n")
    else:
        print("  Fix: update DESIGN.md (or the tokens in code) and re-run. `/impeccable document`")
        print("  re-captures DESIGN.md from the implemented system.\n")
        sys.exit(1)
