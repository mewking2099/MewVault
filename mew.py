#!/usr/bin/env python3
"""MewVault CLI entry point."""
import sys
import io

# Force UTF-8 output on Windows (avoids charmap encoding errors)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

if sys.version_info < (3, 11):
    print(f"Error: mew requires Python 3.11+. Current: {sys.version_info.major}.{sys.version_info.minor}", file=sys.stderr)
    sys.exit(1)

from mew.cli import main

if __name__ == "__main__":
    main()
