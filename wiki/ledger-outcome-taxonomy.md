# Ledger Outcome Taxonomy

_Phase 1 reference — see plan §A-5_

## `outcome_class` values

| Value | Meaning |
|---|---|
| `success` | Agent produced a usable output; no exit code error |
| `failure` | Agent exited non-zero, or response was empty / malformed |
| `timeout` | Request exceeded the provider timeout threshold |
| `cancelled` | Caller cancelled before a response was received |

Rules:
- `outcome_class` is always set at write time — never left NULL for completed rows.
- A row with no outcome yet (e.g., async dispatch) is not written until the outcome is known.
- `success` does not imply correctness — it means the transport layer succeeded. Correctness lives in `verification_mode`.

## `verification_mode` values (ranked by strength)

| Rank | Value | Meaning |
|---|---|---|
| 1 | `test_pass` | Automated test suite green after applying the output |
| 2 | `graph_diff_match` | graphify diff before/after matches the task intent |
| 3 | `human_accept` | Owner reviewed and explicitly accepted the output |
| 4 | `self_report` | Agent's `[model=...]` self-report is present and parseable |

Rules:
- Only the strongest mode achieved is recorded.
- `self_report` is the fallback — it merely confirms the model ran and formatted its response. It says nothing about correctness.
- Phase 2 gates require at least `human_accept` or `test_pass` to count toward routing confidence scores.

## Predicted vs actual columns (§A-5)

`predicted_agent` and `predicted_model` are always distinct from `agent` and `model_actually_run`.

- Phase 1: `predicted_*` columns are NULL (routing is not yet live).
- Phase 2: shadow-mode routing populates them; the delta between predicted and actual is the training signal.
- Never conflate predicted with actual in queries — treat them as separate event streams.
