"""Cross-platform utilities: permissions, git, frontmatter, prompts."""
import os
import sys
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file. Returns (data, body)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}, ""

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        data = {}

    return data, parts[2].strip()


def write_frontmatter(path: Path, frontmatter: dict, body: str = "") -> None:
    """Write a markdown file with YAML frontmatter."""
    fm_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
    content = f"---\n{fm_str}\n---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def secure_file(path: Path) -> None:
    """Restrict a file or directory to owner read/write only."""
    if sys.platform == "win32":
        username = os.environ.get("USERNAME", "")
        if username:
            subprocess.run(
                ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username}:(R,W)"],
                capture_output=True,
            )
    else:
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass


def git_init(path: Path) -> bool:
    """Initialize a git repository. Returns True on success."""
    result = subprocess.run(
        ["git", "init", str(path)],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def git_is_available() -> bool:
    """Return True if git is on PATH."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def confirm(prompt: str, default: bool = False) -> bool:
    """Prompt for yes/no. Returns True for yes."""
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        try:
            answer = input(f"{prompt} {hint} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return default
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
