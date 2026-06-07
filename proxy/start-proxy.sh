#!/usr/bin/env bash
# MewVault LiteLLM Proxy — Unix startup script
# Usage: bash start-proxy.sh
# Requires: pip install litellm[proxy]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG="$SCRIPT_DIR/litellm-config.yaml"
SECRETS_FILE="$VAULT_ROOT/secrets/workspace.env"

if [ ! -f "$CONFIG" ]; then
  echo "Error: litellm-config.yaml not found at $CONFIG" >&2
  exit 1
fi

if ! command -v litellm &>/dev/null; then
  echo "Error: litellm not found. Run: pip install 'litellm[proxy]'" >&2
  exit 1
fi

# Load secrets from workspace.env into the environment
if [ -f "$SECRETS_FILE" ]; then
  echo "Loading secrets from secrets/workspace.env ..."
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
  set +a
else
  echo "Warning: secrets/workspace.env not found — API keys must already be in environment" >&2
fi

echo "Starting MewVault LiteLLM proxy on http://localhost:4000 ..."
exec litellm --config "$CONFIG"
