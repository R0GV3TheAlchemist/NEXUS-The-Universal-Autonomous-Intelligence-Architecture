-- GAIA-OS Sovereign Memory System — SQLite Schema
-- Issue #66 | Pillar III: Societas
-- All content fields are AES-256-GCM encrypted at the application layer.
-- Erasure is achieved via key rotation (crypto-erasure), not physical row deletion.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- ENCRYPTION KEY RING
-- Stores wrapped DEKs (Data Encryption Keys).
-- The KEK (Master Key) lives in the OS keychain, never here.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS encryption_keys (
    key_id      TEXT PRIMARY KEY,   -- e.g. 'episodic-v1', 'semantic-v1'
    wrapped_key BLOB NOT NULL,       -- DEK encrypted under platform KEK
    algorithm   TEXT NOT NULL DEFAULT 'aes-256-gcm',
    created_at  INTEGER NOT NULL,
    rotated_at  INTEGER,             -- NULL = still active
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'retired', 'revoked'))
);

-- ─────────────────────────────────────────────
-- EPISODIC MEMORY
-- Timestamped events: journals, decisions, conversations.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS episodic_memory (
    id              TEXT PRIMARY KEY,       -- UUIDv7 / ULID
    principal_id    TEXT NOT NULL,
    created_at      INTEGER NOT NULL,       -- unix ms
    updated_at      INTEGER NOT NULL,
    type            TEXT NOT NULL           -- 'journal' | 'event' | 'decision' | 'conversation'
                    CHECK (type IN ('journal', 'event', 'decision', 'conversation', 'note')),
    content_cipher  BLOB NOT NULL,
    content_nonce   BLOB NOT NULL,          -- 96-bit random nonce
    content_aad     BLOB,                   -- JSON: {table, id, schema_version}
    tags_json       TEXT,                   -- JSON array of strings
    embedding_id    TEXT,                   -- FK into vector store
    key_id          TEXT NOT NULL REFERENCES encryption_keys(key_id),
    deleted_at      INTEGER                 -- soft delete (NULL = active)
);

