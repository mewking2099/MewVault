"""mew check — MewVault sanity checker.

Exit codes:
  0 — all required checks pass
  1 — one or more required checks failed
"""
import sys
import shutil
import subprocess
import urllib.request
import json
from pathlib import Path
from mew.workspace import find_workspace_root


# ── Colour + Unicode support ──────────────────────────────────────────────────
def _supports_colour() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


C = _supports_colour()
GREEN  = "\033[38;5;114m" if C else ""
YELLOW = "\033[38;5;221m" if C else ""
RED    = "\033[38;5;203m" if C else ""
CYAN   = "\033[38;5;117m" if C else ""
PURPLE = "\033[38;5;141m" if C else ""
BOLD   = "\033[1m"        if C else ""
DIM    = "\033[2m"        if C else ""
NC     = "\033[0m"        if C else ""

ICON_PASS = f"{GREEN}✓{NC}"
ICON_WARN = f"{YELLOW}⚠{NC}"
ICON_FAIL = f"{RED}✗{NC}"

W = 52   # total inner width of the box

# ── Box drawing ───────────────────────────────────────────────────────────────
def _box_top()    -> str: return f"  {DIM}╭{'─' * W}╮{NC}"
def _box_bottom() -> str: return f"  {DIM}╰{'─' * W}╯{NC}"
def _box_mid()    -> str: return f"  {DIM}├{'─' * W}┤{NC}"
def _box_row(text: str, pad: int = 1) -> str:
    inner = f"{' ' * pad}{text}{' ' * pad}"
    # Strip ANSI for length calculation
    import re
    visible = re.sub(r'\033\[[0-9;]*m', '', inner)
    spaces  = W - len(visible)
    return f"  {DIM}│{NC}{inner}{' ' * max(spaces, 0)}{DIM}│{NC}"

def _section_row(label: str, colour: str) -> str:
    bar_len = W - len(label) - 3
    text = f" {colour}{BOLD}{label}{NC}{DIM}  {'─' * bar_len}{NC} "
    import re
    visible = re.sub(r'\033\[[0-9;]*m', '', text)
    spaces  = W - len(visible)
    return f"  {DIM}│{NC}{text}{' ' * max(spaces, 0)}{DIM}│{NC}"


# ── Result store ──────────────────────────────────────────────────────────────
_results: list[tuple[str, str, str]] = []

LABEL_W = 28   # fixed-width label column

def _row(icon: str, tier: str, label: str, note: str, status: str) -> None:
    import re
    label_padded = label.ljust(LABEL_W)
    note_str     = f"{DIM}{note}{NC}" if note else ""
    text         = f" {icon}  {label_padded}  {note_str}"
    visible      = re.sub(r'\033\[[0-9;]*m', '', f" {icon}  {label_padded}  {note}")
    spaces       = W - len(visible)
    print(f"  {DIM}│{NC}{text}{' ' * max(spaces, 0)}{DIM}│{NC}")
    _results.append((tier, label, status))

def _pass(tier: str, label: str, note: str = "") -> None:
    _row(ICON_PASS, tier, label, note, "pass")

def _warn(tier: str, label: str, note: str = "") -> None:
    _row(ICON_WARN, tier, label, note, "warn")

def _fail(tier: str, label: str, note: str = "") -> None:
    _row(ICON_FAIL, tier, label, note, "fail")

def _blank() -> None:
    print(_box_row(""))


# ── Individual checks ─────────────────────────────────────────────────────────

def _check_python() -> None:
    v   = sys.version_info
    ver = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 11):
        _pass("required", "Python 3.11+", ver)
    else:
        _fail("required", "Python 3.11+", f"found {ver} · brew install python@3.11")


def _check_node() -> None:
    if shutil.which("node"):
        try:
            ver = subprocess.check_output(["node", "--version"], text=True, timeout=5).strip()
            _pass("recommend", "Node.js", ver)
        except Exception:
            _warn("recommend", "Node.js", "installed, version check failed")
    else:
        _warn("recommend", "Node.js", "missing · hooks won't fire · brew install node")


def _check_claude() -> None:
    if shutil.which("claude"):
        _pass("recommend", "claude CLI", "found in PATH")
    else:
        _warn("recommend", "claude CLI", "npm install -g @anthropic-ai/claude-code")


def _check_mew() -> None:
    if shutil.which("mew"):
        _pass("required", "mew CLI", "found in PATH")
    else:
        _fail("required", "mew CLI", "pip install -e ~/Jan/mewvault")


def _check_workspace(root: Path | None) -> None:
    if root:
        _pass("required", "workspace root", str(root))
    else:
        _fail("required", "workspace root", "not found · run from inside ~/Jan/")


def _check_silos(root: Path | None) -> None:
    if not root:
        _fail("required", "silos", "cannot check — workspace root missing")
        return
    expected = ["mewvault", "software-projects", "game-lab", "design-studio"]
    missing  = [s for s in expected if not (root / s).exists()]
    if missing:
        _warn("recommend", "silos", f"missing: {', '.join(missing)}")
    else:
        _pass("recommend", "silos", "all four present")


