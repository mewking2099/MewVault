#!/usr/bin/env bash
# MewVault LiteLLM Proxy — Unix startup script
# Usage: bash start-proxy.sh
# Requires: pip install litellm[proxy]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/litellm-config.yaml"

if [ ! -f "$CONFIG" ]; then
  echo "Error: litellm-config.yaml not found at $CONFIG" >&2
  exit 1
fi

if ! command -v litellm &>/dev/null; then
  echo "Error: litellm not found. Run: pip install 'litellm[proxy]'" >&2
  exit 1
fi

echo "Starting MewVault LiteLLM proxy on http://localhost:4000 ..."
exec litellm --config "$CONFIG"
