"""mew harness — install and manage the MewHarness hook runtime."""
import json
import os
import shutil
import sys
from pathlib import Path

MEWVAULT_DIR = Path(__file__).parent.parent.parent.resolve()
HOOKS_DIR = MEWVAULT_DIR / "hooks"
TEMPLATES_RULES_DIR = MEWVAULT_DIR / "templates" / "rules"

HOOK_DEFINITIONS = [
    {
        "event": "UserPromptSubmit",
        "script": "session-start.js",
        "description": "Injects vault rules, project status, and instincts at session start",
    },
    {
        "event": "Stop",
        "script": "session-end.js",
        "description": "Writes auto-wrap log entry and suggested commit message",
    },
    {
        "event": "PreToolUse",
        "script": "pre-tool-use.js",
        "description": "MewKing gate, secrets guardian, immutable path guard, TDD warning",
    },
    {
        "event": "PostToolUse",
        "script": "post-tool-use.js",
        "description": "Accumulates session activity, detects correction signals for instinct pipeline",
    },
    {
        "event": "PreCompact",
        "script": "pre-compact.js",
        "description": "Runs semantic compact, writes context snapshots, preserves latest snapshot post-compaction",
    },
]


def run_harness(args) -> None:
    action = getattr(args, "action", "status")
    if action == "install":
        _install(args)
    elif action == "status":
        _status(args)
    elif action == "config":
        _config(args)
    elif action == "disable":
        _disable(args)
    elif action == "proxy":
        _proxy(args)
    else:
        print(f"Unknown harness action: {action}", file=sys.stderr)
        sys.exit(1)


def _install(args) -> None:
    workspace_root = _resolve_workspace(args)
    print(f"\nMewHarness Install")
    print(f"Workspace root: {workspace_root}\n")

    # Verify hook scripts exist
    missing = [h["script"] for h in HOOK_DEFINITIONS if not (HOOKS_DIR / h["script"]).exists()]
    if missing:
        print(f"Error: Missing hook scripts: {', '.join(missing)}", file=sys.stderr)
        print(f"Expected in: {HOOKS_DIR}", file=sys.stderr)
        sys.exit(1)

    claude_dir = workspace_root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # Write hooks to .claude/settings.json
    settings_file = claude_dir / "settings.json"
    settings = {}
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("Warning: Existing settings.json is malformed — will overwrite hooks section.")

    hooks = settings.setdefault("hooks", {})
    for hook_def in HOOK_DEFINITIONS:
        event = hook_def["event"]
        script_path = str(HOOKS_DIR / hook_def["script"])
        cmd = f"node \"{script_path}\""

        # Preserve existing hooks for this event, append if not already registered
        event_hooks = hooks.setdefault(event, [])
        already = any(
            (isinstance(h, dict) and h.get("command", "") == cmd)
            or h == cmd
            or (
                isinstance(h, dict)
                and isinstance(h.get("hooks"), list)
                and any(isinstance(hh, dict) and hh.get("command", "") == cmd for hh in h["hooks"])
            )
            for h in event_hooks
        )
        if not already:
            event_hooks.append({"matcher": "", "hooks": [{"type": "command", "command": cmd, "timeout": 15000}]})
            print(f"  Registered: {event} -> {hook_def['script']}")
        else:
            print(f"  Already registered: {event} -> {hook_def['script']}")

    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"\n  Written: {settings_file}")

    # Install rule templates
    _install_rules(workspace_root)

    # Install instinct directories
    instincts_pending = MEWVAULT_DIR / "instincts" / "pending"
    instincts_promoted = MEWVAULT_DIR / "instincts" / "promoted"
    instincts_pending.mkdir(parents=True, exist_ok=True)
    instincts_promoted.mkdir(parents=True, exist_ok=True)
    for d in [instincts_pending, instincts_promoted]:
        gk = d / ".gitkeep"
        if not gk.exists():
            gk.touch()

    # Validate node is available
    node_ok = shutil.which("node") is not None
    if not node_ok:
        print("\n  Warning: 'node' not found in PATH. Hooks require Node.js.")
    else:
        print(f"\n  Node.js: OK ({shutil.which('node')})")

    # Set MEWVAULT_ROOT env hint
    print(f"\n  Recommended: set MEWVAULT_ROOT={MEWVAULT_DIR}")
    print(f"    PowerShell: $env:MEWVAULT_ROOT = '{MEWVAULT_DIR}'")
    print(f"    bash:       export MEWVAULT_ROOT='{MEWVAULT_DIR}'")

    print("\nMewHarness installed. Restart Claude Code to activate hooks.\n")


