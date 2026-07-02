#!/usr/bin/env bash
# Install Headroom as a macOS login daemon via launchd.
# Runs automatically on login; survives reboots.
# Usage: bash proxy/install-headroom-daemon.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.mewvault.headroom.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.mewvault.headroom.plist"
LABEL="com.mewvault.headroom"
LOG_DIR="$HOME/.mewvault/logs"

mkdir -p "$LOG_DIR"

# Unload existing if present
if launchctl list "$LABEL" &>/dev/null; then
  echo "Stopping existing daemon ..."
  launchctl unload "$PLIST_DEST" 2>/dev/null
fi

cp "$PLIST_SRC" "$PLIST_DEST"
launchctl load "$PLIST_DEST"

# Give it a moment to start
sleep 2

if launchctl list "$LABEL" &>/dev/null; then
  echo "✓ Headroom daemon installed and running on http://localhost:8787"
  echo "  Logs: $LOG_DIR/headroom.log"
  echo ""
  echo "Add to ~/.zshrc to route Claude Code through it automatically:"
  echo "  export ANTHROPIC_BASE_URL=http://localhost:8787"
else
  echo "✗ Daemon failed to start. Check logs:"
  echo "  tail -50 $LOG_DIR/headroom.log"
  exit 1
fi
