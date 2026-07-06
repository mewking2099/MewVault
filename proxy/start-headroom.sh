#!/usr/bin/env bash
# MewVault Headroom Proxy — context compression for Claude Code
# Usage: bash proxy/start-headroom.sh
# Requires: pip install "headroom-ai[proxy,mcp]"
#
# After starting, launch Claude Code with:
#   ANTHROPIC_BASE_URL=http://localhost:8787 claude
#
# Optional flags you can add:
#   --intercept-tool-results        compress large tool outputs (experimental)
#   --memory --learn                learn from sessions, write to MEMORY.md
#   --mode cache                    freeze prior turns for max cache hits
#   --target-ratio 0.4              more aggressive compression (default: auto)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_FILE="$VAULT_ROOT/secrets/workspace.env"

if ! command -v headroom &>/dev/null; then
  echo "Error: headroom not found. Run: pip install 'headroom-ai[proxy,mcp]'" >&2
  exit 1
fi

# Load secrets so ANTHROPIC_API_KEY is available for API-key users
if [ -f "$SECRETS_FILE" ]; then
  echo "Loading secrets from secrets/workspace.env ..."
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
  set +a
else
  echo "Warning: secrets/workspace.env not found — using environment credentials" >&2
fi

echo "Starting Headroom compression proxy on http://localhost:8787 ..."
echo "  Then launch Claude Code with:"
echo "  ANTHROPIC_BASE_URL=http://localhost:8787 claude"
echo ""

HEADROOM_COMPRESS_USER_MESSAGES=true \
HEADROOM_COMPRESS_SYSTEM_MESSAGES=true \
exec headroom proxy \
  --port 8787 \
  --protect-tool-results "Bash,Read,Edit,Write,MultiEdit" \
  --no-telemetry
