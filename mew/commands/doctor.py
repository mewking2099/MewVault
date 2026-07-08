"""mew doctor — automated MewVault health monitor.

Unlike `mew check` (interactive, human-facing), doctor is built to run
unattended: from the session-start hook, cron, or launchd.

- Writes machine-readable status to <workspace>/.claude/doctor-status.json
- `--notify` sends a macOS notification when anything is warn/fail
- `--quiet` prints only problems
- Exit codes: 0 = healthy, 1 = warnings, 2 = failures

Checks (all token-health oriented):
  cache_safety        ANTHROPIC_BASE_URL proxy / Headroom compression detection
  hook_matchers       PreToolUse/PostToolUse matchers not over-broad ("")
  hooks_registered    all five lifecycle hooks present in settings.json
  injection_size      session-start.js output within token budget and error-free
  instinct_queue      instincts/pending/ not overflowing
  signal_file         correction-signals.json not growing unbounded
  mcp_surface         number of always-on MCP servers in workspace .mcp.json
  ollama              embedding backend reachable (only if doobidoo configured)
  index_freshness     semantic index not older than newest wiki content
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from mew.workspace import find_workspace_root

MEWVAULT_ROOT = Path(os.environ.get("MEWVAULT_ROOT", Path(__file__).resolve().parents[2]))

OK, WARN, FAIL = "ok", "warn", "fail"


def _result(name, status, message):
    return {"check": name, "status": status, "message": message}


# ── Individual checks ─────────────────────────────────────────────────────────

def check_cache_safety(root: Path):
    """A rewriting proxy between Claude Code and the API breaks prompt caching.
    Cache reads cost ~0.1x input; a broken prefix re-bills the whole conversation
    every turn. This was the root cause of the July 2026 token burn."""
    problems = []
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    if base_url and "anthropic.com" not in base_url:
        problems.append(f"ANTHROPIC_BASE_URL routes through {base_url}")
    for var in ("HEADROOM_COMPRESS_USER_MESSAGES", "HEADROOM_COMPRESS_SYSTEM_MESSAGES"):
        if os.environ.get(var, "").lower() == "true":
            problems.append(f"{var}=true (prompt-cache breaking)")
    # Headroom proxy daemon still listening?
    try:
        urllib.request.urlopen("http://localhost:8787/health", timeout=1)
        problems.append("Headroom proxy still running on :8787 (launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.mewvault.headroom.plist)")
    except Exception:
        pass
    if problems:
        return _result("cache_safety", FAIL, "; ".join(problems))
    return _result("cache_safety", OK, "no cache-breaking proxy detected")


def check_hooks_registered(root: Path):
    settings = root / ".claude" / "settings.json"
    if not settings.exists():
        return _result("hooks_registered", FAIL, f"{settings} missing — run `mew harness install`")
    try:
        hooks = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {})
    except Exception as e:
        return _result("hooks_registered", FAIL, f"settings.json unreadable: {e}")
    expected = {"UserPromptSubmit", "Stop", "PreToolUse", "PostToolUse", "PreCompact", "SubagentStop"}
    missing = expected - set(hooks.keys())
    if missing:
        return _result("hooks_registered", FAIL, f"missing hooks: {', '.join(sorted(missing))}")
    return _result("hooks_registered", OK, "all 6 lifecycle hooks registered")


def check_hook_matchers(root: Path):
    settings = root / ".claude" / "settings.json"
    try:
        hooks = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {})
    except Exception:
        return _result("hook_matchers", WARN, "settings.json unreadable")
    bad = []
    for event in ("PreToolUse", "PostToolUse"):
        for entry in hooks.get(event, []):
            if isinstance(entry, dict) and entry.get("matcher", "") == "":
                bad.append(event)
    if bad:
        return _result("hook_matchers", WARN,
                       f"over-broad matcher \"\" on {', '.join(bad)} — node spawns on every tool call")
    return _result("hook_matchers", OK, "matchers scoped")


def check_injection_size(root: Path):
    hook = MEWVAULT_ROOT / "hooks" / "session-start.js"
    if not hook.exists():
        return _result("injection_size", FAIL, "session-start.js missing")
    max_tokens = int(os.environ.get("MEW_SESSION_START_MAX_TOKENS", "3000"))
    max_chars = max_tokens * 4
    payload = json.dumps({"session_id": f"doctor-{int(time.time())}", "cwd": str(root), "prompt": "doctor probe"})
    try:
        proc = subprocess.run(
            ["node", str(hook)], input=payload, capture_output=True,
            text=True, timeout=20,
        )
    except subprocess.TimeoutExpired:
        return _result("injection_size", FAIL, "session-start.js timed out (>20s)")
    except FileNotFoundError:
        return _result("injection_size", WARN, "node not on PATH — cannot probe")
    if proc.returncode != 0:
        return _result("injection_size", FAIL, f"session-start.js exited {proc.returncode}: {proc.stderr[:120]}")
    size = len(proc.stdout)
    est_tokens = size // 4
    if size > max_chars * 1.05:
        return _result("injection_size", WARN, f"first-prompt injection ~{est_tokens} tokens (budget {max_tokens})")
    return _result("injection_size", OK, f"first-prompt injection ~{est_tokens} tokens (budget {max_tokens})")


def check_instinct_queue(root: Path):
    pending = MEWVAULT_ROOT / "instincts" / "pending"
    count = len(list(pending.glob("*.json"))) if pending.exists() else 0
    if count > 50:
        return _result("instinct_queue", FAIL, f"{count} pending instincts — heuristic runaway, run `mew instinct prune`")
    if count > 25:
        return _result("instinct_queue", WARN, f"{count} pending instincts — review with `mew instinct status`")
    return _result("instinct_queue", OK, f"{count} pending instincts")


def check_signal_file(root: Path):
    f = root / ".claude" / "correction-signals.json"
    if f.exists() and f.stat().st_size > 100_000:
        return _result("signal_file", WARN, f"correction-signals.json is {f.stat().st_size // 1024}KB — stale entries not pruned")
    return _result("signal_file", OK, "correction-signals.json size healthy")


def check_mcp_surface(root: Path):
    f = root / ".mcp.json"
    if not f.exists():
        return _result("mcp_surface", OK, "no workspace .mcp.json")
    try:
        servers = list(json.loads(f.read_text(encoding="utf-8")).get("mcpServers", {}).keys())
    except Exception as e:
        return _result("mcp_surface", WARN, f".mcp.json unreadable: {e}")
    if len(servers) > 4:
        return _result("mcp_surface", WARN,
                       f"{len(servers)} always-on MCP servers ({', '.join(servers)}) — every schema loads into every session")
    return _result("mcp_surface", OK, f"{len(servers)} always-on MCP servers ({', '.join(servers) or 'none'})")


def check_ollama(root: Path):
    mcp = root / ".mcp.json"
    if not (mcp.exists() and "doobidoo" in mcp.read_text(encoding="utf-8")):
        return _result("ollama", OK, "doobidoo not configured — skipped")
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return _result("ollama", OK, "ollama reachable on :11434")
    except Exception:
        return _result("ollama", WARN, "ollama not reachable — semantic search degraded (brew services start ollama)")


def check_index_freshness(root: Path):
    db = Path.home() / ".mewvault" / "chroma-wiki" / "memory.db"
    wiki = root / "wiki"
    if not db.exists():
        return _result("index_freshness", OK, "no semantic index — skipped")
    newest = 0.0
    if wiki.exists():
        for p in wiki.rglob("*.md"):
            try:
                newest = max(newest, p.stat().st_mtime)
            except OSError:
                pass
    if newest and db.stat().st_mtime < newest - 7 * 86400:
        return _result("index_freshness", WARN,
                       "semantic index >7 days behind wiki content — run scripts/ingest_wiki.py")
    return _result("index_freshness", OK, "semantic index fresh")


def check_cache_burn(root: Path):
    """Low cache-hit ratio = prompt-prefix invalidation = the Headroom failure class.
    Reads the last 24h of Claude Code transcripts (cheap: mtime-filtered)."""
    try:
        from mew.commands.usage import parse_transcripts, cache_hit_ratio
        data = parse_transcripts(days=1)
        totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
        for d in data["days"].values():
            for k in totals:
                totals[k] += d[k]
        volume = totals["input"] + totals["cache_read"] + totals["cache_create"]
        if volume < 100_000:
            return _result("cache_burn", OK, "not enough transcript volume in last 24h to judge")
        ratio = cache_hit_ratio(totals)
        if ratio < 0.5:
            return _result("cache_burn", FAIL,
                           f"cache-hit ratio {ratio:.0%} over last 24h — prompt prefix is being "
                           f"invalidated between turns (see `mew usage --report`)")
        return _result("cache_burn", OK, f"cache-hit ratio {ratio:.0%} over last 24h")
    except Exception as e:
        return _result("cache_burn", OK, f"skipped ({e})")


def check_impeccable(root: Path):
    """Design tooling health: Impeccable installed, no colliding skill enabled."""
    skill = MEWVAULT_ROOT / ".agents" / "skills" / "impeccable" / "SKILL.md"
    if not skill.exists():
        return _result("impeccable", WARN,
                       "Impeccable skill missing at mewvault/.agents/skills/impeccable/ — UI work loses its quality flow")
    colliding = MEWVAULT_ROOT / "skills" / "frontend-design"
    if colliding.exists():
        return _result("impeccable", WARN,
                       "Anthropic frontend-design skill is enabled alongside Impeccable — they collide "
                       "(impeccable.style anti-pattern: 'pick one'). Move skills/frontend-design to skills/_disabled/")
    return _result("impeccable", OK, "Impeccable installed, no colliding design skill")


def _active_projects(root: Path):
    """Yield (name, status_text, last_session_days) for active software projects."""
    import re
    from datetime import datetime
    silo = root / "software-projects"
    if not silo.exists():
        return
    for proj in sorted(p for p in silo.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        f = proj / "Project_Status.md"
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if not re.search(r"^status:\s*active", text, re.M):
            continue
        idle = None
        m = re.search(r"^last_session:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
        if m:
            try:
                idle = (datetime.now() - datetime.strptime(m.group(1), "%Y-%m-%d")).days
            except ValueError:
                pass
        yield proj, text, idle


def check_ci_presence(root: Path):
    """Active code projects with a package.json should have the CI safety net."""
    missing = [p.name for p, _, _ in _active_projects(root)
               if (p / "package.json").exists()
               and not (p / ".github" / "workflows").exists()]
    if missing:
        return _result("ci_presence", WARN,
                       f"no CI workflow in: {', '.join(missing)} — run `mew ci install`")
    return _result("ci_presence", OK, "all active code projects have CI")


def check_wip_limit(root: Path):
    """More than 3 active projects, or active-but-idle 21+ days = attention debt."""
    projects = list(_active_projects(root))
    stale = [f"{p.name} ({idle}d)" for p, _, idle in projects if idle is not None and idle > 21]
    problems = []
    if len(projects) > 3:
        problems.append(f"{len(projects)} projects marked active (limit 3) — pause or archive some")
    if stale:
        problems.append(f"active but idle 21+ days: {', '.join(stale)}")
    if problems:
        return _result("wip_limit", WARN, "; ".join(problems))
    return _result("wip_limit", OK, f"{len(projects)} active project(s), none stale")


CHECKS = [
    check_cache_safety,
    check_cache_burn,
    check_hooks_registered,
    check_impeccable,
    check_ci_presence,
    check_wip_limit,
    check_hook_matchers,
    check_injection_size,
    check_instinct_queue,
    check_signal_file,
    check_mcp_surface,
    check_ollama,
    check_index_freshness,
]


# ── Runner ────────────────────────────────────────────────────────────────────

def _notify_macos(title: str, message: str):
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message[:180]}" with title "{title}" sound name "Funk"'],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


def run_doctor(args) -> None:
    root = find_workspace_root()
    results = []
    for check in CHECKS:
        try:
            results.append(check(root))
        except Exception as e:  # a broken check must never break doctor
            results.append(_result(check.__name__, WARN, f"check crashed: {e}"))

    warns = [r for r in results if r["status"] == WARN]
    fails = [r for r in results if r["status"] == FAIL]
    overall = FAIL if fails else (WARN if warns else OK)

    status = {
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "overall": overall,
        "results": results,
    }
    status_file = root / ".claude" / "doctor-status.json"
    try:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
    except OSError:
        pass

    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)
    if as_json:
        print(json.dumps(status, indent=2))
    else:
        for r in results:
            if quiet and r["status"] == OK:
                continue
            icon = {"ok": "✓", "warn": "⚠", "fail": "✗"}[r["status"]]
            print(f"  {icon} {r['check']}: {r['message']}")
        if not quiet or overall != OK:
            print(f"\n  overall: {overall} ({len(fails)} fail, {len(warns)} warn, "
                  f"{len(results) - len(fails) - len(warns)} ok)")

    if getattr(args, "notify", False) and overall != OK:
        worst = (fails or warns)[0]
        _notify_macos(
            f"MewVault doctor: {overall.upper()}",
            f"{len(fails)} fail / {len(warns)} warn — {worst['check']}: {worst['message']}",
        )

    if fails:
        sys.exit(2)
    if warns:
        sys.exit(1)