def _install_rules(workspace_root: Path) -> None:
    rules_dst = workspace_root / ".claude" / "rules"
    rules_dst.mkdir(parents=True, exist_ok=True)

    for src_dir in sorted(TEMPLATES_RULES_DIR.iterdir()):
        if not src_dir.is_dir():
            continue
        dst_dir = rules_dst / src_dir.name
        dst_dir.mkdir(parents=True, exist_ok=True)
        installed = []
        for src_file in sorted(src_dir.glob("*.md")):
            dst_file = dst_dir / src_file.name
            if not dst_file.exists():
                shutil.copy(src_file, dst_file)
                installed.append(src_file.name)
        if installed:
            print(f"  Created: .claude/rules/{src_dir.name}/ ({', '.join(installed)})")


def _status(args) -> None:
    workspace_root = _resolve_workspace(args)
    claude_dir = workspace_root / ".claude"
    settings_file = claude_dir / "settings.json"

    print("\nMewHarness Status\n")
    print(f"Workspace: {workspace_root}")
    print(f"Hooks dir: {HOOKS_DIR}")
    print()

    if not settings_file.exists():
        print("  settings.json: not found — run 'mew harness install'")
        return

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("  settings.json: malformed JSON")
        return

    hooks = settings.get("hooks", {})
    print(f"{'Event':<22} {'Script':<22} {'Status'}")
    print("-" * 60)
    for hook_def in HOOK_DEFINITIONS:
        event = hook_def["event"]
        script = hook_def["script"]
        script_path = str(HOOKS_DIR / script)
        cmd = f"node \"{script_path}\""
        event_hooks = hooks.get(event, [])
        registered = any(
            (isinstance(h, dict) and h.get("command", "") == cmd)
            or h == cmd
            or (
                isinstance(h, dict)
                and isinstance(h.get("hooks"), list)
                and any(isinstance(hh, dict) and hh.get("command", "") == cmd for hh in h["hooks"])
            )
            for h in event_hooks
        )
        script_exists = (HOOKS_DIR / script).exists()
        status = "installed" if (registered and script_exists) else (
            "script missing" if registered else "not installed"
        )
        print(f"  {event:<20} {script:<22} {status}")

    # Rules
    print()
    rules_dir = claude_dir / "rules"
    if rules_dir.exists():
        rule_dirs = [d.name for d in sorted(rules_dir.iterdir()) if d.is_dir()]
        print(f"Rules dirs: {', '.join(rule_dirs) if rule_dirs else 'none'}")
    else:
        print("Rules: not installed")

    # Instincts
    pending = MEWVAULT_DIR / "instincts" / "pending"
    promoted = MEWVAULT_DIR / "instincts" / "promoted"
    pending_count = len(list(pending.glob("*.json"))) if pending.exists() else 0
    promoted_count = len(list(promoted.glob("*.json"))) if promoted.exists() else 0
    print(f"Instincts: {pending_count} pending, {promoted_count} promoted")
    print()


def _config(args) -> None:
    """Show or set a harness config value."""
    workspace_root = _resolve_workspace(args)
    settings_file = workspace_root / ".claude" / "settings.json"
    if not settings_file.exists():
        print("No settings.json found. Run 'mew harness install' first.", file=sys.stderr)
        sys.exit(1)

    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    key = getattr(args, "key", None)
    value = getattr(args, "value", None)

    if key is None:
        # Print all harness-related env keys
        print("\nHarness config env vars:")
        print(f"  MEWVAULT_ROOT               = {os.environ.get('MEWVAULT_ROOT', '(not set)')}")
        print(f"  MEW_SESSION_START_MAX_TOKENS = {os.environ.get('MEW_SESSION_START_MAX_TOKENS', '6000 (default)')}")
        return

    print(f"Use environment variables to configure harness. Key: {key} is not a settings.json field.")


