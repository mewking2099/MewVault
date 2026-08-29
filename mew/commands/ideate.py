"""mew ideate — dual-model research and ideation loop.

Flow:
  Round 0  — parallel first pass: GLM-5.2 + Claude Opus
  Round 1  — cross-critique: each model critiques the other's output
  Round 2  — (optional, --rounds 2) each model responds to the critique it received
  Synthesis — Claude Opus synthesises the full transcript into a final recommendation

Output:
  mewvault/ideation/<slug>/synthesis.md   — final recommendation
  mewvault/ideation/<slug>/transcript.md  — full debate transcript
"""
import sys
import json
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from mew.workspace import find_workspace_root
from mew.commands.dispatch import _fetch_zai, _SYSTEM_PROMPTS


# ---------------------------------------------------------------------------
# Opus subprocess
# ---------------------------------------------------------------------------

def _fetch_opus(prompt: str) -> str:
    """Spawn claude --print --model opus and return the text result."""
    result = subprocess.run(
        ["claude", "--print", "--model", "opus",
         "--output-format", "json", "--no-session-persistence"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=240,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude opus subprocess failed (exit {result.returncode}):\n{result.stderr}"
        )
    try:
        body = json.loads(result.stdout)
        return body["result"]
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Unexpected opus output: {e}\n{result.stdout[:500]}")


# ---------------------------------------------------------------------------
# GLM helpers (thin wrappers over dispatch._fetch_zai)
# ---------------------------------------------------------------------------

def _fetch_glm(agent: str, prompt: str, workspace_root: Path | None) -> str:
    messages = []
    system = _SYSTEM_PROMPTS.get(agent)
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    content, _usage = _fetch_zai(agent, messages, workspace_root)
    return content


# ---------------------------------------------------------------------------
# Transcript helpers
# ---------------------------------------------------------------------------

def _format_transcript(entries: list[tuple[str, str]]) -> str:
    parts = []
    for label, content in entries:
        parts.append(f"## {label}\n\n{content.strip()}")
    return "\n\n---\n\n".join(parts)


def _slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:60]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_ideate(args) -> None:
    workspace_root = find_workspace_root()
    topic: str = args.topic

    # Load any prior context files
    context_block = ""
    context_files = getattr(args, "context_file", None) or []
    if context_files:
        parts = []
        for cf in context_files:
            p = Path(cf)
            if not p.exists():
                print(f"ideate: warning — context file not found: {cf}", file=sys.stderr)
                continue
            parts.append(f"### {p.name}\n{p.read_text(encoding='utf-8').strip()}")
        if parts:
            context_block = (
                "Prior research context (already established — do not rehash, build on it):\n\n"
                + "\n\n---\n\n".join(parts)
                + "\n\n"
            )

    print(f"ideate: topic → {topic}", file=sys.stderr)
    if context_block:
        print(f"ideate: context files → {len(context_files)} loaded", file=sys.stderr)
    print("ideate: running first pass → critique → synthesis", file=sys.stderr)

    transcript: list[tuple[str, str]] = []

    # ------------------------------------------------------------------
    # Round 0 — parallel first passes
    # ------------------------------------------------------------------
    print("\nideate: [round 0] first pass — GLM-5.2 + Claude Opus in parallel…", file=sys.stderr)

    first_pass_prompt = (
        f"{context_block}"
        f"Topic: {topic}\n\n"
        "Explore this topic for product/feature ideation. Cover:\n"
        "- Core opportunity and what makes it worth pursuing\n"
        "- Key assumptions being made\n"
        "- Concrete approaches or solutions\n"
        "- Risks and what could go wrong\n"
        "- What is commonly overlooked\n\n"
        "Be direct and specific. No generic advice."
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        glm_r0_fut  = pool.submit(_fetch_glm, "glm-ideator", first_pass_prompt, workspace_root)
        opus_r0_fut = pool.submit(_fetch_opus, first_pass_prompt)
        glm_r0  = glm_r0_fut.result()
        opus_r0 = opus_r0_fut.result()

    transcript.append(("GLM-5.2 — Round 0 (First Pass)", glm_r0))
    transcript.append(("Claude Opus — Round 0 (First Pass)", opus_r0))
    print("ideate: [round 0] done", file=sys.stderr)

    # ------------------------------------------------------------------
    # Round 1 — cross-critique
    # ------------------------------------------------------------------
    print("ideate: [round 1] cross-critique — each model critiques the other…", file=sys.stderr)

    glm_critique_prompt = (
        f"Critique the following analysis on the topic: {topic}\n\n"
        f"--- ANALYSIS TO CRITIQUE ---\n{opus_r0}\n---\n\n"
        "Find gaps in reasoning, weak assumptions, missing angles, and overlooked risks. "
        "Be specific — reference the exact claims you are challenging. "
        "Propose what a stronger version would look like."
    )
    opus_critique_prompt = (
        f"Critique the following analysis on the topic: {topic}\n\n"
        f"--- ANALYSIS TO CRITIQUE ---\n{glm_r0}\n---\n\n"
        "Find gaps in reasoning, weak assumptions, missing angles, and overlooked risks. "
        "Be specific — reference the exact claims you are challenging. "
        "Propose what a stronger version would look like."
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        glm_r1_fut  = pool.submit(_fetch_glm, "glm-critic", glm_critique_prompt, workspace_root)
        opus_r1_fut = pool.submit(_fetch_opus, opus_critique_prompt)
        glm_r1  = glm_r1_fut.result()
        opus_r1 = opus_r1_fut.result()

    transcript.append(("GLM-5.2 — Round 1 (Critique of Opus)", glm_r1))
    transcript.append(("Claude Opus — Round 1 (Critique of GLM)", opus_r1))
    print("ideate: [round 1] done", file=sys.stderr)

    # ------------------------------------------------------------------
    # Synthesis — Opus reads the full transcript and writes the final output
    # ------------------------------------------------------------------
    print("ideate: [synthesis] Claude Opus synthesising…", file=sys.stderr)

    full_transcript = _format_transcript(transcript)
    synthesis_prompt = (
        f"Topic: {topic}\n\n"
        f"The following is a structured debate between GLM-5.2 and Claude Opus:\n\n"
        f"{full_transcript}\n\n"
        "Synthesise the best insights from both models into a final recommendation. Structure as:\n\n"
        "## Key Insights\n"
        "The strongest ideas that emerged, regardless of which model raised them.\n\n"
        "## Resolved Disagreements\n"
        "Where the models disagreed and what the right position is.\n\n"
        "## Open Questions\n"
        "What remains genuinely uncertain or needs more investigation.\n\n"
        "## Concrete Next Steps\n"
        "Specific, actionable recommendations ordered by priority.\n\n"
        "Be direct. Cut anything that is generic or obvious."
    )

    synthesis = _fetch_opus(synthesis_prompt)
    print("ideate: [synthesis] done", file=sys.stderr)

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    slug = _slugify(topic)
    date_str = datetime.now().strftime("%Y-%m-%d")

    if getattr(args, "write_dir", None):
        out_dir = Path(args.write_dir)
    elif workspace_root:
        out_dir = workspace_root / "mewvault" / "ideation" / f"{date_str}-{slug}"
    else:
        out_dir = Path(f"ideation/{date_str}-{slug}")

    out_dir.mkdir(parents=True, exist_ok=True)

    synthesis_path  = out_dir / "synthesis.md"
    transcript_path = out_dir / "transcript.md"

    synthesis_path.write_text(
        f"# {topic}\n_Generated: {date_str}_\n\n{synthesis}",
        encoding="utf-8",
    )
    transcript_path.write_text(
        f"# {topic} — Debate Transcript\n_Generated: {date_str}_\n\n{full_transcript}",
        encoding="utf-8",
    )

    # Print synthesis to stdout
    print(f"\n{'=' * 60}")
    print(synthesis)
    print(f"\n{'=' * 60}")
    print(f"synthesis : {synthesis_path}", file=sys.stderr)
    print(f"transcript: {transcript_path}", file=sys.stderr)
