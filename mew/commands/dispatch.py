"""mew dispatch — send a pure-generation task to a proxy agent or Z.ai GLM.

Providers:
  proxy  — LiteLLM proxy at localhost:4000 (DeepSeek agents)
  zai    — Z.ai GLM via Anthropic-compatible endpoint (GLM agents, no per-token billing)

Agent → provider routing (automatic):
  glm-*  agents → zai
  mew-*  agents → proxy

Exit codes:
  0 — success, response printed to stdout (or written to --write path)
  1 — usage error (bad args, empty prompt, missing task file, missing key)
  3 — proxy unavailable; caller should fall back to Claude
"""
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from mew.workspace import find_workspace_root
from mew.ledger import db as ledger_db
from mew.routing import heuristics as routing_heuristics
from mew.routing import blast_radius as blast_radius_mod
from mew.routing import complexity as complexity_mod
from mew.routing import capability as capability_mod


PROXY_URL = "http://localhost:4000/chat/completions"
ZAI_BASE_URL = "https://api.z.ai/api/anthropic"

# Exit code 3 = proxy unavailable — Claude's routing instinct detects this and retakes the task.
EXIT_PROXY_UNAVAILABLE = 3

# GLM model to use per agent.
_ZAI_MODEL_MAP: dict[str, str] = {
    "glm-code-reviewer": "glm-5.3",    # reasoning-always-on, best for review
    "glm-coder":         "glm-5-turbo", # agent-optimised, fast generation
    "glm-ideator":       "glm-5.2",    # broad ideation, 1M context
    "glm-critic":        "glm-5.2",    # structured critique, 1M context
}

_SYSTEM_PROMPTS: dict[str, str] = {
    # --- DeepSeek agents (proxy) ---
    "mew-coder-simple": (
        "You are a precise code generator. Output ONLY the requested code. "
        "No explanations, no markdown fences, no preamble or postamble. "
        "Follow the spec exactly. Match the language, style, and constraints given. "
        "If a function signature is provided, honour it exactly. "
        "If examples are given, match their style. "
        "Produce production-quality code: correct, clean, no debug prints."
    ),
    "mew-coder-reason": (
        "You are a precise code generator with strong reasoning capabilities. "
        "Reason through the problem step by step internally, then output ONLY the final code. "
        "No markdown fences, no preamble. Output starts with the first line of code. "
        "Match language, constraints, and signatures exactly as specified."
    ),
    # --- GLM agents (Z.ai) ---
    "glm-ideator": (
        "You are a creative product and feature ideation expert. "
        "When given a topic, explore it broadly: surface assumptions, identify "
        "opportunities and risks, propose concrete approaches, and highlight what "
        "is often overlooked. Be direct and opinionated. "
        "Aim for density over length — no filler, no generic advice."
    ),
    "glm-critic": (
        "You are a rigorous analytical critic. "
        "When given a position or analysis, find its weaknesses: gaps in reasoning, "
        "missing edge cases, weak assumptions, overlooked risks, and alternative "
        "interpretations. Be specific — reference the exact claims you are challenging. "
        "Propose what a stronger version of the argument would look like."
    ),
    "glm-code-reviewer": (
        "You are an expert code reviewer. Analyse the code provided for correctness, "
        "clarity, security issues, performance, and adherence to best practices. "
        "Structure your review exactly as:\n\n"
        "## Summary\n"
        "One paragraph — overall assessment.\n\n"
        "## Issues\n"
        "Bullet list. Each issue: severity (high/medium/low), location (file:line or function "
        "name), description, and suggested fix.\n\n"
        "## Suggestions\n"
        "Non-blocking improvements — style, naming, test coverage gaps.\n\n"
        "## Verdict\n"
        "Either: APPROVE or REQUEST CHANGES — one line, then one sentence why."
    ),
    "glm-coder": (
        "You are a precise code generator. Output ONLY the requested code. "
        "No explanations, no markdown fences, no preamble or postamble. "
        "Follow the spec exactly. Match the language, style, and constraints given. "
        "If a function signature is provided, honour it exactly. "
        "Produce production-quality code: correct, clean, no debug prints."
    ),
}


