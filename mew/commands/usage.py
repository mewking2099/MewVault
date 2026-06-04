"""mew usage — show Claude auth status and open the usage dashboard."""
import json
import subprocess
import sys
import platform
from pathlib import Path


def run_usage(args) -> None:
    # ── Auth status ────────────────────────────────────────────────────────────
    print("Claude account\n" + "─" * 40)
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                logged_in = data.get("loggedIn", False)
                status_icon = "✓" if logged_in else "✗"
                print(f"  Status        {status_icon}  {'logged in' if logged_in else 'NOT logged in — mew harness will fail'}")
                if logged_in:
                    print(f"  Email         {data.get('email', '—')}")
                    print(f"  Org           {data.get('orgName', '—')}")
                    print(f"  Subscription  {data.get('subscriptionType', '—')}")
                    print(f"  Auth method   {data.get('authMethod', '—')}")
            except json.JSONDecodeError:
                print(result.stdout.strip())
        else:
            print("  Could not get auth status — run: claude auth login")
    except FileNotFoundError:
        print("  claude CLI not found. Install from: https://claude.ai/code")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("  claude auth status timed out")

    # ── Usage note ────────────────────────────────────────────────────────────
    print()
    print("Usage limits")
    print("─" * 40)
    print("  Anthropic does not expose quota via CLI for subscription accounts.")
    print("  Check remaining usage in your browser:")
    print()
    print("  claude.ai/settings → Usage")
    print("  console.anthropic.com → Usage  (API / team billing)")

    # ── Open browser ──────────────────────────────────────────────────────────
    if getattr(args, "open", False):
        url = "https://claude.ai/settings"
        print(f"\n  Opening {url} …")
        try:
            if platform.system() == "Darwin":
                subprocess.run(["open", url], check=True)
            elif platform.system() == "Windows":
                subprocess.run(["start", url], shell=True, check=True)
            else:
                subprocess.run(["xdg-open", url], check=True)
        except Exception as e:
            print(f"  Could not open browser: {e}")

    print()
