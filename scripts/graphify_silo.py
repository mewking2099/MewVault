#!/usr/bin/env python3
"""
graphify_silo.py — Thin wrapper around `graphify update/build .` for MewVault silos.

Usage:
    python3 mewvault/scripts/graphify_silo.py --silo <silo> [--project <abs_path>]

Silos career and learn are skipped (exit 0 immediately).
Runs graphify build if no graph.json exists yet; otherwise graphify update.
Hard timeout: 30 seconds. Errors are logged to ~/.mewvault-hook-errors.log — never propagated.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ERROR_LOG = Path.home() / ".mewvault-hook-errors.log"

SILO_DIRS = {
    "wiki":     Path("/Users/Mohabbat/Jan/mewwiki"),
    "mewvault": Path("/Users/Mohabbat/Jan/mewvault"),
    "idea":     Path("/Users/Mohabbat/Jan/idea-hub"),
    # design, code, game require --project
}

SKIP_SILOS = {"career", "learn"}
PROJECT_SILOS = {"design", "code", "game"}


def log_error(msg: str) -> None:
    try:
        ts = datetime.now(timezone.utc).isoformat()
        with ERROR_LOG.open("a") as f:
            f.write(f"[{ts}] graphify_silo: {msg}\n")
    except Exception:
        pass


def run_graphify(target: Path) -> None:
    graph_json = target / "graphify-out" / "graph.json"
    cmd = ["graphify", "update", str(target)]
    try:
        result = subprocess.run(
            cmd,
            timeout=120,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log_error(f"graphify exited {result.returncode} in {target}: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        log_error(f"graphify timed out (30s) in {target}")
    except FileNotFoundError:
        log_error("graphify binary not found — install with: pip install graphifyy")
    except Exception as exc:
        log_error(f"unexpected error running graphify in {target}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MewVault graphify wrapper")
    parser.add_argument("--silo", required=True)
    parser.add_argument("--project", default="", help="Absolute path to project (required for design/code/game)")
    args = parser.parse_args()

    silo = args.silo.lower()

    if silo in SKIP_SILOS:
        sys.exit(0)

    if args.project:
        target = Path(args.project)
    elif silo in SILO_DIRS:
        target = SILO_DIRS[silo]
    elif silo in PROJECT_SILOS:
        log_error(f"--project required for silo '{silo}' but not provided")
        sys.exit(0)
    else:
        log_error(f"unknown silo '{silo}'")
        sys.exit(0)

    if not target.exists():
        log_error(f"target directory does not exist: {target}")
        sys.exit(0)

    run_graphify(target)


if __name__ == "__main__":
    main()
