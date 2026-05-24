#!/usr/bin/env bash
# MewVault Bootstrap Installer
#
# Usage (one-liner):
#   curl -fsSL https://raw.githubusercontent.com/mewking2099/MewVault/main/bootstrap.sh | bash
#
# Or clone first and run:
#   bash bootstrap.sh [workspace_path]
#
# Default workspace: ~/Jan

set -euo pipefail

MEWVAULT_REPO="https://github.com/mewking2099/MewVault.git"
WORKSPACE="${1:-$HOME/Jan}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; exit 1; }
step() { echo -e "\n${BOLD}$*${NC}"; }

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD} MewVault Bootstrap${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Workspace : $WORKSPACE"
echo ""

# ── 1. Dependency check ───────────────────────────────────────────────────────
step "1. Checking dependencies"

command -v git &>/dev/null && ok "git" || fail "git not found — install: xcode-select --install"

PY=""
for cmd in python3.13 python3.12 python3.11 python3; do
  if command -v "$cmd" &>/dev/null && "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    PY="$cmd"
    break
  fi
done
[ -n "$PY" ] && ok "Python ($PY)" || fail "Python 3.11+ required — install: brew install python@3.11"

command -v node &>/dev/null && ok "Node.js" || warn "Node.js not found — hooks will not run (install: brew install node)"

# ── 2. Workspace directory ────────────────────────────────────────────────────
step "2. Workspace"

mkdir -p "$WORKSPACE"
ok "directory: $WORKSPACE"

# ── 3. Clone / update mewvault ───────────────────────────────────────────────
step "3. mewvault"

if [ -d "$WORKSPACE/mewvault/.git" ]; then
  echo "  already cloned — pulling latest…"
  git -C "$WORKSPACE/mewvault" pull --ff-only --quiet
  ok "up to date"
else
  git clone --quiet "$MEWVAULT_REPO" "$WORKSPACE/mewvault"
  ok "cloned from GitHub"
fi

# ── 4. Install mew CLI ────────────────────────────────────────────────────────
step "4. mew CLI"

"$PY" -m pip install --quiet -e "$WORKSPACE/mewvault"
ok "installed (editable) — updates apply on git pull"

# Reload PATH in case pip user-bin wasn't in it
PY_USER_BIN=$("$PY" -m site --user-base 2>/dev/null)/bin
export PATH="$PY_USER_BIN:$PATH"

# ── 5. mewwiki scaffold ───────────────────────────────────────────────────────
step "5. mewwiki"

if [ -d "$WORKSPACE/mewwiki" ] && [ "$(ls -A "$WORKSPACE/mewwiki" 2>/dev/null)" ]; then
  ok "already present — not touching"
else
  mkdir -p "$WORKSPACE/mewwiki/Brain"
  mkdir -p "$WORKSPACE/mewwiki/_inbox"
  mkdir -p "$WORKSPACE/mewwiki/Projects"
  mkdir -p "$WORKSPACE/mewwiki/templates"
  TODAY=$(date +%Y-%m-%d)
  cat > "$WORKSPACE/mewwiki/Brain/North Star.md" << EOF
---
updated: $TODAY
---
# North Star

## Active Focus
<!-- What you're working on right now -->

## Active Projects
<!-- Auto-updated by mew wiki sync -->

## This Week
<!-- Top 3 priorities -->
1.
2.
3.

## Quarterly Goal
<!-- One sentence -->
EOF
  ok "fresh wiki scaffold created at $WORKSPACE/mewwiki"
fi

# ── 6. Claude Code workspace config ──────────────────────────────────────────
step "6. Claude Code config"

CLAUDE_DIR="$WORKSPACE/.claude"
mkdir -p "$CLAUDE_DIR"

# Rules: symlink to bootstrap/rules (single source of truth inside mewvault)
if [ -L "$CLAUDE_DIR/rules" ]; then
  ok "rules symlink exists"
elif [ -d "$CLAUDE_DIR/rules" ]; then
  warn "rules/ is already a directory — not replacing (existing install detected)"
else
  ln -s "$WORKSPACE/mewvault/bootstrap/rules" "$CLAUDE_DIR/rules"
  ok "rules → mewvault/bootstrap/rules"
fi

# settings.json: generate from template (substitutes WORKSPACE path)
SETTINGS="$CLAUDE_DIR/settings.json"
if [ -f "$SETTINGS" ]; then
  ok "settings.json exists — not overwriting"
else
  sed "s|{{WORKSPACE}}|$WORKSPACE|g" \
    "$WORKSPACE/mewvault/bootstrap/settings.template.json" \
    > "$SETTINGS"
  ok "settings.json generated"
fi

# Workspace silos (empty dirs so Claude can open them)
for silo in software-projects design-studio game-lab; do
  mkdir -p "$WORKSPACE/$silo"
done
ok "silo directories ready"

# ── 7. Shell PATH setup ───────────────────────────────────────────────────────
step "7. PATH"

if command -v mew &>/dev/null; then
  ok "mew in PATH"
else
  if [ "$SHELL" = "/bin/zsh" ] || [ -n "${ZSH_VERSION:-}" ]; then
    PROFILE="$HOME/.zshrc"
  else
    PROFILE="$HOME/.bash_profile"
  fi
  if [ -d "$PY_USER_BIN" ]; then
    LINE="export PATH=\"$PY_USER_BIN:\$PATH\""
    grep -qxF "$LINE" "$PROFILE" 2>/dev/null || echo "$LINE" >> "$PROFILE"
    ok "added $PY_USER_BIN to $PROFILE"
    warn "open a new terminal tab for PATH to take effect"
  else
    warn "could not detect pip user bin — add 'mew' to PATH manually"
  fi
fi

# ── 8. Done ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD} Installation complete${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Install Claude Code (if not already):"
echo "     npm install -g @anthropic-ai/claude-code"
echo ""
echo "  2. Store your Anthropic API key:"
echo "     mew secret set ANTHROPIC_API_KEY"
echo ""
echo "  3. Open Obsidian → Add vault → $WORKSPACE/mewwiki"
echo "     (a fresh scaffold was created — it's yours, not anyone else's)"
echo ""
echo "  4. Back up your wiki to your own GitHub (optional):"
echo "     cd $WORKSPACE/mewwiki && git init && git remote add origin <your-repo-url>"
echo ""
echo "  5. Open a new terminal, cd to workspace, and start Claude:"
echo "     cd $WORKSPACE && claude"
echo ""
echo "  6. First session — run standup to orient:"
echo "     standup"
echo ""
if ! command -v node &>/dev/null; then
  echo -e "  ${YELLOW}⚠${NC}  Install Node.js for hooks (session-start, gate-guard, etc.):"
  echo "     brew install node"
  echo ""
fi
