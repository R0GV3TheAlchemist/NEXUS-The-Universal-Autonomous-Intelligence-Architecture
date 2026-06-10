-- V001__create_memory_items.sql
-- Initial schema for the GAIA MemoryStore.
-- Source of truth: core/memory/store.py :: MemoryStore._apply_migrations()
--
-- Canon: Phase 3 — Runtime Integration (May 6, 2026)
-- Memory schema version: 2.0

-- ── Main items table ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS memory_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    kind        TEXT    NOT NULL DEFAULT 'message',
    tier        TEXT    NOT NULL DEFAULT 'short_term',
    role        TEXT    NOT NULL DEFAULT 'user',
    text        TEXT    NOT NULL,
    importance  REAL    NOT NULL DEFAULT 0.5,
    created_at  INTEGER NOT NULL,          -- Unix epoch seconds
    session_id  TEXT,
    topic_tag   TEXT,
    ttl_seconds INTEGER,
    deleted     INTEGER NOT NULL DEFAULT 0  -- soft-delete flag (0=live, 1=deleted)
);

-- ── Core lookup indexes ───────────────────────────────────────────────────────
-- Primary hot-path: all live memories for a given user
CREATE INDEX IF NOT EXISTS idx_mem_user_deleted
    ON memory_items (user_id, deleted);

-- Filter by kind within a user (e.g. retrieve only 'message' or 'reflection' rows)
CREATE INDEX IF NOT EXISTS idx_mem_kind
    ON memory_items (user_id, kind, deleted);
