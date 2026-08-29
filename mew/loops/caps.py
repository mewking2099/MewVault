"""Loop caps — max_ticks and max_no_progress_ticks per loop type.

Loaded from ~/.mew/loop-caps.yaml if present; otherwise hard defaults apply.
Changing caps bumps graph_epoch (document in wiki/loop-primitives.md).
"""
from __future__ import annotations

import json
from pathlib import Path

_DEFAULTS: dict = {
    "default_max_ticks": 8,
    "max_no_progress_ticks": 3,
    "loop_type_caps": {
        "spec_build_verify":   8,
        "plan_approve_execute": 6,
        "idea_lifecycle":      12,
        "wrap_prime":          4,
    },
}

_CAPS_FILE = Path.home() / ".mew" / "loop-caps.yaml"


def load() -> dict:
    """Return merged caps: file values override defaults."""
    if not _CAPS_FILE.exists():
        return _DEFAULTS.copy()
    try:
        import yaml  # type: ignore[import]
        overrides = yaml.safe_load(_CAPS_FILE.read_text(encoding="utf-8")) or {}
    except ImportError:
        # yaml not installed — try JSON fallback
        try:
            overrides = json.loads(_CAPS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return _DEFAULTS.copy()
    except Exception:
        return _DEFAULTS.copy()

    merged = _DEFAULTS.copy()
    merged["default_max_ticks"] = overrides.get("default_max_ticks", merged["default_max_ticks"])
    merged["max_no_progress_ticks"] = overrides.get("max_no_progress_ticks", merged["max_no_progress_ticks"])
    if "loop_type_caps" in overrides:
        merged["loop_type_caps"].update(overrides["loop_type_caps"])
    return merged


def max_ticks(loop_type: str, caps: dict | None = None) -> int:
    if caps is None:
        caps = load()
    return caps["loop_type_caps"].get(loop_type, caps["default_max_ticks"])


def max_no_progress(caps: dict | None = None) -> int:
    if caps is None:
        caps = load()
    return caps["max_no_progress_ticks"]
