"""skill_loader — scan agent skill directories and assemble sub-agent context."""
import json
import re
from pathlib import Path
from typing import Any

AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"
ROUTING_INDEX = AGENTS_DIR / ".routing-index.json"


# ── Frontmatter ───────────────────────────────────────────────────────────────

def parse_skill_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Frontmatter is YAML between --- markers."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 3:].lstrip("\n")
    fm: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            raw = val.strip()
            # Simple list: [a, b, c]
            if raw.startswith("[") and raw.endswith("]"):
                fm[key.strip()] = [v.strip().strip('"\'') for v in raw[1:-1].split(",") if v.strip()]
            else:
                fm[key.strip()] = raw.strip('"\'') or None
    return fm, body


def parse_manifest(agent_name: str) -> dict:
    path = AGENTS_DIR / agent_name / "manifest.yaml"
    if not path.exists():
        return {}
    import yaml  # optional dep — fallback to simple parser if unavailable
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return _simple_yaml_parse(path.read_text(encoding="utf-8"))


def _simple_yaml_parse(text: str) -> dict:
    """Minimal YAML parser for manifest files (no nested structures beyond lists)."""
    result: dict = {}
    current_key = None
    current_list: list | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list is not None:
            current_list.append(stripped[2:].strip())
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val:
                result[key] = val
                current_list = None
            else:
                result[key] = []
                current_list = result[key]
            current_key = key
    return result


# ── Skill scanning ────────────────────────────────────────────────────────────

def scan_agent_skills(agent_name: str) -> list[dict]:
    """Return list of skill dicts for an agent, sorted by name."""
    skills_dir = AGENTS_DIR / agent_name / "skills"
    if not skills_dir.exists():
        return []
    skills = []
    for f in sorted(skills_dir.glob("*.md")):
        fm, body = parse_skill_frontmatter(f.read_text(encoding="utf-8"))
        if not fm.get("name"):
            fm["name"] = f.stem
        fm["_path"] = str(f)
        fm["_body"] = body
        fm.setdefault("triggers", [])
        fm.setdefault("inject", "on-trigger")
        fm.setdefault("chains_to", [])
        fm.setdefault("claude_code_skills", [])
        fm.setdefault("requires_approval", False)
        skills.append(fm)
    return skills


def list_all_agents() -> list[str]:
    if not AGENTS_DIR.exists():
        return []
    return [
        d.name for d in sorted(AGENTS_DIR.iterdir())
        if d.is_dir() and not d.name.startswith("_") and (d / "manifest.yaml").exists()
    ]


# ── Routing index ─────────────────────────────────────────────────────────────

def build_routing_index() -> dict:
    """Scan all agents + skills and produce the routing index dict."""
    index: dict[str, list] = {}
    for agent_name in list_all_agents():
        skills = scan_agent_skills(agent_name)
        index[agent_name] = [
            {
                "name": s["name"],
                "triggers": s.get("triggers", []),
                "description": s.get("description", ""),
                "inject": s.get("inject", "on-trigger"),
                "chains_to": s.get("chains_to", []),
                "claude_code_skills": s.get("claude_code_skills", []),
            }
            for s in skills
        ]
    return index


def write_routing_index() -> Path:
    index = build_routing_index()
    ROUTING_INDEX.parent.mkdir(parents=True, exist_ok=True)
    ROUTING_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return ROUTING_INDEX


def read_routing_index() -> dict:
    if ROUTING_INDEX.exists():
        try:
            return json.loads(ROUTING_INDEX.read_text(encoding="utf-8"))
        except Exception:
            pass
    return build_routing_index()


# ── Context assembly ──────────────────────────────────────────────────────────

def assemble_context(agent_name: str, task: str, max_tokens: int = 4000) -> str:
    """
    Build the full context string for a sub-agent spawn:
    system-prompt.md + always-inject skills + on-trigger skills matching task.
    """
    parts: list[str] = []

    system_prompt_path = AGENTS_DIR / agent_name / "system-prompt.md"
    if system_prompt_path.exists():
        parts.append(system_prompt_path.read_text(encoding="utf-8").strip())

    skills = scan_agent_skills(agent_name)
    task_lower = task.lower()

    for skill in skills:
        inject = skill.get("inject", "on-trigger")
        if inject == "always":
            parts.append(_format_skill_block(skill))
        elif inject == "on-trigger":
            triggers = skill.get("triggers", [])
            if any(t.lower() in task_lower for t in triggers):
                parts.append(_format_skill_block(skill))
        # inject == "manual" → never auto-included

    context = "\n\n---\n\n".join(parts)
    # Rough token guard: ~4 chars per token
    if len(context) > max_tokens * 4:
        context = context[: max_tokens * 4]
    return context


def _format_skill_block(skill: dict) -> str:
    header = f"## Skill: {skill['name']}"
    if skill.get("description"):
        header += f"\n_{skill['description']}_"
    body = skill.get("_body", "").strip()
    chains = skill.get("chains_to", [])
    cc_skills = skill.get("claude_code_skills", [])
    extras = []
    if chains:
        extras.append("**Chains to:** " + ", ".join(
            f"{c['agent']}/{c['skill']}" if isinstance(c, dict) else str(c)
            for c in chains
        ))
    if cc_skills:
        extras.append("**CC skills:** " + ", ".join(cc_skills))
    if extras:
        body = body + "\n\n" + "\n".join(extras)
    return f"{header}\n\n{body}"


# ── Cycle detection ───────────────────────────────────────────────────────────

def detect_chains(agent_name: str, skill_name: str, visited: set | None = None) -> list[tuple]:
    """
    Return list of (agent, skill) chain steps. Raises ValueError on cycle.
    visited is the set of (agent, skill) pairs already in the chain.
    """
    if visited is None:
        visited = set()
    key = (agent_name, skill_name)
    if key in visited:
        raise ValueError(f"Cycle detected in skill chain: {agent_name}/{skill_name}")
    visited.add(key)

    skills = scan_agent_skills(agent_name)
    skill = next((s for s in skills if s["name"] == skill_name), None)
    if not skill:
        return []

    steps = [key]
    for chain in skill.get("chains_to", []):
        if isinstance(chain, dict):
            next_agent = chain.get("agent", agent_name)
            next_skill = chain.get("skill", "")
        else:
            continue
        steps.extend(detect_chains(next_agent, next_skill, visited.copy()))
    return steps
