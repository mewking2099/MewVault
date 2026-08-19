#!/usr/bin/env python3
"""
reindex_all.py — One-time full migration runner for always-on-memory.

DO NOT run this automatically. The owner runs this manually once after implementation.

Usage:
    python3 mewvault/scripts/reindex_all.py [--dry-run]

What it does:
  1. Archives existing ~/.mewvault/chroma/ and ~/.mewvault/chroma-wiki/ if present.
  2. For each silo (wiki, design, code, game, idea, mewvault):
     a. Run graphify build . in the silo root (or per-project for multi-project silos).
     b. Run index_silo.py --silo <silo> --full.
  3. Prints progress and final summary.
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MEWVAULT_DIR = Path.home() / ".mewvault"
SCRIPTS_DIR = Path(__file__).parent

SILO_DIRS = {
    "wiki":     Path("/Users/Mohabbat/Jan/mewwiki"),
    "design":   Path("/Users/Mohabbat/Jan/design-studio"),
    "code":     Path("/Users/Mohabbat/Jan/software-projects"),
    "game":     Path("/Users/Mohabbat/Jan/game-lab"),
    "idea":     Path("/Users/Mohabbat/Jan/idea-hub"),
    "mewvault": Path("/Users/Mohabbat/Jan/mewvault"),
}

# Silos that have per-project subdirectories to iterate
MULTI_PROJECT_SILOS = {"design", "code", "game"}


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def archive_dir(path: Path, dry_run: bool) -> None:
    if path.exists():
        backup = path.parent / f"{path.name}-backup-{ts()}"
        print(f"  Archiving {path} → {backup}")
        if not dry_run:
            shutil.move(str(path), str(backup))


def run_graphify(target: Path, dry_run: bool) -> str:
    graph_json = target / "graphify-out" / "graph.json"
    cmd = ["graphify", "update", str(target)]
    if dry_run:
        return f"dry-run (graphify update {target})"
    try:
        result = subprocess.run(
            cmd,
            timeout=180,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"WARN (exit {result.returncode}): {result.stderr[:200]}"
        return "OK"
    except subprocess.TimeoutExpired:
        return "TIMEOUT (60s)"
    except FileNotFoundError:
        return "SKIP (graphify not installed)"
    except Exception as exc:
        return f"ERROR: {exc}"


def run_indexer(silo: str, dry_run: bool) -> str:
    cmd = [sys.executable, str(SCRIPTS_DIR / "index_silo.py"), "--silo", silo, "--full"]
    if dry_run:
        return f"dry-run ({' '.join(cmd)})"
    try:
        result = subprocess.run(
            cmd,
            timeout=300,
            capture_output=True,
            text=True,
        )
        out = result.stdout.strip()
        if result.returncode != 0:
            return f"WARN: {result.stderr[:200]}"
        return out or "OK"
    except subprocess.TimeoutExpired:
        return "TIMEOUT (5min)"
    except Exception as exc:
        return f"ERROR: {exc}"


def get_project_dirs(silo_dir: Path) -> list[Path]:
    """Return subdirectories of a multi-project silo that have Project_Status.md."""
    projects = []
    if not silo_dir.exists():
        return projects
    for sub in silo_dir.iterdir():
        if sub.is_dir() and (sub / "Project_Status.md").exists():
            projects.append(sub)
    return sorted(projects)


def main() -> None:
    parser = argparse.ArgumentParser(description="MewVault full reindex runner")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done, touch nothing")
    args = parser.parse_args()
    dry_run = args.dry_run

    if dry_run:
        print("DRY RUN — no changes will be made\n")

    # Step 1: Archive existing chroma stores
    print("=== Step 1: Archive existing ChromaDB stores ===")
    archive_dir(MEWVAULT_DIR / "chroma", dry_run)
    archive_dir(MEWVAULT_DIR / "chroma-wiki", dry_run)
    print()

    # Step 2: Process each silo
    silos = list(SILO_DIRS.keys())
    total_chunks = 0
    total_files = 0

    print("=== Step 2: Graphify + index per silo ===\n")
    for i, silo in enumerate(silos, start=1):
        silo_dir = SILO_DIRS[silo]
        print(f"[{i}/{len(silos)}] {silo}")

        if not silo_dir.exists():
            print(f"  SKIP — directory not found: {silo_dir}\n")
            continue

        if silo in MULTI_PROJECT_SILOS:
            projects = get_project_dirs(silo_dir)
            if not projects:
                print(f"  SKIP — no Project_Status.md subdirs found in {silo_dir}\n")
                continue

            for proj in projects:
                gfy = run_graphify(proj, dry_run)
                print(f"  project: {proj.name} — graphify: {gfy}")

            idx = run_indexer(silo, dry_run)
            print(f"  indexed: {idx}")

            # Parse chunk count from indexer output
            if "chunks" in idx:
                try:
                    parts = idx.split()
                    total_chunks += int(parts[1])
                    total_files += int(parts[4])
                except (IndexError, ValueError):
                    pass
        else:
            gfy = run_graphify(silo_dir, dry_run)
            print(f"  graphify: {gfy}")

            idx = run_indexer(silo, dry_run)
            print(f"  indexed: {idx}")

            if "chunks" in idx:
                try:
                    parts = idx.split()
                    total_chunks += int(parts[1])
                    total_files += int(parts[4])
                except (IndexError, ValueError):
                    pass

        print()

    # Step 3: Summary
    print("=== Summary ===")
    print(f"Total indexed: ~{total_chunks} chunks from ~{total_files} files")
    chroma_path = MEWVAULT_DIR / "chroma"
    if dry_run:
        print(f"ChromaDB store (would be at): {chroma_path}")
    else:
        if chroma_path.exists():
            print(f"ChromaDB store: {chroma_path}")
        else:
            print("ChromaDB store: not yet created (Ollama may have been offline)")

    if dry_run:
        print("\nDRY RUN complete — run without --dry-run to apply.")


if __name__ == "__main__":
    main()
