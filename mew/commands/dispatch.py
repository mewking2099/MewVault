"""mew dispatch — send a pure-generation task to a LiteLLM proxy agent.

Exit codes:
  0 — success, response printed to stdout
  1 — usage error (bad args, empty prompt, missing task file)
  3 — proxy unavailable; caller should fall back to Claude
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from mew.workspace import find_workspace_root


PROXY_URL = "http://localhost:4000/chat/completions"

# Exit code 3 = proxy unavailable. Distinct from exit 1 (usage error) so
# Claude's routing instinct can detect it and retake the task directly.
EXIT_PROXY_UNAVAILABLE = 3


def run_dispatch(args) -> None:
    workspace_root = find_workspace_root()

    # --check: just test proxy availability, exit 0 if up, 3 if down
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

    api_key = _load_proxy_key(workspace_root)
    agent = args.agent or "mew-coder-simple"

    payload = json.dumps({
        "model": agent,
        "messages": [{"role": "user", "content": prompt}],
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
        # Exit 3 = proxy unavailable. Claude's routing instinct treats this as
        # "retake the task directly" rather than a hard error.
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

    print(content)


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
