"""mew update — one-command, safe engine update.

Does what `git pull` alone cannot:
  1. Pre-flight: stashes uncommitted personal files (log.md, Project_Status.md,
     instincts/) so the pull can never conflict, and restores them after.
  2. git pull --ff-only (refuses to merge — divergent local history is surfaced,
     never auto-resolved).
  3. pip install -e .  (new commands become available)
  4. mew harness install  (new hooks get registered — a pull alone leaves them dead)
  5. mew doctor --quiet  (verifies the result)

Projects, mewwiki, and machine state live outside this repo — an update can
never touch them.
"""
import subprocess
import sys
from pathlib import Path

MEWVAULT_DIR = Path(__file__).parent.parent.parent.resolve()


def _run(cmd, check=True, **kw):
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=MEWVAULT_DIR, check=check, **kw)


def run_update(args) -> None:
    print("\nMewVault update\n")

    # 1. Pre-flight: stash local modifications so pull cannot conflict
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=MEWVAULT_DIR, capture_output=True, text=True,
    ).stdout.strip()
    stashed = False
    if dirty:
        print("  Local changes detected (personal files like log.md are normal):")
        for line in dirty.splitlines()[:8]:
            print(f"    {line}")
        _run(["git", "stash", "push", "-m", "mew-update-autostash"])
        stashed = True
        print("  → stashed; will restore after pull\n")

    # 2. Pull, fast-forward only
    try:
        _run(["git", "pull", "--ff-only"])
    except subprocess.CalledProcessError:
        print("\n  Pull failed (diverged history or network).", file=sys.stderr)
        if stashed:
            _run(["git", "stash", "pop"], check=False)
            print("  Local changes restored. Resolve manually, then re-run mew update.", file=sys.stderr)
        sys.exit(1)

    # 3. Restore personal files
    if stashed:
        result = _run(["git", "stash", "pop"], check=False)
        if result.returncode != 0:
            print("\n  ⚠ Your local changes conflict with the update (rare).")
            print("  They are safe in the stash: git stash show -p | git checkout --theirs …")
            print("  Or ask Claude: 'resolve the mew update stash conflict'.")

    # 4. Reinstall package (new/renamed commands)
    _run([sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"], check=False)

    # 5. Re-register hooks (new hook files/events are dead until registered)
    _run([sys.executable, "mew.py", "harness", "install"], check=False)

    # 6. Verify
    print("\n  Verifying with mew doctor …\n")
    doctor = _run([sys.executable, "mew.py", "doctor", "--quiet"], check=False)
    if doctor.returncode == 0:
        print("\n  Update complete — all checks green.\n")
    else:
        print("\n  Update applied, but doctor found issues above — fix before working.\n")
