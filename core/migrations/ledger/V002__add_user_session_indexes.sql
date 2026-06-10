-- V002__add_user_session_indexes.sql
-- Composite indexes for high-frequency query patterns identified during
-- Phase 3 load testing.
--
-- These are separate from V001 to keep initial table creation fast and to
-- allow them to be built concurrently (or deferred) on large existing ledgers.

-- Per-user event history (audit dashboard: "show events for this user")
CREATE INDEX IF NOT EXISTS idx_user_ts
    ON audit_events (user_id, timestamp DESC);

-- Per-session ordered history (causal chain reconstruction)
CREATE INDEX IF NOT EXISTS idx_session_seq
    ON audit_events (session_id, seq ASC);

-- Safety / alignment monitoring: filter by outcome + type
CREATE INDEX IF NOT EXISTS idx_outcome_type
    ON audit_events (outcome, event_type, timestamp DESC);

-- Parent-child lookup (causal chain traversal upward from a leaf event)
CREATE INDEX IF NOT EXISTS idx_parent
    ON audit_events (parent_id)
    WHERE parent_id IS NOT NULL;
