"""Phase 2 routing heuristics — keyword-based prediction only.

These are fixed heuristics, not learned weights. Any change bumps graph_epoch.
See wiki/routing-heuristics.md for the versioned weight table.
"""
from __future__ import annotations

import re

# ── agent prediction ──────────────────────────────────────────────────────────
# Mirrors dispatch._REVIEW_SIGNALS / _CODER_SIGNALS — keep in sync.

_REVIEW_SIGNALS = {
    "review", "critique", "audit", "analyse", "analyze", "assess", "evaluate",
    "check", "inspect", "look at", "what's wrong", "what is wrong", "wrong with",
    "find bug", "find issue", "find bugs", "find issues",
    "security", "vulnerability", "vulnerabilities",
    "feedback", "is this correct", "is there a bug", "does this work",
    "any issues", "any problems", "improve this", "what do you think",
    "problem with", "problems with",
}

_CODER_SIGNALS = {
    "write", "implement", "create", "build", "generate", "make", "add",
    "refactor", "fix", "rewrite", "convert", "migrate", "update",
}

_AGENT_MODEL_MAP = {
    "glm-code-reviewer": "glm-5.3",
    "glm-coder":         "glm-5-turbo",
}


def predict_agent(prompt: str) -> str:
    lower = prompt.lower()
    review = sum(1 for s in _REVIEW_SIGNALS if s in lower)
    coder  = sum(1 for s in _CODER_SIGNALS  if s in lower)
    return "glm-code-reviewer" if review > coder else "glm-coder"


def predict_model(agent: str) -> str:
    return _AGENT_MODEL_MAP.get(agent, "unknown")


# ── blast-radius bucket ───────────────────────────────────────────────────────
# Signals that suggest wide blast radius (many files likely touched).

_LARGE_RADIUS_SIGNALS = {
    "migrate", "migration", "refactor", "redesign", "rename", "move",
    "delete", "remove all", "restructure", "rearchitect", "replace",
    "upgrade", "downgrade", "breaking change",
}

_SMALL_RADIUS_SIGNALS = {
    "fix", "bugfix", "typo", "comment", "review", "check", "inspect",
    "explain", "describe", "what is", "how does", "show me",
}


def predict_blast_radius(prompt: str) -> str:
    """Return 'small' | 'medium' | 'large' based on keyword signals."""
    lower = prompt.lower()
    large = sum(1 for s in _LARGE_RADIUS_SIGNALS if s in lower)
    small = sum(1 for s in _SMALL_RADIUS_SIGNALS if s in lower)
    if large > 0 and large >= small:
        return "large"
    if small > 0 and small > large:
        return "small"
    return "medium"


# ── complexity bucket ─────────────────────────────────────────────────────────
# Proxy: task text length + multi-step signal words.

_MULTI_STEP_SIGNALS = {
    "then", "and then", "after that", "also", "additionally", "finally",
    "step", "phase", "first", "second", "third",
    "implement and", "create and", "build and", "test and",
}


def predict_complexity(prompt: str) -> str:
    """Return 'simple' | 'moderate' | 'complex'."""
    lower = prompt.lower()
    word_count = len(prompt.split())
    multi = sum(1 for s in _MULTI_STEP_SIGNALS if s in lower)

    if word_count > 120 or multi >= 3:
        return "complex"
    if word_count > 40 or multi >= 1:
        return "moderate"
    return "simple"