def run_dispatch(args) -> None:
    workspace_root = find_workspace_root()

    # --check: test proxy availability only
    if getattr(args, "check", False):
        if _proxy_is_up():
            print("proxy: reachable at http://localhost:4000")
            sys.exit(0)
        else:
            print("proxy: not reachable — run `bash proxy/start-proxy.sh` to start", file=sys.stderr)
            sys.exit(EXIT_PROXY_UNAVAILABLE)

    # Load the task prompt
    if args.task_file:
        task_path = Path(args.task_file)
        if not task_path.exists():
            print(f"Error: task file not found: {args.task_file}", file=sys.stderr)
            sys.exit(1)
        prompt = task_path.read_text(encoding="utf-8").strip()
    elif args.task:
        prompt = args.task.strip()
    else:
        print("Error: provide --task '<prompt>' or --task-file <path>", file=sys.stderr)
        sys.exit(1)

    if not prompt:
        print("Error: task prompt is empty.", file=sys.stderr)
        sys.exit(1)

    # Auto-select agent from prompt when not explicitly set
    agent = args.agent or _infer_agent(prompt)
    print(f"dispatch: agent → {agent}", file=sys.stderr)

    # Build message list
    messages = []
    if not getattr(args, "no_system", False):
        system_text = getattr(args, "system", None) or _SYSTEM_PROMPTS.get(agent)
        if system_text:
            messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": prompt})

    # Route: explicit --provider flag wins; otherwise infer from agent name
    provider = getattr(args, "provider", None) or ("zai" if agent.startswith("glm-") else "proxy")

    dispatch_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    t0 = time.monotonic()

    if provider == "zai":
        content, usage = _fetch_zai(agent, messages, workspace_root)
    else:
        content, usage = _fetch_proxy(agent, messages, workspace_root)

    duration_ms = int((time.monotonic() - t0) * 1000)

    # Phase 3: graph-aware routing metadata + ledger write (fire-and-forget)
    try:
        conn = ledger_db.connect(workspace_root)
        ledger_db.init(conn)
        task_hash = ledger_db._task_hash(agent, prompt)
        model_run = ledger_db.extract_model_self_report(content)
        silo = _detect_silo(workspace_root)
        project_lock = _read_active_project(workspace_root)

        # Cross-silo warning
        if project_lock and silo and silo not in project_lock:
            print(
                f"dispatch: WARNING — silo mismatch "
                f"(locked to '{project_lock}', dispatch silo '{silo}'). "
                "Cross-silo read recorded in ledger.",
                file=sys.stderr,
            )

        # Graph confidence check — emit fallback message when graph is unreliable
        graph_path = _project_graph_path(workspace_root, silo, project_lock)
        confidence_bucket = _read_confidence_bucket(workspace_root, silo, project_lock)
        if confidence_bucket in ("low", "insufficient"):
            print(
                f"dispatch: graph confidence {confidence_bucket}, "
                f"using default routing ({agent})",
                file=sys.stderr,
            )

        # Graph-aware blast-radius + complexity (fall back to keyword buckets when no graph)
        pred_radius_count, pred_radius_bucket = blast_radius_mod.compute(graph_path, prompt)
        complexity_score, _ = complexity_mod.compute(graph_path, prompt)

        # Routing rationale
        rationale = _build_rationale(agent, confidence_bucket, pred_radius_bucket, complexity_score)

        ledger_db.write_dispatch(
            conn,
            agent=agent,
            model_intended=_ZAI_MODEL_MAP.get(agent) if provider == "zai" else agent,
            model_actually_run=model_run,
            provider=provider,
            silo=silo,
            project_lock=project_lock,
            task_text=prompt,
            dispatch_ts=dispatch_ts,
            duration_ms=duration_ms,
            outcome_class="success",
            tokens_in=usage.get("input_tokens"),
            tokens_out=usage.get("output_tokens"),
            predicted_radius=pred_radius_count,
            complexity_score=complexity_score,
            confidence_bucket=confidence_bucket,
            routing_rationale=rationale,
        )
        ledger_db.reconcile_prediction(conn, task_hash, dispatch_ts, agent, model_run)
    except Exception:
        pass  # ledger must never crash the dispatch

    # Output
    write_path = getattr(args, "write", None)
    if write_path:
        out = Path(write_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"dispatch({provider}): wrote {len(content)} chars to {out}", file=sys.stderr)
    else:
        print(content)


# ---------------------------------------------------------------------------
# Agent inference — keyword scoring on the task prompt
# ---------------------------------------------------------------------------

# Signals that mean "look at existing code and give feedback"
_REVIEW_SIGNALS = {
    "review", "critique", "audit", "analyse", "analyze", "assess", "evaluate",
    "check", "inspect", "look at", "what's wrong", "what is wrong", "wrong with",
    "find bug", "find issue", "find bugs", "find issues",
    "security", "vulnerability", "vulnerabilities",
    "feedback", "is this correct", "is there a bug", "does this work",
    "any issues", "any problems", "improve this", "what do you think",
    "problem with", "problems with",
}

# Signals that mean "produce new code" — verbs only, no object nouns
# (nouns like "function", "class", "component" appear in review prompts too)
_CODER_SIGNALS = {
    "write", "implement", "create", "build", "generate", "make", "add",
    "refactor", "fix", "rewrite", "convert", "migrate", "update",
}


def _infer_agent(prompt: str) -> str:
    """Pick the best agent by scoring the prompt against known intent signals."""
    lower = prompt.lower()
    review_score = sum(1 for s in _REVIEW_SIGNALS if s in lower)
    coder_score  = sum(1 for s in _CODER_SIGNALS  if s in lower)
    return "glm-code-reviewer" if review_score > coder_score else "glm-coder"


