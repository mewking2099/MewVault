"""mew promote — promote projects across silos.

Supported flows:
  UX → Code:        mew promote <ux-name> --to <code-name> [--stack next]
  Wiki → UX:        mew promote wiki/ --topic <tag> --name <ux-name>
  Experiment → Game: mew promote game-lab/_experiments/<name> --name <new-name>
"""
import sys
import shutil
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths
from mew.utils import parse_frontmatter, write_frontmatter, today_str

UX_ARTIFACTS = [
    ("01_analysis/personas.md", "personas.md"),
    ("02_synthesis/insights.md", "insights.md"),
    ("04_ui/design-decisions.md", "design-decisions.md"),
    ("04_ui/figma-snapshot.md", "figma-snapshot.md"),
    ("05_handoff/specs.md", "specs.md"),
    ("05_handoff/dev-notes.md", "dev-notes.md"),
]


def run_promote(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    silos = get_silo_paths(workspace_root)
    source = args.source.replace("\\", "/")

    if source.startswith("wiki") or source == "wiki/":
        _promote_wiki_to_ux(args, workspace_root, silos)
    elif "_experiments" in source or "experiment" in source:
        _promote_experiment_to_game(args, workspace_root, silos)
    else:
        _promote_ux_to_code(args, workspace_root, silos)


# ---------------------------------------------------------------------------
# UX → Code
# ---------------------------------------------------------------------------

def _promote_ux_to_code(args, workspace_root, silos) -> None:
    source = args.source
    ux_name = source.split("/")[-1]
    ux_dir = silos["design"] / ux_name

    if not ux_dir.exists():
        print(f"Error: UX project not found: design-studio/{ux_name}")
        sys.exit(1)

    status_file = ux_dir / "Project_Status.md"
    if not status_file.exists():
        print(f"Error: Project_Status.md missing in design-studio/{ux_name}")
        sys.exit(1)

    fm, body = parse_frontmatter(status_file)
    greenlit = fm.get("greenlit", False)
    current_phase = int(fm.get("current_phase", 0))

    if not greenlit and current_phase < 5:
        print(f"Error: {ux_name} is not ready for promotion.")
        print(f"  current_phase: {current_phase} (need 5), greenlit: {greenlit}")
        print("  Set greenlit: true in Project_Status.md to override.")
        sys.exit(1)

    if not args.to:
        print("Error: --to <code-project-name> is required for UX→Code promotion.")
        sys.exit(1)

    code_name = args.to
    stack = args.stack or "next"
    code_dir = silos["software"] / code_name

    if code_dir.exists():
        print(f"Error: code project already exists: software-projects/{code_name}")
        sys.exit(1)

    print(f"\nPromoting {ux_name} → {code_name} ({stack})\n")

    from mew.commands.new import _create_code_project
    _create_code_project(silos["software"], code_name, stack)

    docs_ux = code_dir / "docs" / "ux"
    docs_ux.mkdir(parents=True, exist_ok=True)
    copied = []
    for src_rel, dst_name in UX_ARTIFACTS:
        src = ux_dir / src_rel
        if src.exists() and src.stat().st_size > 0:
            shutil.copy(src, docs_ux / dst_name)
            copied.append(dst_name)

    if copied:
        print(f"  Copied UX artifacts → docs/ux/: {', '.join(copied)}")
    else:
        print("  No UX artifacts to copy yet.")

    figma_key = fm.get("figma_file_key")
    _append_ux_section(code_dir / "CLAUDE.md", ux_name, figma_key, copied)

    promoted_to = fm.get("promoted_to") or []
    if isinstance(promoted_to, str):
        promoted_to = [promoted_to]
    if code_name not in promoted_to:
        promoted_to.append(code_name)
    fm["promoted_to"] = promoted_to
    write_frontmatter(status_file, fm, body)
    print(f"  Updated design-studio/{ux_name}/Project_Status.md (promoted_to)")

    print(f"\nDone. Next: /plan implement-design-system-foundations")
    print(f"  Code project: software-projects/{code_name}/")
    print()


# ---------------------------------------------------------------------------
# Wiki → UX
# ---------------------------------------------------------------------------

def _promote_wiki_to_ux(args, workspace_root, silos) -> None:
    topic = args.topic
    ux_name = args.name

    if not topic:
        print("Error: --topic <tag> is required for wiki→UX promotion.")
        sys.exit(1)
    if not ux_name:
        print("Error: --name <ux-project-name> is required for wiki→UX promotion.")
        sys.exit(1)

    wiki_silo = silos["wiki"]
    ux_dir = silos["design"] / ux_name

    if ux_dir.exists():
        print(f"Error: UX project already exists: design-studio/{ux_name}")
        sys.exit(1)

    # Find wiki notes matching the topic tag
    matching = _search_wiki_by_tag(wiki_silo, topic)
    if not matching:
        print(f"No wiki notes found with tag '{topic}'.")
        print(f"  Check wiki/concepts/ and wiki/projects/ for notes with tags: [{topic}]")
        sys.exit(1)

    print(f"\nPromoting wiki research on '{topic}' → UX project: {ux_name}")
    print(f"  Found {len(matching)} matching note(s):")
    for p in matching:
        print(f"    {p.relative_to(wiki_silo)}")
    print()

    # Scaffold the UX project
    from mew.commands.new import _create_ux_project
    _create_ux_project(silos["design"], ux_name)

    # Copy matched notes into 00_discovery/ as discovery inputs
    discovery_dir = ux_dir / "00_discovery"
    discovery_dir.mkdir(exist_ok=True)
    copied = []
    for src in matching:
        fm_note, body_note = parse_frontmatter(src)
        fm_note["promoted_from"] = str(src.relative_to(wiki_silo))
        fm_note["promoted_to"] = [ux_name]
        # Write a copy into discovery
        dst = discovery_dir / src.name
        write_frontmatter(dst, fm_note, body_note)
        # Update original note's promoted_to list
        orig_promoted = fm_note.get("promoted_to") or []
        if isinstance(orig_promoted, str):
            orig_promoted = [orig_promoted]
        if ux_name not in orig_promoted:
            orig_promoted.append(ux_name)
        fm_note["promoted_to"] = orig_promoted
        write_frontmatter(src, fm_note, body_note)
        copied.append(src.name)

    print(f"  Copied {len(copied)} note(s) → design-studio/{ux_name}/00_discovery/")
    print(f"\nNext: open {ux_name} in Claude Code and run /start design {ux_name}")
    print()


def _search_wiki_by_tag(wiki_silo: Path, topic: str) -> list[Path]:
    matches = []
    for md_file in wiki_silo.rglob("*.md"):
        if "_archive" in md_file.parts or "_inbox" in md_file.parts:
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        frontmatter = text.split("---")[1] if "---" in text else ""
        if f"- {topic}" in text or f"[{topic}]" in text or f" {topic}" in frontmatter:
            matches.append(md_file)
    return matches


# ---------------------------------------------------------------------------
# Experiment → Game project
# ---------------------------------------------------------------------------

def _promote_experiment_to_game(args, workspace_root, silos) -> None:
    source = args.source.replace("\\", "/")
    exp_name = source.split("/")[-1]
    new_name = args.name or args.to

    if not new_name:
        print("Error: --name <new-project-name> is required for experiment→game promotion.")
        sys.exit(1)

    exp_dir = silos["games"] / "_experiments" / exp_name
    if not exp_dir.exists():
        print(f"Error: experiment not found: game-lab/_experiments/{exp_name}")
        sys.exit(1)

    game_dir = silos["games"] / new_name
    if game_dir.exists():
        print(f"Error: game project already exists: game-lab/{new_name}")
        sys.exit(1)

    print(f"\nPromoting experiment {exp_name} → game project: {new_name}\n")

    from mew.commands.new import _create_game_project
    _create_game_project(silos["games"], new_name)

    # Seed registries from experiment session notes (any .md not named Project_Status.md)
    session_notes = [
        f for f in exp_dir.rglob("*.md")
        if f.name != "Project_Status.md"
    ]
    if session_notes:
        sessions_dir = game_dir / "sessions"
        sessions_dir.mkdir(exist_ok=True)
        for note in session_notes:
            shutil.copy(note, sessions_dir / note.name)
        print(f"  Seeded {len(session_notes)} session note(s) → game-lab/{new_name}/sessions/")

    # Mark experiment as promoted
    exp_status = exp_dir / "Project_Status.md"
    if exp_status.exists():
        fm, body = parse_frontmatter(exp_status)
        fm["status"] = "archived"
        fm["promoted_to"] = new_name
        write_frontmatter(exp_status, fm, body)

    print(f"  Experiment marked as promoted.")
    print(f"\nNext: open {new_name} in Godot 4. Run /teach godot to start learning mode.")
    print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append_ux_section(claude_md: Path, ux_name: str, figma_key, copied: list[str]) -> None:
    if not claude_md.exists():
        return
    existing = claude_md.read_text(encoding="utf-8")
    lines = ["\n## Promoted from UX", f"\nSource: design-studio/{ux_name}"]
    if figma_key:
        lines.append(f"Figma file key: `{figma_key}`")
        lines.append(f"Set token: `mew secret set FIGMA_TOKEN --scope {claude_md.parent.name}`")
        lines.append("")
        lines.append("Design tokens: if the Figma MCP is available, run `get_variable_defs` with")
        lines.append(f"the file key above and write the output to `tokens/design-tokens.css`.")
        lines.append("mew-designer handles this at Phase 4 — do not duplicate the work.")
    if copied:
        lines.append("\nUX artifacts in docs/ux/:")
        for f in copied:
            lines.append(f"  - {f}")
    lines.append("\nRead docs/ux/ before planning any UI feature.")
    claude_md.write_text(existing.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
