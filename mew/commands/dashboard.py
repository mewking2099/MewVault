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


def _load_skill_matrix(root: Path) -> tuple[list[dict], dict]:
    """Parse career-studio/skills/matrix.md → (pillars, velocity_summary).

    pillars: [{name, skills: [{name, level, target, evidence, last, trend}]}]
    trend computed from last-evidence age: up (<30d), steady (<90d), dormant.
    """
    f = root / "career-studio" / "skills" / "matrix.md"
    if not f.exists():
        return [], {}
    from datetime import datetime
    pillars, current = [], None
    newest, evidence_count = None, 0
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = {"name": line[3:].strip(), "skills": []}
            pillars.append(current)
            continue
        if current is None or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0] in ("Skill", "---") or set(cells[0]) <= {"-"}:
            continue
        name, level, target, evidence, last = (cells + [""] * 5)[:5]
        trend, age = "·", None
        if last:
            try:
                dt = datetime.strptime(last[:10], "%Y-%m-%d")
                age = (datetime.now() - dt).days
                trend = "↑" if age < 30 else ("→" if age < 90 else "·")
                evidence_count += 1
                if newest is None or dt > newest:
                    newest = dt
            except ValueError:
                pass
        current["skills"].append({"name": name, "level": level, "target": target,
                                  "evidence": evidence, "last": last, "trend": trend, "age": age})
    velocity = {
        "newest_days": (datetime.now() - newest).days if newest else None,
        "evidence_count": evidence_count,
        "dormant_pillars": [p["name"] for p in pillars
                            if p["skills"] and all(s["trend"] == "·" for s in p["skills"])],
    }
    return pillars, velocity


def _render_skills(pillars: list[dict], velocity: dict) -> str:
    if not pillars:
        return ""
    if velocity.get("newest_days") is None:
        vel_line = "No evidence dated yet — run <code>skill review</code> to baseline."
    else:
        d = velocity["newest_days"]
        state = "growing" if d < 30 else ("quiet" if d < 60 else "STALLED")
        vel_line = f"Latest evidence: {d}d ago ({state}) · {velocity['evidence_count']} dated evidence entries"
        if velocity["dormant_pillars"]:
            vel_line += f' · dormant: {html.escape(", ".join(velocity["dormant_pillars"]))}'
    out = [f'<h2>Skills — growth compass</h2>\n<p class="meta">{vel_line} · ↑ &lt;30d · → &lt;90d · · dormant</p>']
    for p in pillars:
        rows = []
        for s in p["skills"]:
            try:
                lvl = int(s["level"]) if s["level"] else 0
            except ValueError:
                lvl = 0
            dots = '<span style="letter-spacing:2px">' + "●" * lvl + "○" * (5 - lvl) + "</span>"
            trend_color = {"↑": "#1f6f43", "→": "#8a6d1a", "·": "#999"}[s["trend"]]
            stale = ' style="color:#c98a3d"' if s["trend"] == "·" and s["last"] else ""
            rows.append(
                f'<tr{stale}><td>{html.escape(s["name"])}</td><td>{dots}</td>'
                f'<td style="color:{trend_color};font-weight:600">{s["trend"]}</td>'
                f'<td>{html.escape(s["last"] or "—")}</td>'
                f'<td>{html.escape(s["evidence"][:50] or "—")}</td></tr>'
            )
        out.append(
            f"<h3 style='font-size:0.95rem;margin-bottom:0.3rem'>{html.escape(p['name'])}</h3>\n"
            "<table>\n<tr><th>Skill</th><th>Level</th><th>Trend</th><th>Last evidence</th><th>Evidence</th></tr>\n"
            + "\n".join(rows) + "\n</table>"
        )
    return "\n".join(out)


def _load_learning(root: Path) -> list[dict]:
    """Learning tracks: due counts + streak/stage from learn-lab/*/Track_Status.md."""
    import json as _json
    import re
    out = []
    lab = root / "learn-lab"
    if not lab.exists():
        return out
    from datetime import date
    today = date.today().isoformat()
    for track_dir in sorted(p for p in lab.iterdir() if p.is_dir() and not p.name.startswith(".")):
        status_f = track_dir / "Track_Status.md"
        if not status_f.exists():
            continue
        text = status_f.read_text(encoding="utf-8")
        get = lambda k: ((re.search(rf"^{k}:\s*(.+)$", text, re.M) or [None, ""])[1]).split("#")[0].strip()
        info = {"track": track_dir.name, "phase": get("phase") or get("stage"),
                "streak": get("streak"), "due": None, "new": None}
        deck = track_dir / "srs" / "deck.jsonl"
        if deck.exists():
            due = new = 0
            for line in deck.read_text(encoding="utf-8").splitlines():
                try:
                    c = _json.loads(line)
                except _json.JSONDecodeError:
                    continue
                s = c.get("srs", {})
                if s.get("reps", 0) == 0 and s.get("lapses", 0) == 0:
                    new += 1
                elif s.get("due", "9999") <= today:
                    due += 1
            info["due"], info["new"] = due, new
        out.append(info)
    return out


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
    pillars, velocity = _load_skill_matrix(root)
    skills_html = _render_skills(pillars, velocity)
    tracks = _load_learning(root)
    if tracks:
        rows = "".join(
            f"<tr><td>{html.escape(t['track'])}</td><td>{html.escape(str(t['phase'] or '—'))}</td>"
            f"<td>{t['due'] if t['due'] is not None else '—'}</td>"
            f"<td>{t['new'] if t['new'] is not None else '—'}</td>"
            f"<td>{html.escape(str(t['streak'] or '—'))}</td></tr>"
            for t in tracks)
        learning_html = ("<h2>Learning tracks</h2>\n<table>\n"
                         "<tr><th>Track</th><th>Phase/Stage</th><th>Due</th><th>New</th><th>Streak</th></tr>\n"
                         + rows + "\n</table>")
    else:
        learning_html = ""
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

{learning_html}

{skills_html}
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
