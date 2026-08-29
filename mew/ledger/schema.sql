-- MewVault dispatch ledger schema
-- Phase 1: graph-loop-engineering plan
-- Storage: SQLite + WAL. Kuzu migration trigger: see plan §A-3.
-- Never edit rows. Ledger is append-only.

-- ── epoch tracking ────────────────────────────────────────────────────────────
-- graph_epoch bumps when: graphify graph is rebuilt, schema migrates, or routing
-- heuristics change. Pins routing decisions so analysis can filter by era.

CREATE TABLE IF NOT EXISTS schema_epoch (
    epoch        INTEGER PRIMARY KEY,
    applied_at   TEXT    NOT NULL,  -- ISO 8601
    description  TEXT
);

-- Seed epoch 1 if table is empty
INSERT OR IGNORE INTO schema_epoch (epoch, applied_at, description)
VALUES (1, datetime('now'), 'initial schema');

-- ── dispatch rows ─────────────────────────────────────────────────────────────
-- Every mew dispatch call (ZAI, proxy, or future paths) writes one row.
-- Composite PK: task_hash disambiguates content; graph_epoch pins era;
-- dispatch_ts makes the triple unique even for identical prompts.

CREATE TABLE IF NOT EXISTS dispatch (
    -- PK (non-negotiable — §A-4)
    task_hash           TEXT    NOT NULL,   -- sha256(agent:prompt[:500])[:16]
    graph_epoch         INTEGER NOT NULL,
    dispatch_ts         TEXT    NOT NULL,   -- ISO 8601, microsecond precision

    -- agent & model
    agent               TEXT    NOT NULL,   -- e.g. glm-code-reviewer, mew-coder-simple
    model_intended      TEXT,               -- from _ZAI_MODEL_MAP / CLAUDE.md table
    model_actually_run  TEXT,               -- parsed from [model=...] self-report
    provider            TEXT,               -- anthropic | zai | proxy

    -- context
    silo                TEXT,               -- software-projects | game-lab | etc.
    project_lock        TEXT,               -- .active-project value at dispatch time
    parent_dispatch_ts  TEXT,               -- set for nested Agent() calls

    -- task (truncated to avoid bloating the DB)
    task_text           TEXT,               -- prompt[:500]

    -- usage
    tokens_in           INTEGER,
    tokens_out          INTEGER,
    cost_usd            REAL,
    duration_ms         INTEGER,

    -- outcome (§A-5: predicted and actual are always distinct columns)
    outcome_class       TEXT,               -- success | failure | timeout | cancelled
    verification_mode   TEXT,               -- test_pass | graph_diff_match | human_accept | self_report
    tools_used          TEXT,               -- JSON array e.g. '["Bash","Read"]'

    -- routing shadow-mode (Phase 2 populates these)
    predicted_agent     TEXT,
    predicted_model     TEXT,

    -- blast-radius + complexity (Phase 3)
    predicted_radius    INTEGER,            -- neighborhood size from graph expansion
    actual_radius       INTEGER,            -- populated post-dispatch via graphify diff
    complexity_score    REAL,               -- file_count × log2(community_span+1) × type_factor
    confidence_bucket   TEXT,               -- high | medium | low | insufficient at dispatch time
    routing_rationale   TEXT,               -- one-line rationale for the agent choice
    cross_silo_reads    TEXT,               -- JSON array of silos read during routing

    PRIMARY KEY (task_hash, graph_epoch, dispatch_ts)
);

-- ── cross-silo read log (Phase 3) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cross_silo_read (
    task_hash   TEXT    NOT NULL,
    read_ts     TEXT    NOT NULL,
    from_silo   TEXT,
    to_silo     TEXT    NOT NULL,

    PRIMARY KEY (task_hash, read_ts, to_silo)
);

CREATE INDEX IF NOT EXISTS idx_csr_task  ON cross_silo_read(task_hash);
CREATE INDEX IF NOT EXISTS idx_csr_to    ON cross_silo_read(to_silo);

