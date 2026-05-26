"""mew memory — cross-session context store commands."""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

_BLOCKED = frozenset([
    "raw", "secrets", "research", ".obsidian", "export",
    "__pycache__", ".git", "node_modules", "dist", "build",
    "_archive", ".venv", "venv",
])

_SILOS: dict[str, str] = {
    "mewvault":          "mewvault",
    "idea-hub":          "idea-hub",
    "wiki":              "wiki",
    "design-studio":     "design-studio",
    "software-projects": "software-projects",
    "game-lab":          "game-lab",
}


def _find_workspace_root(start: Path) -> Path | None:
    d = start.resolve()
    while True:
        if (d / ".claude" / "rules" / "mew-common").exists():
            return d
        if (d / "mewvault").exists() and (d / "wiki").exists():
            return d
        parent = d.parent
        if parent == d:
            return None
        d = parent


def _extract_title(path: Path, fallback: str) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[:15]:
            line = line.strip()
            if line.startswith("title:"):
                return line.split(":", 1)[1].strip().strip("\"'")
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return fallback


def _extract_body(path: Path, max_chars: int = 1200) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                text = text[end + 3:].lstrip()
        return text[:max_chars]
    except Exception:
        return ""


def _classify(rel: Path) -> str | None:
    name = rel.name.lower()
    parts = rel.parts
    if name == "log.md":
        return "log"
    if name in ("idea.md", "feasibility.md", "brief.md", "status.md"):
        return "idea"
    if name == "plan.md" and "proposals" in parts:
        return "note"
    if len(parts) >= 2 and parts[-2] == "wiki":
        return "wiki"
    if name.endswith(".md") and len(parts) >= 2:
        return "wiki"
    return None


def _sync_silo(store, workspace_root: Path, silo_name: str, folder: str) -> int:
    silo_path = workspace_root / folder
    if not silo_path.exists():
        return 0
    count = 0
    for item in silo_path.rglob("*.md"):
        if not item.is_file():
            continue
        rel = item.relative_to(silo_path)
        if any(p in _BLOCKED or p.startswith(".") for p in rel.parts):
            continue
        entry_type = _classify(rel)
        if entry_type is None:
            continue
        project = rel.parts[0] if len(rel.parts) > 1 else None
        title = _extract_title(item, item.stem.replace("-", " ").title())
        body = _extract_body(item)
        if not body.strip():
            continue
        store.upsert(
            type=entry_type,
            silo=silo_name,
            project=project,
            source_path=str(item.relative_to(workspace_root)),
            title=title,
            body=body,
        )
        count += 1
    return count


def run_memory(args: argparse.Namespace) -> None:
    from mew.memory_store import MemoryStore, find_db

    workspace_root = _find_workspace_root(Path.cwd())
    if workspace_root is None:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    store = MemoryStore(find_db(workspace_root))
    action = getattr(args, "memory_action", None)

    try:
        if action == "sync" or action is None:
            target = getattr(args, "silo", None)
            silos = {target: _SILOS.get(target, target)} if target else _SILOS
            total = 0
            for silo_name, folder in silos.items():
                n = _sync_silo(store, workspace_root, silo_name, folder)
                if n:
                    print(f"  {silo_name}: {n} entries indexed")
                total += n
            print(f"Sync complete — {total} indexed, {store.count()} total.")

        elif action == "search":
            results = store.search(
                args.query,
                silo=getattr(args, "silo", None),
                limit=getattr(args, "limit", 10),
            )
            if not results:
                print("No results.")
                return
            for r in results:
                loc = f"{r['silo']}/{r['project']}" if r.get("project") else r["silo"]
                print(f"[{r['type']}] {r['title']}  ({loc})  {r['updated_at'][:10]}")
                snippet = (r.get("snippet") or r.get("body", ""))[:120].replace("\n", " ")
                print(f"  {snippet}\n")

        elif action == "recall":
            results = store.recall(
                silo=getattr(args, "silo", None),
                days=getattr(args, "days", 14),
                limit=getattr(args, "limit", 5),
            )
            silo_label = getattr(args, "silo", None)
            days_label = getattr(args, "days", 14)
            if not results:
                print(f"No entries in the last {days_label} days"
                      + (f" for silo '{silo_label}'" if silo_label else "") + ".")
                return
            for r in results:
                loc = f"{r['silo']}/{r['project']}" if r.get("project") else r["silo"]
                preview = (r["body"] or "")[:300].replace("\n", " ")
                print(f"### {r['title']} [{loc}] ({r['updated_at'][:10]})")
                print(preview)
                print()

        elif action == "purge":
            before = getattr(args, "before", None)
            days = getattr(args, "days", 90)
            cutoff = before if before else (datetime.utcnow() - timedelta(days=days)).isoformat()
            deleted = store.purge(cutoff)
            print(f"Purged {deleted} entries older than {cutoff[:10]}. {store.count()} remaining.")

        else:
            print("Usage: mew memory [sync|search|recall|purge]")
            print("  sync   [--silo NAME]")
            print("  search QUERY [--silo NAME] [--limit N]")
            print("  recall [--silo NAME] [--days N] [--limit N]")
            print("  purge  [--before DATE] [--days N]")

    finally:
        store.close()