def _check_claude_settings(root: Path | None) -> None:
    candidates   = []
    if root:
        candidates.append(root / ".claude" / "settings.json")
    candidates.append(Path.home() / ".claude" / "settings.json")

    settings_path = next((p for p in candidates if p.exists()), None)
    if not settings_path:
        _fail("required", "Claude hooks", "settings.json not found · run bootstrap.sh")
        return
    try:
        data     = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks    = data.get("hooks", {})
        pre      = hooks.get("PreToolUse", [])
        post     = hooks.get("PostToolUse", [])
        has_pre  = any("pre-tool-use"  in str(h) for g in pre  for h in g.get("hooks", []))
        has_post = any("post-tool-use" in str(h) for g in post for h in g.get("hooks", []))
        if has_pre and has_post:
            _pass("required", "Claude hooks", "PreToolUse + PostToolUse wired")
        elif has_pre:
            _warn("required", "Claude hooks", "PreToolUse wired, PostToolUse missing")
        elif has_post:
            _warn("required", "Claude hooks", "PostToolUse wired, PreToolUse missing")
        else:
            _fail("required", "Claude hooks", "no mewvault hooks · run bootstrap.sh")
    except Exception as e:
        _fail("required", "Claude hooks", f"parse error: {e}")


def _check_hook_files(root: Path | None) -> None:
    if not root:
        return
    hooks_dir      = root / "mewvault" / "hooks"
    required_hooks = ["pre-tool-use.js", "post-tool-use.js", "session-start.js", "session-end.js"]
    missing        = [h for h in required_hooks if not (hooks_dir / h).exists()]
    if missing:
        _fail("required", "hook scripts", f"missing: {', '.join(missing)}")
    else:
        _pass("required", "hook scripts", f"{len(required_hooks)} scripts present")


def _check_secrets_dir(root: Path | None) -> None:
    if not root:
        return
    secrets = root / "mewvault" / "secrets"
    if secrets.exists():
        keys = []
        env  = secrets / "workspace.env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    keys.append(line.split("=", 1)[0])
        _pass("required", "secrets/", f"{len(keys)} key(s) stored")
    else:
        _warn("required", "secrets/", "directory not found · mew secret set <KEY>")


def _check_instincts(root: Path | None) -> None:
    if not root:
        return
    promoted = root / "mewvault" / "instincts" / "promoted"
    if promoted.exists():
        count = sum(1 for f in promoted.glob("*.md"))
        _pass("recommend", "instincts", f"{count} promoted")
    else:
        _warn("recommend", "instincts", "promoted/ not found")


def _check_proxy() -> None:
    try:
        with urllib.request.urlopen("http://localhost:4000/health", timeout=2):
            _pass("optional", "DeepSeek proxy", "running on :4000")
    except Exception:
        _warn("optional", "DeepSeek proxy", "offline · Claude handles all tasks")


def _check_ruff() -> None:
    if shutil.which("ruff"):
        try:
            ver = subprocess.check_output(["ruff", "--version"], text=True, timeout=5).strip()
            _pass("optional", "ruff", ver)
        except Exception:
            _pass("optional", "ruff", "installed")
    else:
        _warn("optional", "ruff", "pip install ruff")


def _check_gdtoolkit() -> None:
    if shutil.which("gdlint"):
        _pass("optional", "gdtoolkit", "gdlint found")
    else:
        _warn("optional", "gdtoolkit", "pip install 'gdtoolkit==4.*'")


def _check_graphify() -> None:
    if shutil.which("graphify"):
        _pass("optional", "graphify", "found in PATH")
    else:
        _warn("optional", "graphify", "pip install graphifyy")


# ── Main runner ───────────────────────────────────────────────────────────────

def run_check(args) -> None:
    # Reset results for re-entrant calls
    _results.clear()

    print()
    print(_box_top())
    print(_box_row(f"  {PURPLE}{BOLD}⬡  MewVault{NC}  {DIM}sanity check{NC}", pad=0))
    print(_box_bottom())
    print()

    # ── REQUIRED ──────────────────────────────────────────────────────────────
    print(_box_top())
    print(_section_row("REQUIRED", RED))
    print(_box_mid())
    _check_python()
    _check_mew()
    _check_workspace(find_workspace_root())
    _check_claude_settings(find_workspace_root())
    _check_hook_files(find_workspace_root())
    _check_secrets_dir(find_workspace_root())
    print(_box_bottom())
    print()

    root = find_workspace_root()

    # ── RECOMMENDED ───────────────────────────────────────────────────────────
    print(_box_top())
    print(_section_row("RECOMMENDED", YELLOW))
    print(_box_mid())
    _check_node()
    _check_claude()
    _check_silos(root)
    _check_instincts(root)
    print(_box_bottom())
    print()

    # ── OPTIONAL ──────────────────────────────────────────────────────────────
    print(_box_top())
    print(_section_row("OPTIONAL", CYAN))
    print(_box_mid())
    _check_proxy()
    _check_ruff()
    _check_gdtoolkit()
    _check_graphify()
    print(_box_bottom())
    print()

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = sum(1 for _, _, s in _results if s == "pass")
    warned = sum(1 for _, _, s in _results if s == "warn")
    failed = sum(1 for _, _, s in _results if s == "fail")
    total  = len(_results)

    if failed:
        icon    = ICON_FAIL
        message = f"{RED}Fix the failing checks before using MewVault.{NC}"
    elif warned:
        icon    = ICON_WARN
        message = f"{YELLOW}Functional · address warnings for full experience.{NC}"
    else:
        icon    = ICON_PASS
        message = f"{GREEN}All systems go. MewVault is fully operational.{NC}"

    parts = []
    if passed: parts.append(f"{GREEN}{passed} passed{NC}")
    if warned: parts.append(f"{YELLOW}{warned} warnings{NC}")
    if failed: parts.append(f"{RED}{failed} failed{NC}")
    score_line = "  ".join(parts) + f"  {DIM}/ {total} checks{NC}"

    print(_box_top())
    print(_box_row(f" {icon}  {score_line}", pad=0))
    print(_box_mid())
    print(_box_row(f"    {message}", pad=0))
    print(_box_bottom())
    print()

    if failed:
        sys.exit(1)
