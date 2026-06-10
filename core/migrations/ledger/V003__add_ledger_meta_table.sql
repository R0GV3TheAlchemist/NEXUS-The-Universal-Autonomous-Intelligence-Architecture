-- V003__add_ledger_meta_table.sql
-- Adds a ledger_meta key-value table for per-database metadata:
--   schema_version, genesis_chain_hash, gaian_name, created_at, etc.
--
-- This is separate from the schema_versions tracking table (which is
-- maintained by env.py) and is intended for application-level metadata
-- that the ActionLedger class and audit dashboards can read at runtime.

CREATE TABLE IF NOT EXISTS ledger_meta (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at REAL NOT NULL
);

-- Seed the genesis record so verify_chain() has a stable anchor point
INSERT OR IGNORE INTO ledger_meta (key, value, updated_at)
VALUES
    ('schema_version',   '1.0',   strftime('%s', 'now')),
    ('genesis_chain_hash', '',    strftime('%s', 'now')),  -- updated on first event append
    ('constitutional_floor', 'T1-IMMUTABLE', strftime('%s', 'now')),
    ('canon_ref',  'https://github.com/R0GV3TheAlchemist/GAIA', strftime('%s', 'now'));
