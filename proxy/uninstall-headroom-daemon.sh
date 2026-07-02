#!/usr/bin/env bash
# Remove the Headroom launchd daemon.
# Usage: bash proxy/uninstall-headroom-daemon.sh

PLIST="$HOME/Library/LaunchAgents/com.mewvault.headroom.plist"
LABEL="com.mewvault.headroom"

if launchctl list "$LABEL" &>/dev/null; then
  launchctl unload "$PLIST"
  echo "✓ Daemon stopped"
else
  echo "Daemon was not running"
fi

[ -f "$PLIST" ] && rm "$PLIST" && echo "✓ Plist removed"
echo "Done. Headroom will no longer start at login."
