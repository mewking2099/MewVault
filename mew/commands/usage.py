"""mew usage — show Claude auth status and open the usage dashboard.

--report parses Claude Code transcript JSONL (~/.claude/projects/) and shows
per-day token totals and the cache-hit ratio. A low cache-hit ratio is the
signature of prompt-cache breakage (see wiki/headroom-postmortem.md).
"""
import json
import subprocess
import sys
import platform
import time
from datetime import datetime
from pathlib import Path


def parse_transcripts(days: int = 7) -> dict:
    """Aggregate token usage from Claude Code transcripts, keyed by day.

    Returns {"days": {date: {input, output, cache_read, cache_create}}, "files": n}.
    Only reads transcript files modified within the window. Also used by
    `mew doctor` for the cache-burn check.
    """
    projects_dir = Path.home() / ".claude" / "projects"
    cutoff = time.time() - days * 86400
    by_day: dict = {}
    files_read = 0
    if not projects_dir.exists():
        return {"days": by_day, "files": 0}

    for f in projects_dir.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        files_read += 1
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    if '"usage"' not in line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    usage = (entry.get("message") or {}).get("usage") or {}
                    if not usage:
                        continue
                    ts = entry.get("timestamp", "")[:10]
                    if not ts:
                        continue
                    day = by_day.setdefault(ts, {"input": 0, "output": 0,
                                                 "cache_read": 0, "cache_create": 0})
                    day["input"] += usage.get("input_tokens", 0) or 0
                    day["output"] += usage.get("output_tokens", 0) or 0
                    day["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
                    day["cache_create"] += usage.get("cache_creation_input_tokens", 0) or 0
        except OSError:
            continue
    return {"days": by_day, "files": files_read}


def cache_hit_ratio(day: dict) -> float:
    """Fraction of all input-side tokens served from cache (0..1)."""
    total = day["input"] + day["cache_read"] + day["cache_create"]
    return (day["cache_read"] / total) if total else 1.0


def _report(days: int) -> None:
    data = parse_transcripts(days)
    by_day = data["days"]
    print(f"Token usage — last {days} day(s) ({data['files']} transcript file(s))")
    print("─" * 72)
    if not by_day:
        print("  No transcript data found in ~/.claude/projects/")
        print("  (Transcripts only exist on the machine where Claude Code runs.)")
        print()
        return

    print(f"  {'Day':<12} {'Input':>10} {'Cache read':>12} {'Cache create':>13} "
          f"{'Output':>10} {'Cache hit':>10}")
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    for date in sorted(by_day):
        d = by_day[date]
        for k in totals:
            totals[k] += d[k]
        ratio = cache_hit_ratio(d)
        flag = "  ⚠" if ratio < 0.5 and (d["input"] + d["cache_read"] + d["cache_create"]) > 100_000 else ""
        print(f"  {date:<12} {d['input']:>10,} {d['cache_read']:>12,} {d['cache_create']:>13,} "
              f"{d['output']:>10,} {ratio:>9.0%}{flag}")

    print("  " + "-" * 70)
    ratio = cache_hit_ratio(totals)
    print(f"  {'total':<12} {totals['input']:>10,} {totals['cache_read']:>12,} "
          f"{totals['cache_create']:>13,} {totals['output']:>10,} {ratio:>9.0%}")
    print()
    if ratio < 0.5:
        print("  ⚠ Cache-hit ratio below 50% — the prompt prefix is being invalidated")
        print("    between turns. Check for rewriting proxies (ANTHROPIC_BASE_URL),")
        print("    mid-session CLAUDE.md churn, or hooks with unstable output.")
        print()


def run_usage(args) -> None:
    if getattr(args, "report", False):
        _report(getattr(args, "days", None) or 7)
        return

    # ── Auth status ────────────────────────────────────────────────────────────
    print("Claude account\n" + "─" * 40)
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                logged_in = data.get("loggedIn", False)
                status_icon = "✓" if logged_in else "✗"
                print(f"  Status        {status_icon}  {'logged in' if logged_in else 'NOT logged in — mew harness will fail'}")
                if logged_in:
                    print(f"  Email         {data.get('email', '—')}")
                    print(f"  Org           {data.get('orgName', '—')}")
                    print(f"  Subscription  {data.get('subscriptionType', '—')}")
                    print(f"  Auth method   {data.get('authMethod', '—')}")
            except json.JSONDecodeError:
                print(result.stdout.strip())
        else:
            print("  Could not get auth status — run: claude auth login")
    except FileNotFoundError:
        print("  claude CLI not found. Install from: https://claude.ai/code")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("  claude auth status timed out")

    # ── Usage note ────────────────────────────────────────────────────────────
    print()
    print("Usage limits")
    print("─" * 40)
    print("  Anthropic does not expose quota via CLI for subscription accounts.")
    print("  Check remaining usage in your browser:")
    print()
    print("  claude.ai/settings → Usage")
    print("  console.anthropic.com → Usage  (API / team billing)")

    # ── Open browser ──────────────────────────────────────────────────────────
    if getattr(args, "open", False):
        url = "https://claude.ai/settings"
        print(f"\n  Opening {url} …")
        try:
            if platform.system() == "Darwin":
                subprocess.run(["open", url], check=True)
            elif platform.system() == "Windows":
                subprocess.run(["start", url], shell=True, check=True)
            else:
                subprocess.run(["xdg-open", url], check=True)
        except Exception as e:
            print(f"  Could not open browser: {e}")

    print()
