"""mew agent — list and invoke specialist agents via Claude Code sub-agents."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

MEWVAULT_DIR = Path(__file__).parent.parent.parent.resolve()
AGENTS_DIR = MEWVAULT_DIR / "templates" / "agents"

# Map stored model names → Claude Code --model aliases
_MODEL_ALIASES: dict[str, str] = {
    "claude-opus-4-7":           "opus",
    "claude-sonnet-4-6":         "sonnet",
    "claude-haiku-4-5-20251001": "haiku",
    "claude-haiku-4-5":          "haiku",
}

AGENT_REGISTRY = [
    {"name": "mew-planner",   "model": "claude-opus-4-7",           "silo": "global", "role": "Architecture and MewKing planning"},
    {"name": "mew-designer",  "model": "claude-sonnet-4-6",         "silo": "design", "role": "UX, Figma review, component specs"},
    {"name": "mew-coder",     "model": "claude-sonnet-4-6",         "silo": "code",   "role": "Implementation, refactoring, test generation"},
    {"name": "mew-gamedev",   "model": "claude-sonnet-4-6",         "silo": "game",   "role": "GDScript, game mechanics, Godot patterns"},
    {"name": "mew-learner",   "model": "claude-sonnet-4-6",         "silo": "wiki",   "role": "Concept distillation, research ingest"},
    {"name": "mew-archivist", "model": "claude-haiku-4-5-20251001", "silo": "global", "role": "Session wrap, log writes, git messages"},
    {"name": "mew-chief",     "model": "claude-sonnet-4-6",         "silo": "global", "role": "Cross-silo orchestration, triage, routing"},
]


def run_agent(args) -> None:
    action = getattr(args, "agent_action", None) or "list"
    if action == "list":
        _list_agents()
    elif action == "invoke":
        _invoke_agent(args)
    else:
        _list_agents()


def _list_agents() -> None:
    print("\nMewVault Agent Array\n")
    print(f"  {'':2} {'Name':<16} {'Model alias':<10} {'Silo':<10} Role")
    print("  " + "-" * 72)
    for a in AGENT_REGISTRY:
        installed = "ok" if (AGENTS_DIR / f"{a['name']}.md").exists() else " -"
        alias = _MODEL_ALIASES.get(a["model"], a["model"])
        print(f"  {installed} {a['name']:<16} {alias:<10} {a['silo']:<10} {a['role']}")
    print()
    print("  Invocation: claude --model <alias> --append-system-prompt <template>")
    print("  Auth: Claude Code subscription or ANTHROPIC_API_KEY (no proxy required)")
    print()


def _invoke_agent(args) -> None:
    name = getattr(args, "name", None)
    task = getattr(args, "task", None)

    if not name:
        print("Usage: mew agent invoke <name> [--task \"...\"]", file=sys.stderr)
        sys.exit(1)

    agent = next((a for a in AGENT_REGISTRY if a["name"] == name), None)
    if not agent:
        print(f"Unknown agent: {name}", file=sys.stderr)
        print(f"Available: {', '.join(a['name'] for a in AGENT_REGISTRY)}", file=sys.stderr)
        sys.exit(1)

    template_path = AGENTS_DIR / f"{name}.md"
    if not template_path.exists():
        print(f"Agent template not found: {template_path}", file=sys.stderr)
        print("Run 'mew harness install' to install agent templates.", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("claude"):
        print("Error: 'claude' not found in PATH.", file=sys.stderr)
        print("Install Claude Code: npm install -g @anthropic-ai/claude-code", file=sys.stderr)
        sys.exit(1)

    system_prompt = _strip_frontmatter(template_path.read_text(encoding="utf-8"))
    alias = _MODEL_ALIASES.get(agent["model"], agent["model"])

    if not task:
        # No task — launch an interactive Claude Code session with this agent's persona
        print(f"\nStarting interactive session: {name} ({alias})")
        print(f"Role: {agent['role']}")
        print("Type /exit or Ctrl+C to end the session.\n")
        cmd = ["claude", "--model", alias, "--append-system-prompt", system_prompt]
        os.execvp("claude", cmd)
        # execvp replaces this process — nothing below runs

    # --task provided: non-interactive print mode
    print(f"\n{name} ({alias}) — {agent['role']}")
    print(f"Task: {task}")
    print("-" * 60)

    result = subprocess.run([
        "claude",
        "--model", alias,
        "--append-system-prompt", system_prompt,
        "--print",
        task,
    ])
    sys.exit(result.returncode)


def _strip_frontmatter(content: str) -> str:
    """Remove YAML --- frontmatter block, return body only."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content
