-- Migration 002 — Phase 3: blast-radius + complexity columns on dispatch
-- Epoch: 1 → 2
-- Safe to run multiple times (ALTER TABLE ADD COLUMN is idempotent in our runner).

ALTER TABLE dispatch ADD COLUMN predicted_radius   INTEGER;
ALTER TABLE dispatch ADD COLUMN actual_radius      INTEGER;
ALTER TABLE dispatch ADD COLUMN complexity_score   REAL;
ALTER TABLE dispatch ADD COLUMN confidence_bucket  TEXT;
ALTER TABLE dispatch ADD COLUMN routing_rationale  TEXT;
ALTER TABLE dispatch ADD COLUMN cross_silo_reads   TEXT;   -- JSON array

-- Cross-silo read log (§Phase 3 federation function)
CREATE TABLE IF NOT EXISTS cross_silo_read (
    task_hash   TEXT    NOT NULL,
    read_ts     TEXT    NOT NULL,
    from_silo   TEXT,
    to_silo     TEXT    NOT NULL,

    PRIMARY KEY (task_hash, read_ts, to_silo)
);

CREATE INDEX IF NOT EXISTS idx_csr_task  ON cross_silo_read(task_hash);
CREATE INDEX IF NOT EXISTS idx_csr_to    ON cross_silo_read(to_silo);