CREATE INDEX IF NOT EXISTS idx_episodic_principal_created
    ON episodic_memory (principal_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_episodic_type_created
    ON episodic_memory (type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_episodic_deleted
    ON episodic_memory (deleted_at);

-- ─────────────────────────────────────────────
-- SEMANTIC MEMORY
-- Distilled patterns, values, beliefs, long-arc interpretations.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS semantic_memory (
    id                      TEXT PRIMARY KEY,
    principal_id            TEXT NOT NULL,
    pattern_cipher          BLOB NOT NULL,
    pattern_nonce           BLOB NOT NULL,
    pattern_aad             BLOB,
    confidence              REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    first_observed_at       INTEGER NOT NULL,
    last_observed_at        INTEGER NOT NULL,
    supporting_episode_ids  TEXT NOT NULL,  -- JSON array of episodic_memory.id
    tags_json               TEXT,
    key_id                  TEXT NOT NULL REFERENCES encryption_keys(key_id),
    deleted_at              INTEGER
);

CREATE INDEX IF NOT EXISTS idx_semantic_principal_last_observed
    ON semantic_memory (principal_id, last_observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_semantic_tags
    ON semantic_memory (tags_json);

-- ─────────────────────────────────────────────
-- BIOMETRIC HISTORY
-- Time-series: HRV, alignment score, affect snapshots.
-- Values are NOT encrypted (no PII — numeric scalars only).
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS biometric_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    principal_id TEXT NOT NULL,
    timestamp    INTEGER NOT NULL,
    signal_type  TEXT NOT NULL,
    -- signal_type values: 'hrv_rmssd' | 'alignment_score' | 'affect_valence'
    --                     | 'affect_arousal' | 'affect_dominance' | 'affect_entropy'
    --                     | 'arc_stability' | 'kp_index' | 'schumann_amplitude'
    value        REAL NOT NULL,
    source       TEXT NOT NULL    -- 'apple_health' | 'oura' | 'garmin' | 'polar'
                                  -- | 'gaia_affect' | 'schumann_layer' | 'manual'
);

CREATE INDEX IF NOT EXISTS idx_biometric_type_time
    ON biometric_history (signal_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_biometric_principal_time
    ON biometric_history (principal_id, timestamp DESC);

-- ─────────────────────────────────────────────
-- STAGE RECORDS
-- Current developmental stage state (one row per principal, updated in place).
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stage_records (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    principal_id              TEXT NOT NULL UNIQUE,
    current_stage             INTEGER NOT NULL CHECK (current_stage BETWEEN 1 AND 5),
    stage_entered_at          INTEGER NOT NULL,
    days_in_stage             INTEGER NOT NULL DEFAULT 0,
    decision_entropy          REAL NOT NULL DEFAULT 0,  -- 0–100
    hrv_coherence             REAL NOT NULL DEFAULT 0,  -- 0–100
    journaling_depth          REAL NOT NULL DEFAULT 0,  -- 0–100
    focus_session_length_min  REAL NOT NULL DEFAULT 0,  -- raw minutes (avg)
    goal_completion_rate      REAL NOT NULL DEFAULT 0,  -- 0–100
    emotional_arc_stability   REAL NOT NULL DEFAULT 0,  -- 0–100
    transition_candidate      INTEGER NOT NULL DEFAULT 0 CHECK (transition_candidate IN (0,1)),
    regression_risk           INTEGER NOT NULL DEFAULT 0 CHECK (regression_risk IN (0,1)),
    updated_at                INTEGER NOT NULL
);

-- ─────────────────────────────────────────────
-- STAGE TRANSITIONS
-- Append-only log of every stage change (forward or regression).
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stage_transitions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    principal_id     TEXT NOT NULL,
    from_stage       INTEGER NOT NULL,
    to_stage         INTEGER NOT NULL,
    transitioned_at  INTEGER NOT NULL,
    is_regression    INTEGER NOT NULL DEFAULT 0 CHECK (is_regression IN (0,1)),
    markers_met_json TEXT NOT NULL,              -- JSON array of marker names
    ceremony_shown   INTEGER NOT NULL DEFAULT 0  -- 0/1
);

CREATE INDEX IF NOT EXISTS idx_stage_transitions_principal_time
    ON stage_transitions (principal_id, transitioned_at DESC);

-- ─────────────────────────────────────────────
-- LEGACY ARTIFACTS
-- Stage-4/5 outputs: letters to future self, wisdom distillations.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS legacy_artifacts (
    id                TEXT PRIMARY KEY,
    principal_id      TEXT NOT NULL,
    created_at        INTEGER NOT NULL,
    stage_at_creation INTEGER NOT NULL CHECK (stage_at_creation IN (4, 5)),
    title_cipher      BLOB NOT NULL,
    title_nonce       BLOB NOT NULL,
    title_aad         BLOB,                   -- AAD used when encrypting the title
    content_cipher    BLOB NOT NULL,
    content_nonce     BLOB NOT NULL,
    content_aad       BLOB,
    source_episode_id TEXT REFERENCES episodic_memory(id),
    export_formats    TEXT NOT NULL DEFAULT '["markdown","json"]',  -- JSON array
    tags_json         TEXT,
    key_id            TEXT NOT NULL REFERENCES encryption_keys(key_id),
    deleted_at        INTEGER
);

CREATE INDEX IF NOT EXISTS idx_legacy_principal_created
    ON legacy_artifacts (principal_id, created_at DESC);

-- ─────────────────────────────────────────────
-- SCHEMA VERSION (for forward-only migrations)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  INTEGER NOT NULL,
    description TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_version (version, applied_at, description)
    VALUES (1, strftime('%s','now') * 1000, 'Initial Sovereign Memory schema — Issue #66');