def _disable(args) -> None:
    workspace_root = _resolve_workspace(args)
    settings_file = workspace_root / ".claude" / "settings.json"
    if not settings_file.exists():
        print("No settings.json found — nothing to disable.", file=sys.stderr)
        return

    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    hooks = settings.get("hooks", {})
    removed = 0
    for hook_def in HOOK_DEFINITIONS:
        event = hook_def["event"]
        script_path = str(HOOKS_DIR / hook_def["script"])
        cmd = f"node \"{script_path}\""
        if event in hooks:
            before = len(hooks[event])
            hooks[event] = [
                h for h in hooks[event]
                if not (
                    (isinstance(h, dict) and h.get("command", "") == cmd)
                    or h == cmd
                    or (
                        isinstance(h, dict)
                        and isinstance(h.get("hooks"), list)
                        and any(isinstance(hh, dict) and hh.get("command", "") == cmd for hh in h["hooks"])
                    )
                )
            ]
            removed += before - len(hooks[event])
            if not hooks[event]:
                del hooks[event]

    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"Disabled {removed} MewHarness hooks from settings.json.")
    print("Restart Claude Code to apply.")


def _pid_alive(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        pass
    import platform, subprocess
    if platform.system() == "Windows":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True,
        )
        return str(pid) in result.stdout
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _proxy(args) -> None:
    proxy_dir = MEWVAULT_DIR / "proxy"
    config_file = proxy_dir / "litellm-config.yaml"
    pid_file = proxy_dir / ".proxy.pid"

    if not proxy_dir.exists() or not config_file.exists():
        print("Error: proxy/litellm-config.yaml not found. Run 'mew harness install' first.", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "stop", False):
        _proxy_stop(pid_file)
        return

    # Check if already running
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if _pid_alive(pid):
                print(f"Proxy already running (PID {pid}) on http://localhost:4000")
                print("Use 'mew harness proxy --stop' to stop it.")
                return
        except Exception:
            pass
        pid_file.unlink(missing_ok=True)

    if not shutil.which("litellm"):
        print("Error: litellm not found. Run: pip install 'litellm[proxy]'", file=sys.stderr)
        sys.exit(1)

    import subprocess
    print(f"Starting MewVault LiteLLM proxy on http://localhost:4000 ...")
    print(f"Config: {config_file}\n")

    proc = subprocess.Popen(
        ["litellm", "--config", str(config_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pid_file.write_text(str(proc.pid))

    print(f"Proxy started (PID {proc.pid})")
    print(f"PID saved: {pid_file}\n")
    print("To route Claude Code through the proxy, set ANTHROPIC_BASE_URL:")
    print(f"  PowerShell:  $env:ANTHROPIC_BASE_URL = 'http://localhost:4000'")
    print(f"  bash/zsh:    export ANTHROPIC_BASE_URL='http://localhost:4000'\n")
    print("To stop:  mew harness proxy --stop")


def _proxy_stop(pid_file) -> None:
    if not pid_file.exists():
        print("No running proxy found (no PID file).")
        return
    try:
        pid = int(pid_file.read_text().strip())
        import signal, platform
        if platform.system() == "Windows":
            import subprocess
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
        pid_file.unlink(missing_ok=True)
        print(f"Proxy stopped (PID {pid}).")
    except ProcessLookupError:
        pid_file.unlink(missing_ok=True)
        print("Proxy was not running (stale PID file removed).")
    except Exception as e:
        print(f"Error stopping proxy: {e}", file=sys.stderr)


def _resolve_workspace(args) -> Path:
    if hasattr(args, "path") and args.path:
        return Path(args.path).resolve()
    # Walk up from mewvault looking for workspace root
    from mew.workspace import find_workspace_root
    mewvault_parent = MEWVAULT_DIR.parent
    return find_workspace_root(mewvault_parent)