CREATE INDEX IF NOT EXISTS idx_dispatch_agent    ON dispatch(agent);
CREATE INDEX IF NOT EXISTS idx_dispatch_ts       ON dispatch(dispatch_ts);
CREATE INDEX IF NOT EXISTS idx_dispatch_silo     ON dispatch(silo);
CREATE INDEX IF NOT EXISTS idx_dispatch_epoch    ON dispatch(graph_epoch);
CREATE INDEX IF NOT EXISTS idx_dispatch_outcome  ON dispatch(outcome_class);

-- ── loop tick nodes ───────────────────────────────────────────────────────────
-- One row per tick of an instrumented loop. B and C share ONE schema (§A-1).
-- loop_tick rows stay ledger-native; they are NOT written into graph.json
-- until graphify supports streaming (deferred — plan §Deferrals).

CREATE TABLE IF NOT EXISTS loop_tick (
    -- PK
    loop_id             TEXT    NOT NULL,   -- UUID for the loop instance
    tick_n              INTEGER NOT NULL,   -- 0-indexed
    graph_epoch         INTEGER NOT NULL,

    -- loop metadata (repeated each tick for self-contained query results)
    loop_type           TEXT    NOT NULL,   -- spec_build_verify | plan_approve_execute |
                                            --   idea_lifecycle | wrap_prime
    -- termination predicate state (JSON snapshot)
    predicate_state     TEXT,

    -- oscillation detection (§A-1 livelock detector: cycle + content-hash)
    content_hash        TEXT,               -- sha256 of tick output
    embedding_ref       TEXT,               -- doobidoo doc ID for semantic distance
    no_progress_streak  INTEGER DEFAULT 0,  -- increments when content_hash == prev tick

    -- termination
    terminated_reason   TEXT,               -- predicate_met | max_ticks |
                                            --   no_progress_cap | human_escalation |
                                            --   error | NULL (ongoing)
    tick_ts             TEXT    NOT NULL,   -- ISO 8601

    -- link to the dispatch(es) this tick spawned (primary/first dispatch)
    -- soft reference only — no FK (dispatch_ts is part of a composite PK in dispatch)
    dispatch_ts         TEXT,

    PRIMARY KEY (loop_id, tick_n, graph_epoch)
);

CREATE INDEX IF NOT EXISTS idx_loop_id        ON loop_tick(loop_id);
CREATE INDEX IF NOT EXISTS idx_loop_type      ON loop_tick(loop_type);
CREATE INDEX IF NOT EXISTS idx_loop_terminated ON loop_tick(terminated_reason);

-- ── route predictions (Phase 2) ───────────────────────────────────────────────
-- Written by `mew route --dry-run`. One row per prediction attempt.
-- Reconciled when an actual dispatch fires with the same task_hash.

CREATE TABLE IF NOT EXISTS route_prediction (
    task_hash           TEXT    NOT NULL,
    predicted_at        TEXT    NOT NULL,   -- ISO 8601
    graph_epoch         INTEGER NOT NULL,

    task_text           TEXT,               -- prompt[:500]
    predicted_agent     TEXT,
    predicted_model     TEXT,
    predicted_silo      TEXT,
    blast_radius_bucket TEXT,               -- small | medium | large
    complexity_bucket   TEXT,               -- simple | moderate | complex

    -- reconciliation (filled in by the actual dispatch, if it happens)
    actual_dispatch_ts  TEXT,
    actual_agent        TEXT,
    actual_model        TEXT,
    agent_diverged      INTEGER,            -- 0/1 — predicted_agent != actual_agent
    model_diverged      INTEGER,            -- 0/1

    PRIMARY KEY (task_hash, predicted_at)
);

CREATE INDEX IF NOT EXISTS idx_rp_task_hash  ON route_prediction(task_hash);
CREATE INDEX IF NOT EXISTS idx_rp_predicted  ON route_prediction(predicted_at);
CREATE INDEX IF NOT EXISTS idx_rp_diverged   ON route_prediction(agent_diverged);
