"""mew agent — list and invoke specialist agents."""
import json
import sys
from pathlib import Path

MEWVAULT_DIR = Path(__file__).parent.parent.parent.resolve()
AGENTS_DIR = MEWVAULT_DIR / "templates" / "agents"

AGENT_REGISTRY = [
    {"name": "mew-planner",   "model": "claude-opus-4-7",   "silo": "global",  "role": "Architecture and MewKing planning"},
    {"name": "mew-designer",  "model": "claude-sonnet-4-6", "silo": "design",  "role": "UX, Figma review, component specs"},
    {"name": "mew-coder",     "model": "mimo-v2-pro",       "silo": "code",    "role": "Implementation, refactoring, test generation"},
    {"name": "mew-gamedev",   "model": "mimo-v2-pro",       "silo": "game",    "role": "GDScript, game mechanics, Godot patterns"},
    {"name": "mew-learner",   "model": "claude-sonnet-4-6", "silo": "wiki",    "role": "Concept distillation, Karpathy ingest"},
    {"name": "mew-archivist", "model": "claude-haiku-4-5",  "silo": "global",  "role": "Session wrap, log writes, git messages"},
    {"name": "mew-chief",     "model": "claude-sonnet-4-6", "silo": "global",  "role": "Cross-silo orchestration, triage, routing"},
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
    print(f"{'Name':<18} {'Model':<24} {'Silo':<10} Role")
    print("-" * 75)
    for a in AGENT_REGISTRY:
        template_path = AGENTS_DIR / f"{a['name']}.md"
        installed = "✓" if template_path.exists() else "○"
        print(f"  {installed} {a['name']:<16} {a['model']:<24} {a['silo']:<10} {a['role']}")
    print()
    print("Legend: ✓ template installed  ○ template not yet created")
    proxy_cfg = MEWVAULT_DIR / "proxy" / "litellm-config.yaml"
    if proxy_cfg.exists():
        print("LiteLLM proxy: configured (run 'mew harness proxy' to start)")
    else:
        print("LiteLLM proxy: not configured")
    print()


def _invoke_agent(args) -> None:
    name = args.name
    task = getattr(args, "task", None)
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

    print(f"\nInvoking {name} ({agent['model']}) — {agent['role']}")
    if task:
        print(f"Task: {task}")
    print()
    print("Note: Direct agent invocation requires the LiteLLM proxy to be running.")
    print("The agent system is designed to be invoked by Claude Code hooks,")
    print("not called directly from the CLI in v2.0.")
    print()
    print(f"Agent system prompt is at: {template_path}")
