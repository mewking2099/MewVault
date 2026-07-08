"""mew agent — dispatcher-driven specialist agents via Claude Code sub-agents."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from mew.lib.skill_loader import (
    AGENTS_DIR,
    assemble_context,
    build_routing_index,
    list_all_agents,
    parse_manifest,
    scan_agent_skills,
    write_routing_index,
    write_temp_mcp_config,
)

_MODEL_ALIASES = {
    "claude-opus-4-7":           "opus",
    "claude-sonnet-4-6":         "sonnet",
    "claude-haiku-4-5-20251001": "haiku",
    "claude-haiku-4-5":          "haiku",
    "opus": "opus",
    "sonnet": "sonnet",
    "haiku": "haiku",
}

# Fallback registry if agents/ dir doesn't exist yet
_FALLBACK_REGISTRY = [
    {"name": "mew-planner",   "model": "opus",   "silo": "global",  "role": "Architecture and MewKing planning"},
    {"name": "mew-designer",  "model": "sonnet", "silo": "design",  "role": "UX, Figma review, component specs"},
    {"name": "mew-coder",     "model": "sonnet", "silo": "code",    "role": "Implementation, refactoring, test generation"},
    {"name": "mew-gamedev",   "model": "sonnet", "silo": "game",    "role": "GDScript, game mechanics, Godot patterns"},
    {"name": "mew-learner",   "model": "sonnet", "silo": "wiki",    "role": "Concept distillation, research ingest"},
    {"name": "mew-archivist", "model": "haiku",  "silo": "global",  "role": "Session wrap, log writes, git messages"},
    {"name": "mew-chief",     "model": "sonnet", "silo": "global",  "role": "Cross-silo orchestration, triage, routing"},
]


def run_agent(args) -> None:
    action = getattr(args, "agent_action", None) or "list"
    dispatch = {
        "list":         _list_agents,
        "invoke":       _invoke_agent,
        "sync":         _sync,
        "fetch-skills": _fetch_skills,
        "status":       _agent_status,
    }
    fn = dispatch.get(action)
    if fn:
        fn(args)
    else:
        _list_agents(args)


# ── status ────────────────────────────────────────────────────────────────────

def _agent_status(args=None) -> None:
    """Show recent agent dispatches from the ledger written by agent-track.js."""
    import json
    from datetime import datetime, timedelta
    from mew.workspace import find_workspace_root

    root = find_workspace_root()
    ledger = Path(root) / ".claude" / "agent-dispatches.jsonl"
    limit = getattr(args, "limit", None) or 20

    print("\nMewVault Agent Activity\n")
    if not ledger.exists():
        print("  No dispatch ledger yet (.claude/agent-dispatches.jsonl).")
        print("  It is written by the agent-track.js hook on every Agent/Task dispatch.")
        print("  If agents have run since the hook was installed, something is wrong —")
        print("  check `mew harness status` and restart your Claude session.\n")
        return

    entries = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    dispatches = [e for e in entries if e.get("event") == "dispatch"]
    blocked    = [e for e in entries if e.get("event") == "blocked"]
    stops      = [e for e in entries if e.get("event") == "stop"]

    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent = [e for e in dispatches if e.get("ts", "") >= week_ago]

    print(f"  Ledger: {len(dispatches)} dispatches, {len(stops)} completions, "
          f"{len(blocked)} blocked (missing model) · last 7 days: {len(recent)}\n")

    if blocked:
        last_block = blocked[-1]
        print(f"  ! Last blocked dispatch: {last_block.get('agent')} at {last_block.get('ts', '?')[:16]}")
        print("    (blocked = Claude tried to launch a mew agent without a model param)\n")

    print(f"  {'When':<17} {'Agent':<18} {'Model':<22} Task")
    print("  " + "-" * 78)
    for e in dispatches[-limit:]:
        ts = (e.get("ts") or "")[:16].replace("T", " ")
        model = e.get("model") or "(session default)"
        print(f"  {ts:<17} {e.get('agent', '?'):<18} {model:<22} {e.get('description', '')[:34]}")
    print()


# ── list ──────────────────────────────────────────────────────────────────────

def _list_agents(args=None) -> None:
    agents = _load_agents()
    print("\nMewVault Agent Array\n")
    print(f"  {'':2} {'Name':<16} {'Model':<8} {'Silo':<10} {'Skills':<8} Role")
    print("  " + "-" * 76)
    for a in agents:
        installed = "ok" if (AGENTS_DIR / a["name"] / "system-prompt.md").exists() else " -"
        skill_count = len(scan_agent_skills(a["name"])) if AGENTS_DIR.exists() else "-"
        model = _MODEL_ALIASES.get(a["model"], a["model"])
        print(f"  {installed} {a['name']:<16} {model:<8} {a['silo']:<10} {str(skill_count):<8} {a['role']}")
    print()
    index_exists = (AGENTS_DIR / ".routing-index.json").exists()
    index_status = "current" if index_exists else "not built — run: mew agent sync"
    print(f"  Routing index: {index_status}")
    print(f"  Auth: Claude Code subscription or ANTHROPIC_API_KEY (no proxy required)")
    print()


# ── sync ──────────────────────────────────────────────────────────────────────

def _sync(args=None) -> None:
    print("\nMewVault Agent Sync\n")
    if not AGENTS_DIR.exists():
        print("  Error: agents/ directory not found.", file=sys.stderr)
        sys.exit(1)

    index_path = write_routing_index()
    index = build_routing_index()

    total_skills = sum(len(v) for v in index.values())
    print(f"  Scanned {len(index)} agents · {total_skills} skills")
    for agent_name, skills in sorted(index.items()):
        if skills:
            print(f"  {agent_name}: {', '.join(s['name'] for s in skills)}")
        else:
            print(f"  {agent_name}: (no skills yet)")
    print(f"\n  Written: {index_path}")
    print("  Restart your Claude session to apply changes.\n")


# ── fetch-skills ──────────────────────────────────────────────────────────────

def _fetch_skills(args=None) -> None:
    source = getattr(args, "from_source", None) or getattr(args, "url", None)
    if not source:
        print("Usage: mew agent fetch-skills --from <source> | --url <url>", file=sys.stderr)
        print("\nKnown sources:")
        print("  awesome-claude   — f/awesome-chatgpt-prompts (adapted)")
        print("  anthropic        — anthropics/prompt-library")
        print()
        print("Fetched skills are staged in agents/_fetched/ for review.")
        print("Promote with: mew agent promote-skill <agent> <file>")
        sys.exit(0)

    staged_dir = AGENTS_DIR / "_fetched" / (source.replace("/", "-").replace(":", ""))
    staged_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nFetch-skills: source = {source}")
    print(f"Staging to: {staged_dir}")
    print("(Fetching from external repos not yet implemented — drop .md files manually into agents/_fetched/)")
    print()


# ── invoke ────────────────────────────────────────────────────────────────────

def _invoke_agent(args) -> None:
    name = getattr(args, "name", None)
    task = getattr(args, "task", None)

    if not name:
        print("Usage: mew agent invoke <name> [--task \"...\"]", file=sys.stderr)
        sys.exit(1)

    agents = _load_agents()
    agent = next((a for a in agents if a["name"] == name), None)
    if not agent:
        print(f"Unknown agent: {name}", file=sys.stderr)
        print(f"Available: {', '.join(a['name'] for a in agents)}", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("claude"):
        print("Error: 'claude' not found in PATH.", file=sys.stderr)
        print("Install: npm install -g @anthropic-ai/claude-code", file=sys.stderr)
        sys.exit(1)

    model = _MODEL_ALIASES.get(agent["model"], agent["model"])

    # Assemble context: system-prompt + matched skills
    if task:
        context = assemble_context(name, task)
    else:
        # Interactive: load system-prompt + always-inject skills only
        context = assemble_context(name, "")

    if not context:
        # Fallback: old templates/agents/<name>.md
        fallback = Path(__file__).parent.parent.parent / "templates" / "agents" / f"{name}.md"
        if fallback.exists():
            from mew.commands.agent import _strip_frontmatter  # avoid circular
            context = _strip_frontmatter(fallback.read_text(encoding="utf-8"))
        else:
            print(f"No system prompt found for {name}.", file=sys.stderr)
            sys.exit(1)

    if not task:
        print(f"\nStarting interactive session: {name} ({model})")
        print(f"Role: {agent['role']}")
        skill_count = len(scan_agent_skills(name))
        if skill_count:
            print(f"Skills loaded: {skill_count} (always-inject only for interactive mode)")
        print("Type /exit or Ctrl+C to end.\n")
        os.execvp("claude", ["claude", "--model", model, "--append-system-prompt", context])

    print(f"\n→ {name} ({model}) — {agent['role']}")
    print(f"  Task: {task}\n" + "-" * 60)

    cmd = ["claude", "--model", model, "--append-system-prompt", context, "--print", task]
    mcp_tmp = write_temp_mcp_config(name)
    if mcp_tmp:
        cmd.extend(["--mcp-config", str(mcp_tmp), "--strict-mcp-config"])

    try:
        result = subprocess.run(cmd)
        exit_code = result.returncode
    finally:
        if mcp_tmp and mcp_tmp.exists():
            mcp_tmp.unlink()

    _execute_chains(name, task, exit_code)
    sys.exit(exit_code)


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_agents() -> list[dict]:
    """Load agent list from agents/*/manifest.yaml, fallback to hardcoded registry."""
    names = list_all_agents()
    if not names:
        return _FALLBACK_REGISTRY
    agents = []
    for name in names:
        m = parse_manifest(name)
        agents.append({
            "name": m.get("name", name),
            "model": m.get("model", "sonnet"),
            "silo": m.get("silo", "global"),
            "role": m.get("role", ""),
        })
    return agents


def _execute_chains(agent_name: str, task: str, prior_exit_code: int) -> None:
    """Fire on_complete chain links declared by skills that were triggered for this task."""
    if prior_exit_code != 0:
        return

    skills = scan_agent_skills(agent_name)
    task_lower = task.lower()

    for skill in skills:
        inject = skill.get("inject", "on-trigger")
        if inject == "manual":
            continue
        if inject == "on-trigger":
            triggers = skill.get("triggers", [])
            if not any(t.lower() in task_lower for t in triggers):
                continue

        for chain in skill.get("chains_to", []):
            if not isinstance(chain, dict):
                continue
            if chain.get("trigger", "on_complete") != "on_complete":
                continue
            next_agent = chain.get("agent")
            next_skill_name = chain.get("skill", "")
            if not next_agent:
                continue
            print(f"\n→ Chain: {agent_name}/{skill['name']} → {next_agent}/{next_skill_name}")
            _run_chained_agent(next_agent, next_skill_name, task)


def _run_chained_agent(agent_name: str, skill_name: str, task: str) -> None:
    """Invoke an agent as part of a skill chain, with MCP scoping."""
    agents = _load_agents()
    agent = next((a for a in agents if a["name"] == agent_name), None)
    if not agent:
        print(f"  Chain error: agent not found: {agent_name}", file=sys.stderr)
        return

    model = _MODEL_ALIASES.get(agent["model"], agent["model"])
    chain_task = f"{skill_name}: {task}" if skill_name else task
    context = assemble_context(agent_name, chain_task)

    if not context:
        print(f"  Chain error: no context assembled for {agent_name}", file=sys.stderr)
        return

    print(f"  {agent_name} ({model}) — {skill_name or 'default'}")

    cmd = ["claude", "--model", model, "--append-system-prompt", context, "--print", task]
    mcp_tmp = write_temp_mcp_config(agent_name)
    if mcp_tmp:
        cmd.extend(["--mcp-config", str(mcp_tmp), "--strict-mcp-config"])

    try:
        subprocess.run(cmd)
    finally:
        if mcp_tmp and mcp_tmp.exists():
            mcp_tmp.unlink()


def _strip_frontmatter(content: str) -> str:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content
