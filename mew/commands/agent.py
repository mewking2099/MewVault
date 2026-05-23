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
    }
    fn = dispatch.get(action)
    if fn:
        fn(args)
    else:
        _list_agents(args)


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

    result = subprocess.run([
        "claude",
        "--model", model,
        "--append-system-prompt", context,
        "--print",
        task,
    ])
    sys.exit(result.returncode)


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


def _strip_frontmatter(content: str) -> str:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content
