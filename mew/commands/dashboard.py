"""mew dashboard — self-contained HTML overview of the vault.

Generates <workspace>/.claude/dashboard.html from:
  - every Project_Status.md across silos (phase, tier, next_action, staleness)
  - .claude/doctor-status.json  (health)
  - .claude/agent-dispatches.jsonl  (agent activity)
  - mewwiki/_inbox  (queue depth)

No server, no dependencies. The page meta-refreshes every 60s;
use --watch N to regenerate in a loop so the refresh picks up changes.
"""
import html
import json
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from mew.utils import parse_frontmatter
from mew.workspace import find_workspace_root, find_project_status_files

STALE_DAYS = 14


def _load_projects(root: Path) -> list[dict]:
    projects = []
    for silo_key, status_path in find_project_status_files(root):
        data, _ = parse_frontmatter(status_path)
        if not isinstance(data, dict):
            data = {}
        last = str(data.get("last_session", "") or "")[:10]
        stale_days = None
        if last:
            try:
                stale_days = (datetime.now() - datetime.strptime(last, "%Y-%m-%d")).days
            except ValueError:
                pass
        open_p0 = data.get("open_p0")
        projects.append({
            "slug": status_path.parent.name,
            "silo": silo_key,
            "tier": str(data.get("tier", "?")),
            "phase": str(data.get("current_phase", data.get("status", "?"))),
            "next_action": str(data.get("next_action", "") or ""),
            "last_session": last or "—",
            "stale_days": stale_days,
            "open_p0": int(open_p0) if str(open_p0).isdigit() else None,
        })
    return sorted(projects, key=lambda p: (p["silo"], p["slug"]))


def _load_doctor(root: Path) -> dict:
    f = root / ".claude" / "doctor-status.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _load_agent_activity(root: Path, limit: int = 10) -> tuple[list[dict], int]:
    f = root / ".claude" / "agent-dispatches.jsonl"
    if not f.exists():
        return [], 0
    entries = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    dispatches = [e for e in entries if e.get("event") == "dispatch"]
    blocked = sum(1 for e in entries if e.get("event") == "blocked")
    return dispatches[-limit:], blocked


def _inbox_count(root: Path) -> int:
    inbox = root / "mewwiki" / "_inbox"
    if inbox.exists():
        return sum(1 for f in inbox.iterdir() if f.is_file() and f.suffix == ".md")
    return 0


def _render(root: Path) -> str:
    projects = _load_projects(root)
    doctor = _load_doctor(root)
    activity, blocked_count = _load_agent_activity(root)
    inbox = _inbox_count(root)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    overall = doctor.get("overall", "unknown")
    badge_bg = {"ok": "#1f6f43", "warn": "#8a6d1a", "fail": "#8a2a2a"}.get(overall, "#555")
    issues = [r for r in doctor.get("results", []) if r.get("status") != "ok"]

    rows = []
    for p in projects:
        stale = p["stale_days"] is not None and p["stale_days"] > STALE_DAYS
        stale_cell = f'{p["stale_days"]}d' if p["stale_days"] is not None else "—"
        row_style = ' style="color:#c98a3d"' if stale else ""
        if p["open_p0"] is None:
            p0_cell = "—"
        elif p["open_p0"] > 0:
            p0_cell = f'<strong style="color:#c0392b">{p["open_p0"]} P0</strong>'
        else:
            p0_cell = "0"
        rows.append(
            f"<tr{row_style}><td>{html.escape(p['slug'])}</td><td>{html.escape(p['silo'])}</td>"
            f"<td>{html.escape(p['tier'])}</td><td>{html.escape(p['phase'])}</td>"
            f"<td>{html.escape(p['next_action'][:70])}</td>"
            f"<td>{html.escape(p['last_session'])}</td><td>{stale_cell}</td><td>{p0_cell}</td></tr>"
        )

    issue_html = "".join(
        f"<li><strong>{html.escape(r.get('check', '?'))}</strong> "
        f"[{html.escape(r.get('status', ''))}] — {html.escape(r.get('message', ''))}</li>"
        for r in issues
    ) or "<li>All checks passing.</li>"

    activity_rows = "".join(
        f"<tr><td>{html.escape((e.get('ts') or '')[:16].replace('T', ' '))}</td>"
        f"<td>{html.escape(e.get('agent', '?'))}</td>"
        f"<td>{html.escape(e.get('model') or 'session default')}</td>"
        f"<td>{html.escape((e.get('description') or '')[:60])}</td></tr>"
        for e in reversed(activity)
    ) or '<tr><td colspan="4">No dispatches recorded yet.</td></tr>'

    blocked_note = (
        f'<p class="warn">{blocked_count} dispatch(es) blocked for missing model param.</p>'
        if blocked_count else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="60">
<title>MewVault Dashboard</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 980px;
         padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.05rem; margin-top: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 0.35rem 0.6rem; border-bottom: 1px solid #4443; }}
  th {{ font-weight: 600; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.6rem; border-radius: 4px;
           color: #fff; background: {badge_bg}; font-size: 0.8rem; }}
  .meta {{ color: #888; font-size: 0.8rem; }}
  .warn {{ color: #c98a3d; }}
  ul {{ padding-left: 1.2rem; }}
</style>
</head>
<body>
<h1>MewVault <span class="badge">doctor: {html.escape(overall)}</span></h1>
<p class="meta">Generated {now} · auto-refreshes every 60s (run <code>mew dashboard --watch 60</code> to keep data current) · mewwiki inbox: {inbox} item(s)</p>

<h2>Projects ({len(projects)})</h2>
<table>
<tr><th>Project</th><th>Silo</th><th>Tier</th><th>Phase</th><th>Next action</th><th>Last session</th><th>Idle</th><th>Audit P0</th></tr>
{''.join(rows)}
</table>

<h2>Health</h2>
<ul>{issue_html}</ul>

<h2>Agent activity (latest first)</h2>
{blocked_note}
<table>
<tr><th>When</th><th>Agent</th><th>Model</th><th>Task</th></tr>
{activity_rows}
</table>
</body>
</html>
"""


def run_dashboard(args) -> None:
    root = find_workspace_root()
    out = root / ".claude" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    watch = getattr(args, "watch", None)
    no_open = getattr(args, "no_open", False)

    out.write_text(_render(root), encoding="utf-8")
    print(f"\n  Dashboard written: {out}")
    if not no_open:
        webbrowser.open(out.as_uri())

    if watch:
        print(f"  Watching — regenerating every {watch}s (Ctrl-C to stop)\n")
        try:
            while True:
                time.sleep(watch)
                out.write_text(_render(root), encoding="utf-8")
                print(f"  regenerated {datetime.now().strftime('%H:%M:%S')}")
        except KeyboardInterrupt:
            print("\n  Stopped.\n")
    else:
        print()
