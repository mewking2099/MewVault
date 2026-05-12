"""mew wiki — MewWiki Obsidian vault management (init + sync)."""
import json
import re
import subprocess
import sys
from pathlib import Path
from mew.workspace import find_workspace_root, get_silo_paths
from mew.utils import git_init, git_is_available, confirm, today_str, now_iso, parse_frontmatter


_MEWWIKI_POINTER = ".mewwiki"  # file in mewvault/ storing the vault path


# ── Public entry point ────────────────────────────────────────────────────────

def run_wiki(args) -> None:
    action = getattr(args, "wiki_action", None)
    if action == "init":
        _wiki_init(args)
    elif action == "sync":
        _wiki_sync(args)
    else:
        print("Usage: mew wiki init | mew wiki sync", file=sys.stderr)
        sys.exit(1)


# ── Phase 1: Init ─────────────────────────────────────────────────────────────

def _wiki_init(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    wiki_path = Path(args.path).expanduser().resolve() if getattr(args, "path", None) \
        else workspace_root / "mewwiki"

    print(f"\nMewWiki Init")
    print(f"Vault path: {wiki_path}\n")

    if wiki_path.exists() and any(wiki_path.iterdir()):
        print(f"Warning: {wiki_path} already exists and is not empty.")
        if not confirm("Continue? Existing files will not be overwritten."):
            print("Aborted.")
            return
        print()

    _create_dirs(wiki_path)
    _write_initial_content(wiki_path)
    _write_obsidian_config(wiki_path)
    _write_templates(wiki_path)
    _write_bases(wiki_path)
    _write_sync_manifest(wiki_path)

    if git_is_available():
        if not (wiki_path / ".git").exists():
            git_init(wiki_path)
            print("  git init: mewwiki/")
        subprocess.run(["git", "-C", str(wiki_path), "add", "-A"], capture_output=True)
        result = subprocess.run(
            ["git", "-C", str(wiki_path), "commit", "-m", "init: bootstrap mewwiki vault"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("  Initial commit: ok")

    mewvault_dir = Path(__file__).parent.parent.parent.resolve()
    (mewvault_dir / _MEWWIKI_POINTER).write_text(str(wiki_path), encoding="utf-8")
    print(f"\nVault path saved to mewvault/{_MEWWIKI_POINTER}")
    print(f"\nMewWiki ready at: {wiki_path}")
    print("\nNext steps:")
    print("  1. Open mewwiki/ in Obsidian as a new vault")
    print("  2. Enable Bases in Settings → Core plugins")
    print("  3. Run: mew wiki sync")
    print()


def _create_dirs(wiki_path: Path) -> None:
    dirs = [
        "Projects/_archive",
        "Knowledge/raw",
        "Knowledge/concepts",
        "Operations/People",
        "Operations/Meetings/_inbox",
        "Operations/Decisions",
        "Operations/Ideas",
        "Integrations/Calendar",
        "Integrations/GitHub",
        "Integrations/Teams",
        "Brain",
        "_inbox",
        "Templates",
        "Bases",
        ".obsidian",
    ]
    for d in dirs:
        (wiki_path / d).mkdir(parents=True, exist_ok=True)
    print("  Created directory structure")


def _write_initial_content(wiki_path: Path) -> None:
    today = today_str()
    files = {
        ".gitignore": _GITIGNORE,
        "README.md": _README_MD,
        "CLAUDE.md": _CLAUDE_MD,
        "Home.md": _HOME_MD.format(date=today),
        "Brain/North Star.md": _NORTH_STAR_MD.format(date=today),
        "Brain/Memories.md": _MEMORIES_MD.format(date=today),
        "Brain/Patterns.md": _PATTERNS_MD.format(date=today),
        "Brain/Gotchas.md": _GOTCHAS_MD.format(date=today),
        "Knowledge/index.md": _KNOWLEDGE_INDEX_MD.format(date=today),
        "Operations/Ideas/inbox.md": _IDEAS_INBOX_MD.format(date=today),
    }
    for rel, content in files.items():
        path = wiki_path / rel
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print("  Written: initial content")


def _write_obsidian_config(wiki_path: Path) -> None:
    obsidian = wiki_path / ".obsidian"
    configs = {
        "core-plugins.json": json.dumps([
            "file-explorer", "global-search", "switcher", "graph",
            "backlink", "outgoing-link", "tag-pane", "page-preview",
            "note-composer", "command-palette", "word-count",
            "file-recovery", "bases", "templates",
        ], indent=2),
        "app.json": json.dumps({
            "newFileLocation": "folder",
            "newFileFolderPath": "_inbox",
            "attachmentFolderPath": "Knowledge/raw",
            "showLineNumber": False,
            "readableLineLength": True,
            "strictLineBreaks": False,
        }, indent=2),
        "templates.json": json.dumps({
            "folder": "Templates",
        }, indent=2),
        "graph.json": json.dumps({
            "collapse-filter": False,
            "search": "",
            "showTags": False,
            "showAttachments": False,
            "hideUnresolved": False,
            "showOrphans": True,
            "collapse-color-groups": False,
            "colorGroups": [
                {"query": "path:Projects", "color": {"a": 1, "rgb": 928102}},
                {"query": "path:Knowledge", "color": {"a": 1, "rgb": 5519188}},
                {"query": "path:Operations", "color": {"a": 1, "rgb": 6710886}},
                {"query": "path:Brain", "color": {"a": 1, "rgb": 16750848}},
            ],
        }, indent=2),
        "appearance.json": json.dumps({
            "accentColor": "#0e2c46",
        }, indent=2),
    }
    for name, content in configs.items():
        path = obsidian / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print("  Written: .obsidian/ config")


def _write_templates(wiki_path: Path) -> None:
    templates = {
        "Meeting Note.md": _TPL_MEETING,
        "Decision.md": _TPL_DECISION,
        "Person Profile.md": _TPL_PERSON,
        "Concept Page.md": _TPL_CONCEPT,
        "Project Mirror.md": _TPL_PROJECT_MIRROR,
        "Idea.md": _TPL_IDEA,
        "API Note.md": _TPL_API_NOTE,
        "Gotcha.md": _TPL_GOTCHA,
    }
    for name, content in templates.items():
        path = wiki_path / "Templates" / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print("  Written: 8 templates")


def _write_bases(wiki_path: Path) -> None:
    bases = {
        "Active Projects.base": _BASE_ACTIVE_PROJECTS,
        "Stale Projects.base": _BASE_STALE_PROJECTS,
        "Decision Log.base": _BASE_DECISIONS,
        "Idea Pipeline.base": _BASE_IDEAS,
        "Knowledge Index.base": _BASE_KNOWLEDGE,
        "People Directory.base": _BASE_PEOPLE,
    }
    for name, content in bases.items():
        path = wiki_path / "Bases" / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print("  Written: 6 Bases dashboards")


def _write_sync_manifest(wiki_path: Path) -> None:
    manifest_path = wiki_path / ".sync-manifest.json"
    if not manifest_path.exists():
        manifest = {"version": 1, "last_sync": None, "repos": {}}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("  Written: .sync-manifest.json")


# ── Phase 2: Sync ─────────────────────────────────────────────────────────────

def _wiki_sync(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    wiki_path = _resolve_wiki_path(args, workspace_root)
    if not wiki_path or not wiki_path.exists():
        print(f"Error: mewwiki not found at {wiki_path}.", file=sys.stderr)
        print("Run 'mew wiki init' first, or pass --wiki <path>.", file=sys.stderr)
        sys.exit(1)

    dry_run = getattr(args, "dry_run", False)
    manifest_path = wiki_path / ".sync-manifest.json"
    manifest = _load_manifest(manifest_path)
    last_sync_date = manifest.get("last_sync", "")[:10] if manifest.get("last_sync") else ""

    silos = get_silo_paths(workspace_root)
    # (git_root, slug, silo_key, is_silo_level)
    projects = _discover_projects(workspace_root, silos)

    if not projects:
        print("No projects found to sync.")
        return

    print(f"\nMewWiki Sync{' (dry run)' if dry_run else ''}")
    print(f"Vault: {wiki_path}\n")

    # Cache git diffs per git_root to avoid redundant subprocess calls
    _sha_cache: dict[Path, str] = {}
    _diff_cache: dict[tuple[Path, str], list[str]] = {}
    synced = 0

    for git_root, slug, silo_key, is_silo_level in projects:
        manifest_key = f"{git_root}/{slug}" if is_silo_level else str(git_root)

        if git_root not in _sha_cache:
            _sha_cache[git_root] = _get_head_sha(git_root)
        current_sha = _sha_cache[git_root]
        if not current_sha:
            continue

        last_sha = manifest["repos"].get(manifest_key, "")
        if last_sha == current_sha:
            print(f"  ok (no changes): {slug}")
            continue

        cache_key = (git_root, last_sha)
        if cache_key not in _diff_cache:
            _diff_cache[cache_key] = _get_changed_files(git_root, last_sha)
        all_changed = _diff_cache[cache_key]

        # For silo-level repos, filter and strip the slug/ prefix
        if is_silo_level:
            prefix = f"{slug}/"
            changed = [f[len(prefix):] for f in all_changed if f.startswith(prefix)]
            project_root = git_root / slug
        else:
            changed = all_changed
            project_root = git_root

        if not changed:
            if not dry_run:
                manifest["repos"][manifest_key] = current_sha
            print(f"  ok (no relevant changes): {slug}")
            continue

        print(f"  syncing: {slug} ({len(changed)} changed file(s))")

        for rel_path in changed:
            p = Path(rel_path)
            if p.name == "log.md" and len(p.parts) == 1:
                _sync_log(project_root / p, wiki_path / "Projects" / slug / "log.md",
                          last_sync_date, dry_run)
            elif p.name == "Project_Status.md" and len(p.parts) == 1:
                _sync_status(project_root / p, wiki_path / "Projects" / slug / "index.md",
                             slug, silo_key, dry_run)
            elif p.parts[0] == "wiki" and p.suffix == ".md":
                page_name = p.stem
                dest = wiki_path / "_inbox" / f"{slug}-{page_name}.md"
                _sync_wiki_page(project_root / p, dest, slug, dry_run)

        if not dry_run:
            manifest["repos"][manifest_key] = current_sha
        synced += 1

    if not dry_run:
        manifest["last_sync"] = now_iso()
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        _commit_wiki(wiki_path)

    inbox_count = sum(1 for f in (wiki_path / "_inbox").iterdir()
                      if f.is_file()) if (wiki_path / "_inbox").exists() else 0
    print(f"\n  {synced} project(s) synced. Inbox: {inbox_count} item(s).")
    if inbox_count > 0:
        print(f"  Review _inbox/ in Obsidian and route notes to Knowledge/.")
    print()


def _resolve_wiki_path(args, workspace_root: Path) -> Path | None:
    if getattr(args, "wiki_path", None):
        return Path(args.wiki_path).expanduser().resolve()
    mewvault_dir = Path(__file__).parent.parent.parent.resolve()
    pointer = mewvault_dir / _MEWWIKI_POINTER
    if pointer.exists():
        return Path(pointer.read_text(encoding="utf-8").strip())
    return workspace_root / "mewwiki"


def _load_manifest(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": 1, "last_sync": None, "repos": {}}


def _discover_projects(workspace_root: Path, silos: dict) -> list[tuple[Path, str, str, bool]]:
    """Return [(git_root, slug, silo_key, is_silo_level)] for all projects."""
    results = []
    skip = {"_archive", "_experiments", "_templates", ".git"}

    for silo_key in ["software", "design", "games"]:
        silo_path = silos.get(silo_key)
        if not silo_path or not silo_path.exists():
            continue

        if (silo_path / ".git").exists():
            # Silo-level repo: each project is a subdir
            for child in sorted(silo_path.iterdir()):
                if child.is_dir() and child.name not in skip \
                        and not child.name.startswith(".") \
                        and (child / "Project_Status.md").exists():
                    results.append((silo_path, child.name, silo_key, True))
        else:
            # Per-project repos
            for child in sorted(silo_path.iterdir()):
                if child.is_dir() and child.name not in skip \
                        and (child / ".git").exists() \
                        and (child / "Project_Status.md").exists():
                    results.append((child, child.name, silo_key, False))

    return results


def _get_head_sha(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _get_changed_files(repo: Path, last_sha: str) -> list[str]:
    if not last_sha:
        result = subprocess.run(
            ["git", "-C", str(repo), "ls-files"],
            capture_output=True, text=True,
        )
    else:
        result = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-only", last_sha, "HEAD"],
            capture_output=True, text=True,
        )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().splitlines() if f]


def _sync_log(src: Path, dest: Path, since_date: str, dry_run: bool) -> None:
    if not src.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)

    src_content = src.read_text(encoding="utf-8")

    if not dest.exists():
        if not dry_run:
            dest.write_text(src_content, encoding="utf-8")
        print(f"    + created: Projects/{dest.parent.name}/{dest.name}")
        return

    # Append only new entries (newer than since_date) to top of existing log
    new_entries = _extract_log_entries_after(src_content, since_date)
    if not new_entries:
        return

    existing = dest.read_text(encoding="utf-8")
    # Insert new entries after "## Entries" line
    if "## Entries" in existing:
        parts = existing.split("## Entries", 1)
        after = parts[1].lstrip("\n")
        updated = parts[0] + "## Entries\n\n" + "\n".join(new_entries) + "\n\n" + after
    else:
        updated = existing + "\n\n" + "\n".join(new_entries)

    if not dry_run:
        dest.write_text(updated, encoding="utf-8")
    print(f"    + {len(new_entries)} new log entry(ies)")


def _extract_log_entries_after(content: str, since_date: str) -> list[str]:
    in_entries = False
    entries = []
    for line in content.splitlines():
        if line.strip() == "## Entries":
            in_entries = True
            continue
        if not in_entries:
            continue
        m = re.match(r"- \*\*(\d{4}-\d{2}-\d{2})\*\*", line)
        if m:
            if not since_date or m.group(1) > since_date:
                entries.append(line)
        elif entries and line.startswith("  "):
            # continuation of last entry
            entries.append(line)
    return entries


def _sync_status(src: Path, dest: Path, slug: str, silo: str, dry_run: bool) -> None:
    if not src.exists():
        return
    fm, _ = parse_frontmatter(src)
    if not fm:
        return

    dest.parent.mkdir(parents=True, exist_ok=True)

    blockers = fm.get("blockers") or []
    questions = fm.get("open_questions") or []

    content = f"""---
project: {fm.get('project', slug)}
silo: {silo}
status: {fm.get('status', 'unknown')}
stack: {fm.get('stack', '')}
tier: {fm.get('tier', '')}
current_phase: {fm.get('current_phase', '')}
last_session: {fm.get('last_session', '')}
synced: {today_str()}
---

# {fm.get('project', slug)}

**Status**: {fm.get('status', 'unknown')}
**Phase**: {fm.get('current_phase', '')}
**Last session**: {fm.get('last_session', '')}
**Next action**: {fm.get('next_action', '')}

## Blockers
{_fmt_list(blockers)}
## Open Questions
{_fmt_list(questions)}
## Log
→ [[{slug}/log|Full log]]
"""
    action = "updated" if dest.exists() else "created"
    if not dry_run:
        dest.write_text(content, encoding="utf-8")
    print(f"    + {action}: Projects/{slug}/index.md")


def _sync_wiki_page(src: Path, dest: Path, slug: str, dry_run: bool) -> None:
    if not src.exists():
        return
    if dest.exists():
        return  # never overwrite _inbox — user reviews first
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        content = src.read_text(encoding="utf-8")
        header = f"> Source: [[{slug}]] · Queued by mew wiki sync on {today_str()}\n\n"
        dest.write_text(header + content, encoding="utf-8")
    print(f"    + queued: _inbox/{dest.name}")


def _commit_wiki(wiki_path: Path) -> None:
    if not git_is_available() or not (wiki_path / ".git").exists():
        return
    subprocess.run(["git", "-C", str(wiki_path), "add", "-A"], capture_output=True)
    result = subprocess.run(
        ["git", "-C", str(wiki_path), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if not result.stdout.strip():
        return
    subprocess.run(
        ["git", "-C", str(wiki_path), "commit", "-m", f"sync: {now_iso()}"],
        capture_output=True,
    )
    print("  Committed changes to mewwiki.")


def _fmt_list(items: list) -> str:
    if not items:
        return "_None_\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


# ── Content templates ──────────────────────────────────────────────────────────

_GITIGNORE = """.DS_Store
Thumbs.db
*.tmp
*.pdf
*.png
*.jpg
*.jpeg
*.gif
*.webp
.obsidian/workspace.json
.obsidian/workspace-mobile.json
"""

_README_MD = """# MewWiki

This Obsidian vault is the read layer for your MewVault workspace.

**Written by**: `mew wiki sync` (runs at session end)
**Browsed in**: Obsidian
**Never edited directly** — write to silos, sync to here.

## Dashboards

Open the `Bases/` folder in Obsidian to see live dashboards:
- Active Projects
- Decision Log
- Idea Pipeline
- People Directory

## Sync

From mewvault: `mew wiki sync`
"""

_CLAUDE_MD = """# MewWiki — read-only reference

This vault is written by `mew wiki sync`. Do not write here directly from Claude Code.

To update content:
- Project logs/status → update silo, then `mew wiki sync`
- Notes → use `/dump` from mewvault
- Meetings → use `/meeting-capture` from mewvault
"""

_HOME_MD = """---
updated: {date}
---
# Home

Welcome to MewWiki.

## Active Projects
→ [[Bases/Active Projects]]

## Quick Links
- [[Brain/North Star]] — current focus
- [[Operations/Ideas/inbox]] — ideas inbox
- [[Knowledge/index]] — concept library

## Sync
Last synced: {date}
"""

_NORTH_STAR_MD = """---
updated: {date}
---
# North Star

## Active Focus
<!-- What you're working on right now -->

## Active Projects
<!-- Auto-updated by mew wiki sync -->

## This Week
<!-- Top 3 priorities -->
1.
2.
3.

## Quarterly Goal
<!-- One sentence -->
"""

_MEMORIES_MD = """---
updated: {date}
---
# Memories

Topic index — links to relevant concept pages and decisions.

## Architecture Decisions
<!-- [[Operations/Decisions/...]] -->

## Key People
<!-- [[Operations/People/...]] -->

## Patterns
→ [[Brain/Patterns]]

## Gotchas
→ [[Brain/Gotchas]]
"""

_PATTERNS_MD = """---
updated: {date}
---
# Patterns

Recurring approaches that work. Append-only.

<!-- Format: ## Pattern Name · Date -->
"""

_GOTCHAS_MD = """---
updated: {date}
---
# Gotchas

Things that burned time. Reference before starting similar work.

<!-- Format: ## Gotcha title · Date -->
"""

_KNOWLEDGE_INDEX_MD = """---
updated: {date}
---
# Knowledge Index

All concept pages in this vault. Auto-updated by mew wiki sync.

## Concepts
<!-- [[Knowledge/concepts/...]] -->

## Raw Sources
<!-- [[Knowledge/raw/...]] -->
"""

_IDEAS_INBOX_MD = """---
updated: {date}
---
# Ideas Inbox

Unsorted ideas. Review and file regularly.

Use `/dump idea <text>` from mewvault to add.

## Ideas
"""

# ── 8 Templates ───────────────────────────────────────────────────────────────

_TPL_MEETING = """---
date: {{date}}
attendees: []
project:
type: meeting
---
# Meeting — {{title}}

## Decisions
-

## Action Items
- [ ]

## Notes

## Follow-up
"""

_TPL_DECISION = """---
date: {{date}}
project:
status: decided
type: decision
---
# Decision — {{title}}

**Context**:

**Decision**:

**Rationale**:

**Alternatives considered**:

**Trade-offs**:
"""

_TPL_PERSON = """---
name: {{title}}
role:
org:
type: person
---
# {{title}}

**Role**:
**Org**:
**Last contact**:

## Notes

## Meeting history
"""

_TPL_CONCEPT = """---
title: {{title}}
source:
date: {{date}}
type: concept
---
# {{title}}

## Summary

## Key points

## Related
"""

_TPL_PROJECT_MIRROR = """---
project:
silo:
status: active
stack:
tier:
current_phase:
last_session:
synced: {{date}}
---
# {{title}}

**Status**: active
**Phase**:
**Last session**:
**Next action**:

## Blockers
_None_

## Open Questions
_None_

## Log
→ [[log|Full log]]
"""

_TPL_IDEA = """---
date: {{date}}
project:
type: idea
status: inbox
---
# {{title}}

**Context**:

**The idea**:

**Why it matters**:

**Next step**:
"""

_TPL_API_NOTE = """---
date: {{date}}
project:
type: api-note
---
# {{title}} — API Note

**Endpoint / Service**:

**Key behaviour**:

**Gotchas**:

**Example**:
```

```
"""

_TPL_GOTCHA = """---
date: {{date}}
project:
type: gotcha
---
# {{title}}

**What happened**:

**Root cause**:

**Fix / workaround**:

**Prevention**:
"""

# ── 6 Bases dashboards ────────────────────────────────────────────────────────
# Obsidian Bases JSON format. Open in Obsidian to adjust columns/filters.

_BASE_ACTIVE_PROJECTS = json.dumps({
    "filters": {
        "conjunction": "and",
        "conditions": [
            {"id": "1", "field": "status", "operator": "is", "value": "active"}
        ]
    },
    "columns": [
        {"id": "file-name", "field": "file-name", "width": 220},
        {"id": "silo", "field": "silo", "width": 120},
        {"id": "current_phase", "field": "current_phase", "width": 160},
        {"id": "last_session", "field": "last_session", "width": 120},
        {"id": "tier", "field": "tier", "width": 90},
    ],
    "sortBy": [{"field": "last_session", "direction": "desc"}],
    "source": {"type": "folder", "folder": "Projects"},
}, indent=2)

_BASE_STALE_PROJECTS = json.dumps({
    "filters": {
        "conjunction": "and",
        "conditions": [
            {"id": "1", "field": "status", "operator": "is", "value": "active"}
        ]
    },
    "columns": [
        {"id": "file-name", "field": "file-name", "width": 220},
        {"id": "silo", "field": "silo", "width": 120},
        {"id": "last_session", "field": "last_session", "width": 120},
        {"id": "current_phase", "field": "current_phase", "width": 160},
    ],
    "sortBy": [{"field": "last_session", "direction": "asc"}],
    "source": {"type": "folder", "folder": "Projects"},
}, indent=2)

_BASE_DECISIONS = json.dumps({
    "filters": {
        "conjunction": "and",
        "conditions": [
            {"id": "1", "field": "type", "operator": "is", "value": "decision"}
        ]
    },
    "columns": [
        {"id": "file-name", "field": "file-name", "width": 260},
        {"id": "project", "field": "project", "width": 160},
        {"id": "date", "field": "date", "width": 120},
        {"id": "status", "field": "status", "width": 100},
    ],
    "sortBy": [{"field": "date", "direction": "desc"}],
    "source": {"type": "folder", "folder": "Operations/Decisions"},
}, indent=2)

_BASE_IDEAS = json.dumps({
    "filters": {
        "conjunction": "and",
        "conditions": [
            {"id": "1", "field": "type", "operator": "is", "value": "idea"}
        ]
    },
    "columns": [
        {"id": "file-name", "field": "file-name", "width": 260},
        {"id": "project", "field": "project", "width": 160},
        {"id": "status", "field": "status", "width": 120},
        {"id": "date", "field": "date", "width": 120},
    ],
    "sortBy": [{"field": "date", "direction": "desc"}],
    "source": {"type": "folder", "folder": "Operations/Ideas"},
}, indent=2)

_BASE_KNOWLEDGE = json.dumps({
    "filters": {"conjunction": "and", "conditions": [
        {"id": "1", "field": "type", "operator": "is", "value": "concept"}
    ]},
    "columns": [
        {"id": "file-name", "field": "file-name", "width": 260},
        {"id": "source", "field": "source", "width": 200},
        {"id": "date", "field": "date", "width": 120},
    ],
    "sortBy": [{"field": "date", "direction": "desc"}],
    "source": {"type": "folder", "folder": "Knowledge"},
}, indent=2)

_BASE_PEOPLE = json.dumps({
    "filters": {"conjunction": "and", "conditions": [
        {"id": "1", "field": "type", "operator": "is", "value": "person"}
    ]},
    "columns": [
        {"id": "file-name", "field": "file-name", "width": 200},
        {"id": "role", "field": "role", "width": 180},
        {"id": "org", "field": "org", "width": 160},
    ],
    "sortBy": [{"field": "file-name", "direction": "asc"}],
    "source": {"type": "folder", "folder": "Operations/People"},
}, indent=2)