# ---------------------------------------------------------------------------
# Z.ai provider — Anthropic-compatible endpoint, draws from Coding Plan quota
# ---------------------------------------------------------------------------

def _fetch_zai(agent: str, messages: list, workspace_root: Path | None) -> str:
    api_key = _load_zai_key(workspace_root)
    if not api_key:
        print(
            "Error: Z_AI_KEY not set. Run:\n"
            "  mew secret set Z_AI_KEY --scope workspace",
            file=sys.stderr,
        )
        sys.exit(1)

    model = _ZAI_MODEL_MAP.get(agent, "glm-5.2")

    # Anthropic messages format: system is a top-level field, not a message role
    system_text = None
    user_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            user_messages.append(msg)

    body: dict = {"model": model, "max_tokens": 8096, "messages": user_messages}
    if system_text:
        body["system"] = system_text

    payload = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    url = f"{ZAI_BASE_URL}/v1/messages"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Error: Z.ai returned HTTP {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: could not reach Z.ai endpoint: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: unexpected response from Z.ai: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract text blocks only — GLM-5.3 may return thinking blocks too
    try:
        blocks = resp_body["content"]
        text = "\n".join(b["text"] for b in blocks if b.get("type") == "text")
    except (KeyError, TypeError):
        print(f"Error: malformed Z.ai response: {json.dumps(resp_body, indent=2)}", file=sys.stderr)
        sys.exit(1)

    usage = resp_body.get("usage", {})
    return text, {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens")}


def _load_zai_key(workspace_root: Path | None) -> str | None:
    if workspace_root is None:
        return None
    env_file = workspace_root / "mewvault" / "secrets" / "workspace.env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("Z_AI_KEY="):
            return line.split("=", 1)[1].strip()
    return None


# ---------------------------------------------------------------------------
# LiteLLM proxy provider — DeepSeek agents
# ---------------------------------------------------------------------------

def _fetch_proxy(agent: str, messages: list, workspace_root: Path | None) -> str:
    api_key = _load_proxy_key(workspace_root)

    payload = json.dumps({
        "model": agent,
        "messages": messages,
        "stream": False,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(PROXY_URL, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError:
        print("DISPATCH_UNAVAILABLE: proxy not reachable — Claude should handle this task directly.", file=sys.stderr)
        print("To enable DeepSeek routing: bash proxy/start-proxy.sh (optional)", file=sys.stderr)
        sys.exit(EXIT_PROXY_UNAVAILABLE)
    except json.JSONDecodeError as e:
        print(f"Error: unexpected response from proxy: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print(f"Error: malformed proxy response: {json.dumps(body, indent=2)}", file=sys.stderr)
        sys.exit(1)

    usage = body.get("usage", {})
    return content, {"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens")}


def _proxy_is_up() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:4000/health", timeout=3):
            return True
    except Exception:
        return False


def _load_proxy_key(workspace_root: Path | None) -> str | None:
    if workspace_root is None:
        return None
    env_file = workspace_root / "mewvault" / "secrets" / "workspace.env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("MEW_PROXY_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def _project_graph_path(workspace_root: Path | None, silo: str | None,
                        project_lock: str | None) -> Path:
    """Project-first graph resolution: locked project → silo → /dev/null."""
    if workspace_root and project_lock:
        project_graph = workspace_root / project_lock / "graphify-out" / "graph.json"
        if project_graph.exists():
            return project_graph
    if workspace_root and silo:
        silo_graph = workspace_root / silo / "graphify-out" / "graph.json"
        if silo_graph.exists():
            return silo_graph
    return Path("/dev/null")


def _read_confidence_bucket(workspace_root: Path | None, silo: str | None,
                            project_lock: str | None = None) -> str:
    """Read confidence bucket — project-level first, silo fallback."""
    for rel in filter(None, [project_lock, (silo or "")]):
        conf_path = workspace_root / rel / "graphify-out" / "confidence.json" if workspace_root else None
        if conf_path and conf_path.exists():
            try:
                import json
                return json.loads(conf_path.read_text(encoding="utf-8")).get("bucket", "insufficient")
            except Exception:
                pass
    return "insufficient"


def _build_rationale(agent: str, confidence: str, radius: str, complexity: float) -> str:
    return (
        f"agent={agent} confidence={confidence} "
        f"radius={radius} complexity={complexity:.1f}"
    )


def _read_active_project(workspace_root: Path | None) -> str | None:
    if workspace_root is None:
        return None
    lock = workspace_root / "mewvault" / ".active-project"
    if lock.exists():
        return lock.read_text(encoding="utf-8").strip() or None
    return None


_SILO_DIRS = {
    "software-projects", "game-lab", "design-studio",
    "wiki", "career-studio", "learn-lab", "idea-hub", "mewvault",
}


def _detect_silo(workspace_root: Path | None) -> str | None:
    if workspace_root is None:
        return None
    try:
        cwd = Path.cwd()
        for part in cwd.parts:
            if part in _SILO_DIRS:
                return part
    except Exception:
        pass
    return None
