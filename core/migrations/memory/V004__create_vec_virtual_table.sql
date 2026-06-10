-- V004__create_vec_virtual_table.sql
-- Creates the sqlite-vec virtual table that stores embedding vectors
-- keyed by the same rowid as memory_items.
--
-- IMPORTANT: This migration will fail if the sqlite-vec extension is not
-- loaded into the SQLite connection.  The migration runner (env.py) attempts
-- to load sqlite-vec before running migrations in the memory/ folder.
-- If the extension is unavailable, this migration is SKIPPED (not failed)
-- and the MemoryStore falls back to text-only retrieval — this matches the
-- existing graceful-degrade behaviour in store.py.
--
-- Embedding dimension: 384 (default for all-MiniLM-L6-v2 / FallbackEmbedder).
-- If you swap in a different embedding model with a different dimension,
-- create a V005 migration to DROP and recreate this virtual table.
--
-- The vec0 virtual table is a pure in-process index — it does not add
-- a physical table to the SQLite file in the traditional sense, so there
-- is no IF NOT EXISTS guard syntax available for virtual tables.
-- The runner is responsible for checking whether this table already exists
-- before executing this file (see env.py).

CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory_items
USING vec0(
    embedding FLOAT[384]
);
