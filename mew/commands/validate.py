"""mew validate — check schema compliance of all Project_Status.md files."""
import re
import sys
from pathlib import Path
from typing import Optional
from mew.workspace import find_workspace_root, find_project_status_files
from mew.utils import parse_frontmatter

REQUIRED_FIELDS = ["project", "status", "next_action"]
VALID_STATUSES = {"active", "greenlit", "blocked", "archived", "abandoned"}
RECOMMENDED_FIELDS = ["last_session", "last_wrap", "started"]

VERBOSE_PHRASES = [
    (r"you should be aware that ", ""),
    (r"it is important to note that ", ""),
    (r"please ensure that you ", ""),
    (r"please ensure that ", ""),
    (r"please make sure that you ", ""),
    (r"please make sure that ", ""),
    (r"it should be noted that ", ""),
    (r"in order to ", "to "),
    (r"due to the fact that ", "because "),
    (r"for the purpose of ", "for "),
    (r"at this point in time", "now"),
    (r"at the end of the day", "ultimately"),
    (r"in the event that ", "if "),
    (r"with regard to ", "regarding "),
    (r"in relation to ", "regarding "),
]
COMPILED_PHRASES = [(re.compile(p, re.IGNORECASE), r) for p, r in VERBOSE_PHRASES]

SILO_DIRS = ["wiki", "software-projects", "game-lab", "design-studio", "mewvault"]


def _find_claude_md_files(workspace_root: Path) -> list[Path]:
    results = []
    for p in workspace_root.rglob("CLAUDE.md"):
        parts = p.parts
        if any(skip in parts for skip in ["venv", "node_modules", ".git", "__pycache__"]):
            continue
        results.append(p)
    return sorted(results)


def _slim_suggest(line: str) -> Optional[str]:
    suggested = line
    for pattern, replacement in COMPILED_PHRASES:
        suggested = pattern.sub(replacement, suggested)
    suggested = re.sub(r"\s{2,}", " ", suggested).strip()
    return suggested if suggested != line.strip() else None


def run_slim(workspace_root: Path) -> None:
    files = _find_claude_md_files(workspace_root)
    if not files:
        print("  No CLAUDE.md files found.")
        return

    total_original_words = 0
    total_suggested_words = 0
    any_suggestions = False

    for claude_file in files:
        lines = claude_file.read_text(encoding="utf-8").splitlines()
        suggestions = []
        in_code_block = False

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
            if in_code_block or not stripped:
                continue

            words = stripped.split()
            if len(words) > 20:
                suggestion = _slim_suggest(stripped)
                if suggestion:
                    suggestions.append((lineno, stripped, suggestion))

        if suggestions:
            any_suggestions = True
            rel = claude_file.relative_to(workspace_root)
            print(f"\n--- {rel} ({len(suggestions)} suggestion{'s' if len(suggestions) != 1 else ''}) ---")
            for lineno, original, suggested in suggestions:
                orig_words = len(original.split())
                sug_words = len(suggested.split())
                total_original_words += orig_words
                total_suggested_words += sug_words
                print(f"\n  Line {lineno} [{orig_words} words → {sug_words} words]:")
                print(f"  - {original}")
                print(f"  + {suggested}")

    if not any_suggestions:
        print("  No verbose sentences found — CLAUDE.md files look tight.")
        return

    saved_words = total_original_words - total_suggested_words
    saved_tokens = round(saved_words * 0.75)
    print(f"\nEstimated savings: ~{saved_tokens} token{'s' if saved_tokens != 1 else ''} "
          f"({saved_words} words) across {len(files)} file(s).")
    print("Note: suggestions only — no files were changed.")


def run_validate(args, workspace_root: Optional[Path] = None) -> None:
    if workspace_root is None:
        workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "slim", False):
        run_slim(workspace_root)
        return

    status_files = find_project_status_files(workspace_root)

    if not status_files:
        print("  No Project_Status.md files found — workspace looks fresh.")
        return

    errors: list[str] = []
    warnings: list[str] = []

    for silo_key, status_path in status_files:
        fm, _ = parse_frontmatter(status_path)
        project_id = fm.get("project", status_path.parent.name)

        for field in REQUIRED_FIELDS:
            if field not in fm:
                errors.append(f"  [{project_id}] missing required field: '{field}'")

        status_val = fm.get("status")
        if status_val is not None and status_val not in VALID_STATUSES:
            errors.append(
                f"  [{project_id}] invalid status '{status_val}' — must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

        for field in RECOMMENDED_FIELDS:
            if field not in fm:
                warnings.append(f"  [{project_id}] missing recommended field: '{field}'")

    total = len(status_files)
    error_count = len(errors)
    warn_count = len(warnings)

    if not errors and not warnings:
        print(f"  All {total} project(s) valid. ✓")
        return

    if errors:
        print(f"  Errors ({error_count}):")
        for e in errors:
            print(e)

    if warnings:
        print(f"  Warnings ({warn_count}):")
        for w in warnings:
            print(w)

    print(f"\n  {total} project(s) checked. {error_count} error(s), {warn_count} warning(s).")

    if errors:
        sys.exit(1)
