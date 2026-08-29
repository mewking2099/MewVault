"""Fixed termination predicates for the four instrumented loop types (Phase 4).

Each predicate function takes a context dict and returns (is_met, reason, state_snapshot).
State snapshot is JSON-serializable — written into loop_tick.predicate_state each tick.

RULE: Phase 4 ships ONLY these four fixed loops. Fuzzy-predicate loops are deferred to Phase 5.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


# ── dispatch to the right predicate ──────────────────────────────────────────

LOOP_TYPES = frozenset({
    "spec_build_verify",
    "plan_approve_execute",
    "idea_lifecycle",
    "wrap_prime",
})


def evaluate(loop_type: str, ctx: dict) -> tuple[bool, str, dict]:
    """Return (is_met, reason, state_snapshot) for the given loop type and context.

    ctx keys vary by loop type — see each predicate for the required keys.
    Missing keys result in predicate returning (False, 'context incomplete', ...).
    """
    fn = {
        "spec_build_verify":   _spec_build_verify,
        "plan_approve_execute": _plan_approve_execute,
        "idea_lifecycle":       _idea_lifecycle,
        "wrap_prime":           _wrap_prime,
    }.get(loop_type)
    if fn is None:
        return False, f"unknown loop type: {loop_type}", {}
    return fn(ctx)


# ── spec_build_verify ─────────────────────────────────────────────────────────
# Predicate met: all acceptance criteria in the spec have a passing test.
# Detection: looks for checked `- [x]` items in spec + a `.tests-pass` marker
#            OR `outcome_class = test_pass` in the loop's ledger dispatches.

def _spec_build_verify(ctx: dict) -> tuple[bool, str, dict]:
    spec_path = _path(ctx.get("spec_file"))
    tests_pass_marker = _path(ctx.get("tests_pass_marker"))
    ledger_has_test_pass = bool(ctx.get("ledger_test_pass_count", 0))

    state: dict = {}

    # Count acceptance criteria in spec
    total_criteria = 0
    met_criteria = 0
    if spec_path and spec_path.exists():
        text = spec_path.read_text(encoding="utf-8")
        total_criteria = len(re.findall(r"^- \[[ x]\]", text, re.MULTILINE))
        met_criteria   = len(re.findall(r"^- \[x\]", text, re.MULTILINE | re.IGNORECASE))

    state["criteria_total"] = total_criteria
    state["criteria_met"]   = met_criteria

    # Tests passing: marker file OR ledger evidence
    tests_passing = (
        (tests_pass_marker and tests_pass_marker.exists())
        or ledger_has_test_pass
    )
    state["tests_passing"] = tests_passing

    if total_criteria > 0 and met_criteria >= total_criteria and tests_passing:
        return True, "predicate_met", state
    if not tests_passing:
        return False, f"tests not passing (criteria {met_criteria}/{total_criteria})", state
    return False, f"criteria incomplete ({met_criteria}/{total_criteria})", state


# ── plan_approve_execute ──────────────────────────────────────────────────────
# Predicate met: plan_approved: true in Project_Status.md AND all
# deliverable items in plan.md are checked.

def _plan_approve_execute(ctx: dict) -> tuple[bool, str, dict]:
    project_status_path = _path(ctx.get("project_status_file"))
    plan_path           = _path(ctx.get("plan_file"))

    state: dict = {}

    plan_approved = False
    if project_status_path and project_status_path.exists():
        text = project_status_path.read_text(encoding="utf-8")
        plan_approved = bool(re.search(r"plan_approved\s*:\s*true", text, re.IGNORECASE))
    state["plan_approved"] = plan_approved

    total_deliverables = 0
    done_deliverables  = 0
    if plan_path and plan_path.exists():
        text = plan_path.read_text(encoding="utf-8")
        total_deliverables = len(re.findall(r"^- \[[ x]\]", text, re.MULTILINE))
        done_deliverables  = len(re.findall(r"^- \[x\]", text, re.MULTILINE | re.IGNORECASE))
    state["deliverables_total"] = total_deliverables
    state["deliverables_done"]  = done_deliverables

    if plan_approved and total_deliverables > 0 and done_deliverables >= total_deliverables:
        return True, "predicate_met", state
    if not plan_approved:
        return False, "plan_approved not set", state
    return False, f"deliverables incomplete ({done_deliverables}/{total_deliverables})", state


# ── idea_lifecycle ────────────────────────────────────────────────────────────
# Predicate met: status ∈ {promoted, archived} in the idea's status.md.

def _idea_lifecycle(ctx: dict) -> tuple[bool, str, dict]:
    status_path = _path(ctx.get("idea_status_file"))

    state: dict = {}

    if not status_path or not status_path.exists():
        state["status"] = "unknown"
        return False, "idea status.md not found", state

    text = status_path.read_text(encoding="utf-8")
    m = re.search(r"^status\s*:\s*(\w+)", text, re.MULTILINE | re.IGNORECASE)
    status = m.group(1).lower() if m else "unknown"
    state["status"] = status

    if status in ("promoted", "archived"):
        return True, "predicate_met", state
    return False, f"status={status} (need promoted or archived)", state


# ── wrap_prime ────────────────────────────────────────────────────────────────
# Predicate met: log.md updated this session AND next-session brief exists.

def _wrap_prime(ctx: dict) -> tuple[bool, str, dict]:
    log_path   = _path(ctx.get("log_file"))
    brief_path = _path(ctx.get("brief_file"))
    session_start_ts = float(ctx.get("session_start_ts", 0.0))  # POSIX timestamp

    state: dict = {}

    log_updated = False
    if log_path and log_path.exists():
        log_mtime = log_path.stat().st_mtime
        log_updated = log_mtime >= session_start_ts
    state["log_updated"] = log_updated

    brief_exists = bool(brief_path and brief_path.exists())
    state["brief_exists"] = bool(brief_exists)
    if brief_path:
        state["brief_path"] = str(brief_path)

    if log_updated and brief_exists:
        return True, "predicate_met", state
    reasons = []
    if not log_updated:
        reasons.append("log.md not updated this session")
    if not brief_exists:
        reasons.append("brief file not written")
    return False, "; ".join(reasons), state


# ── helpers ───────────────────────────────────────────────────────────────────

def _path(val) -> Path | None:
    return Path(val) if val else None
