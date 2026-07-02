#!/usr/bin/env bash
set -euo pipefail

PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/com.mewvault.chromadb.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.mewvault.chromadb.plist"

echo "Installing ChromaDB launchd daemon..."
cp "$PLIST_SRC" "$PLIST_DST"
launchctl load -w "$PLIST_DST"
echo "Done. ChromaDB will start now and on every login."
echo "Logs: ~/.mewvault/logs/chromadb.log"
echo "Data: ~/.mewvault/chromadb/"
