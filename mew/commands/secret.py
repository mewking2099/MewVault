"""mew secret — manage secrets in mewvault/secrets/<scope>.env."""
import sys
import getpass
from pathlib import Path
from mew.workspace import find_workspace_root
from mew.utils import secure_file


def run_secret(args) -> None:
    workspace_root = find_workspace_root()
    if not workspace_root:
        print("Error: not inside a MewVault workspace.", file=sys.stderr)
        sys.exit(1)

    scope = args.scope or "workspace"
    secrets_dir = workspace_root / "mewvault" / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    env_file = secrets_dir / f"{scope}.env"

    if args.action == "set":
        if not args.key:
            print("Error: key name required. Usage: mew secret set <KEY> [--scope <project>]")
            sys.exit(1)
        try:
            value = getpass.getpass(f"Value for {args.key} (input hidden): ")
        except KeyboardInterrupt:
            print("\nAborted.")
            return
        _set_secret(env_file, args.key, value)
        secure_file(env_file)
        print(f"Stored {args.key} in secrets/{scope}.env")

    elif args.action == "get":
        if not args.key:
            print("Error: key name required.")
            sys.exit(1)
        if _secret_exists(env_file, args.key):
            print(f"{args.key} is set in secrets/{scope}.env")
        else:
            print(f"Secret not found: {args.key} in scope '{scope}'")
            sys.exit(1)

    elif args.action == "list":
        keys = _list_keys(env_file)
        if keys:
            print(f"Secrets in scope '{scope}':")
            for k in keys:
                print(f"  {k}")
        else:
            print(f"No secrets in scope '{scope}'.")

    elif args.action == "rotate":
        if not args.key:
            print("Error: key name required.")
            sys.exit(1)
        if not _secret_exists(env_file, args.key):
            print(f"Warning: {args.key} not found in scope '{scope}' — will create it.")
        try:
            value = getpass.getpass(f"New value for {args.key} (input hidden): ")
        except KeyboardInterrupt:
            print("\nAborted.")
            return
        _set_secret(env_file, args.key, value)
        secure_file(env_file)
        print(f"Rotated {args.key} in secrets/{scope}.env")


def _set_secret(env_file: Path, key: str, value: str) -> None:
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"{key}={value}")
    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _secret_exists(env_file: Path, key: str) -> bool:
    if not env_file.exists():
        return False
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return True
    return False


def _list_keys(env_file: Path) -> list[str]:
    if not env_file.exists():
        return []
    keys = []
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            keys.append(stripped.split("=", 1)[0])
    return keys
