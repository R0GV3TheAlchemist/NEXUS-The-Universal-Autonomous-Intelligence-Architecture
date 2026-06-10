-- V002__add_metadata_column.sql
-- Adds the `metadata` JSON column to memory_items.
-- This mirrors the live ALTER TABLE guard in store.py so the migration
-- is safe to apply against both fresh and pre-existing databases.
--
-- SQLite will raise 'duplicate column name' if the column already exists;
-- the migration runner catches OperationalError and treats it as a no-op
-- for this specific statement, then marks the version applied.
--
-- If you need strict idempotence at the SQL layer, apply this manually
-- with the guard below; the runner handles it in Python.

ALTER TABLE memory_items ADD COLUMN metadata TEXT;
