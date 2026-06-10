-- V001__create_audit_events.sql
-- Initial schema for the GAIA ActionLedger.
-- Source of truth: core/audit/ledger.py :: ActionLedger (_DDL constant)
--
-- The ledger is append-only and tamper-evident.  Each row stores:
--   payload_hash  — SHA-256 of the serialised AuditEvent JSON
--   chain_hash    — SHA-256 of (payload_hash + previous_chain_hash)
-- so that any post-hoc modification to any row breaks the chain and is
-- detected by ActionLedger.verify_chain().
--
-- Canon: Phase 3 — Runtime Integration (May 6, 2026)
-- EventType values (from core/audit/ledger.py :: EventType enum):
--   action_executed, policy_decision, memory_write, memory_read,
--   tool_execution, state_snapshot, session_start, session_end,
--   identity_verified, alignment_check, safety_intervention,
--   canon_invocation, error, custom

-- ── Append-only ledger table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_events (
    seq           INTEGER PRIMARY KEY AUTOINCREMENT,  -- monotone sequence for chain ordering
    event_id      TEXT    NOT NULL UNIQUE,             -- UUIDv4
    event_type    TEXT    NOT NULL,                    -- EventType enum value
    actor         TEXT    NOT NULL,                    -- "gaia" | "user" | "policy" | ...
    user_id       TEXT    NOT NULL DEFAULT '',
    session_id    TEXT    NOT NULL DEFAULT '',
    action        TEXT    NOT NULL,                    -- short action name
    outcome       TEXT    NOT NULL DEFAULT 'success',  -- "success" | "failure" | "blocked"
    justification TEXT    NOT NULL DEFAULT '',         -- GAIA's reasoning
    metadata_json TEXT    NOT NULL DEFAULT '{}',       -- arbitrary JSON context
    timestamp     REAL    NOT NULL,                    -- Unix epoch float
    parent_id     TEXT,                                -- event_id of causal predecessor
    payload_hash  TEXT    NOT NULL,                    -- SHA-256 of serialised event
    chain_hash    TEXT    NOT NULL                     -- SHA-256 of (payload_hash + prev_chain_hash)
);

-- ── Lookup indexes ────────────────────────────────────────────────────────────
-- These four match the indexes created inline in ActionLedger.__init__() via _DDL

-- Query by session (most common operational read pattern)
CREATE INDEX IF NOT EXISTS idx_session
    ON audit_events (session_id);

-- Query by actor ("who did what?")
CREATE INDEX IF NOT EXISTS idx_actor
    ON audit_events (actor);

-- Query by event_type ("show me all safety_intervention events")
CREATE INDEX IF NOT EXISTS idx_evtype
    ON audit_events (event_type);

-- Time-range queries (audit dashboards, rate analysis)
CREATE INDEX IF NOT EXISTS idx_ts
    ON audit_events (timestamp);
