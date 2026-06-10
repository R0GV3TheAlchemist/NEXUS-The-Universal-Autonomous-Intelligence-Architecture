-- V003__add_topic_tier_indexes.sql
-- Additional query-performance indexes for common retrieval patterns.
--
-- These are separate from V001 to make the initial table creation cheap;
-- the heavier indexes are applied in this follow-up migration that can
-- run as a background step on large existing databases.

-- Filter by topic_tag (used by MemoryStore.retrieve() when topic_tag is set)
CREATE INDEX IF NOT EXISTS idx_mem_topic
    ON memory_items (user_id, topic_tag, deleted)
    WHERE topic_tag IS NOT NULL;

-- Filter by memory tier (short_term / long_term / episodic / semantic)
CREATE INDEX IF NOT EXISTS idx_mem_tier
    ON memory_items (user_id, tier, deleted);

-- TTL pruning scan — find rows whose TTL has expired
CREATE INDEX IF NOT EXISTS idx_mem_ttl
    ON memory_items (created_at, ttl_seconds)
    WHERE ttl_seconds IS NOT NULL AND deleted = 0;

-- Recency sort (used by the fallback retrieval path when sqlite-vec is absent)
CREATE INDEX IF NOT EXISTS idx_mem_recency
    ON memory_items (user_id, created_at DESC, deleted);

-- Importance filter (used by retrieve() importance_floor parameter)
CREATE INDEX IF NOT EXISTS idx_mem_importance
    ON memory_items (user_id, importance DESC, deleted);
