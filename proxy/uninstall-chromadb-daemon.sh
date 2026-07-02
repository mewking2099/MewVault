#!/usr/bin/env bash
set -euo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.mewvault.chromadb.plist"

echo "Uninstalling ChromaDB launchd daemon..."
launchctl unload -w "$PLIST_DST" 2>/dev/null || true
rm -f "$PLIST_DST"
echo "Done. ChromaDB daemon removed. Data preserved at ~/.mewvault/chromadb/"
