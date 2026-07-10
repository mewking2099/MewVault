"""mew brief <topic> — the total-context command.

Assembles everything the vault knows about a topic into one ranked,
source-cited, token-budgeted context pack:

  Decisions > People & Meetings > Specs & Design shards > Knowledge/wiki > Log mentions

Output: printed pack (for session injection) + saved artifact in
mewwiki/Knowledge/briefs/<slug>-<date>.md.

Token discipline: hard cap (default 2,000 tokens ≈ 8,000 chars), filled in
rank order — low-priority sections get whatever budget remains. Excerpts are
matching lines ±1 line of context, max 3 excerpts per file.

Note: doobidoo (semantic) is an MCP tool only Claude can call — the `brief`
trigger tells Claude to ALSO consult it; this CLI covers the lexical layer.
"""
import re
import sys
from datetime import date
from pathlib import Path

from mew.workspace import find_workspace_root

MAX_TOKENS_DEFAULT = 2000
SKIP_DIRS = {"node_modules", ".git", ".next", "venv", ".venv", "__pycache__",
             "Library", "dist", "build", ".obsidian", "_archive"}
MAX_FILE_BYTES = 300_000
MAX_EXCERPTS_PER_FILE = 3


def _iter_files(root: Path, patterns=(".md",)):
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix in patterns:
            yield p


def _excerpts(path: Path, needle: re.Pattern) -> list[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    out = []
    for i, line in enumerate(lines):
        if needle.search(line):
            ctx = lines[max(0, i - 1): i + 2]
            out.append(" / ".join(x.strip() for x in ctx if x.strip())[:300])
            if len(out) >= MAX_EXCERPTS_PER_FILE:
                break
    return out


def _collect(root: Path, topic: str) -> list[tuple[int, str, list[str]]]:
    """Return [(rank, source_label, excerpts)] — rank 0 = most important."""
    needle = re.compile(re.escape(topic), re.IGNORECASE)
    wiki = root / "mewwiki"
    results = []

    buckets = [
        (0, "Decision", [wiki / "Operations" / "Decisions"]),
        (1, "People/Meetings", [wiki / "Operations" / "People", wiki / "Operations" / "Meetings"]),
        (2, "Spec/Design", []),   # filled below from silos
        (3, "Knowledge", [wiki / "Knowledge", wiki / "Brain"]),
        (4, "Log", []),           # filled below
    ]

    # Silo scan: specs, design shards, project wikis, logs
    spec_dirs, log_files = [], []
    for silo in ("software-projects", "design-studio", "game-lab", "idea-hub"):
        silo_path = root / silo
        if not silo_path.exists():
            continue
        for proj in silo_path.iterdir():
            if not proj.is_dir() or proj.name.startswith(("_", ".")):
                continue
            for sub in ("specs", "design", "wiki", "proposals"):
                d = proj / sub
                if d.exists():
                    spec_dirs.append(d)
            lg = proj / "log.md"
            if lg.exists():
                log_files.append(lg)
    # mewvault is a project itself, not a project container
    mv = root / "mewvault"
    for sub in ("wiki", "proposals"):
        if (mv / sub).exists():
            spec_dirs.append(mv / sub)
    if (mv / "log.md").exists():
        log_files.append(mv / "log.md")

    for rank, label, dirs in buckets:
        if label == "Spec/Design":
            files = [f for d in spec_dirs for f in _iter_files(d)]
        elif label == "Log":
            files = log_files
        else:
            files = [f for d in dirs if d.exists() for f in _iter_files(d)]
        for f in files:
            # filename match counts even without content excerpts
            name_hit = bool(needle.search(f.stem.replace("-", " ")) or needle.search(f.stem))
            ex = _excerpts(f, needle)
            if ex or name_hit:
                rel = str(f.relative_to(root))
                results.append((rank, rel, ex or ["(filename match — read the file)"]))

    results.sort(key=lambda r: (r[0], r[1]))
    return results


def run_brief(args) -> None:
    topic = " ".join(getattr(args, "topic", []) or []).strip()
    if not topic:
        print("Usage: mew brief <topic>", file=sys.stderr)
        sys.exit(1)

    max_tokens = getattr(args, "tokens", None) or MAX_TOKENS_DEFAULT
    budget = max_tokens * 4
    root = find_workspace_root()
    results = _collect(root, topic)

    section_names = {0: "Decisions", 1: "People & Meetings", 2: "Specs & Design",
                     3: "Knowledge & Brain", 4: "Log mentions"}
    header = (f"# Brief: {topic}\n\ngenerated: {date.today()} · sources: {len(results)} file(s) · "
              f"budget: {max_tokens} tokens\n"
              f"> Lexical pack. Also consult `mcp__doobidoo__retrieve_memory(\"{topic}\")` for semantic hits.\n")
    parts, used = [header], len(header)
    current_section = None
    related_only = []

    for rank, rel, excerpts in results:
        block_lines = []
        if section_names.get(rank) != current_section:
            block_lines.append(f"\n## {section_names.get(rank, 'Other')}\n")
        block_lines.append(f"**{rel}**")
        block_lines += [f"- {e}" for e in excerpts]
        block = "\n".join(block_lines) + "\n"
        if used + len(block) > budget:
            related_only.append(rel)
            continue
        current_section = section_names.get(rank)
        parts.append(block)
        used += len(block)

    if related_only:
        tail = "\n## Related files (over budget — read on demand)\n" + \
               "\n".join(f"- {r}" for r in related_only[:25]) + "\n"
        parts.append(tail)

    if len(results) == 0:
        parts.append(f"\nNo lexical matches for '{topic}' in the vault. "
                     "Try a broader term, or the semantic layer may still have hits.\n")

    pack = "\n".join(parts)
    print(pack)

    # Saved artifact
    if not getattr(args, "no_save", False):
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50]
        out_dir = root / "mewwiki" / "Knowledge" / "briefs"
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"{slug}-{date.today()}.md"
            out.write_text(pack, encoding="utf-8")
            print(f"\n[saved: {out.relative_to(root)}]", file=sys.stderr)
        except OSError as e:
            print(f"\n[not saved: {e}]", file=sys.stderr)
