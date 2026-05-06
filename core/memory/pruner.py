"""
core.memory.pruner
==================
Importance-weighted LRU eviction for GAIA's memory store.

The pruner runs periodically (or on-demand) to keep the number of live
memory rows below a configured capacity.  It uses a combined priority
score to decide which items to drop first:

    priority = importance * 0.6
             + recency_factor * 0.25   (1 → 0 over 90 days)
             + tier_bonus * 0.15       (PERMANENT gets highest bonus)

Lower priority → evicted first.  PERMANENT items are never auto-pruned.

Usage
-----
    from core.memory import MemoryStore, MemoryPruner

    store  = MemoryStore()
    pruner = MemoryPruner(store, capacity=50_000, batch_size=500)

    # In your background task:
    report = pruner.run(user_id="user_001")   # prune one user
    report = pruner.run()                     # prune globally
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from .store import MemoryStore
from .taxonomy import MemoryTier

log = logging.getLogger(__name__)

_TIER_BONUS = {
    MemoryTier.PERMANENT:  1.0,
    MemoryTier.LONG_TERM:  0.6,
    MemoryTier.SHORT_TERM: 0.3,
    MemoryTier.EPHEMERAL:  0.0,
}


@dataclass
class PruneReport:
    """Summary returned by ``MemoryPruner.run()``."""
    user_id:       Optional[str]
    rows_before:   int
    rows_pruned:   int
    rows_after:    int
    duration_ms:   float


class MemoryPruner:
    """
    Evict low-priority memory items to keep the store below *capacity*.

    Parameters
    ----------
    store       : The MemoryStore to operate on.
    capacity    : Maximum live rows per user (or globally if user_id omitted).
                  Default 100 000.
    batch_size  : How many rows to evict per run.  Default 500.
    min_age_sec : Only consider rows older than this for eviction.
                  Protects very recent memories from being pruned.
                  Default 3600 (1 hour).
    """

    def __init__(
        self,
        store:        MemoryStore,
        capacity:     int = 100_000,
        batch_size:   int = 500,
        min_age_sec:  int = 3_600,
    ) -> None:
        self._store       = store
        self._capacity    = capacity
        self._batch_size  = batch_size
        self._min_age_sec = min_age_sec

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, user_id: Optional[str] = None) -> PruneReport:
        """
        Run one eviction pass.  Marks excess low-priority items as
        deleted and returns a report.

        Call ``store.hard_delete_soft_deleted()`` afterwards to free
        disk space (or let it accumulate and compact on a schedule).
        """
        t0     = time.perf_counter()
        before = self._count(user_id)

        if before <= self._capacity:
            return PruneReport(
                user_id=user_id,
                rows_before=before,
                rows_pruned=0,
                rows_after=before,
                duration_ms=0.0,
            )

        excess  = before - self._capacity
        to_drop = min(excess + self._batch_size, before)  # over-shoot slightly

        ids = self._select_eviction_candidates(user_id, to_drop)
        if ids:
            self._soft_delete(ids)
            log.info(
                "MemoryPruner: evicted %d rows (user=%s, before=%d, capacity=%d)",
                len(ids), user_id or "*", before, self._capacity,
            )

        after = self._count(user_id)
        return PruneReport(
            user_id=user_id,
            rows_before=before,
            rows_pruned=len(ids),
            rows_after=after,
            duration_ms=(time.perf_counter() - t0) * 1000,
        )

    def prune_expired_ttl(self, user_id: Optional[str] = None) -> int:
        """
        Soft-delete any items whose TTL has elapsed.
        Returns the number of items marked deleted.
        """
        now = int(time.time())
        where = "ttl_seconds IS NOT NULL AND (created_at + ttl_seconds) < ? AND deleted = 0"
        params: list = [now]
        if user_id:
            where += " AND user_id = ?"
            params.append(user_id)
        cur = self._store._conn.execute(
            f"UPDATE memory_items SET deleted = 1 WHERE {where}", params
        )
        self._store._conn.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count(self, user_id: Optional[str]) -> int:
        sql = "SELECT COUNT(*) FROM memory_items WHERE deleted = 0"
        params: list = []
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        return self._store._conn.execute(sql, params).fetchone()[0]

    def _select_eviction_candidates(self, user_id: Optional[str], limit: int) -> list:
        """
        Return *limit* row ids with the lowest keep-priority, excluding
        PERMANENT items and items younger than min_age_sec.

        Uses ``<=`` for the age cutoff so that rows inserted within the
        current second are included when min_age_sec=0 (e.g. in tests).
        """
        now       = int(time.time())
        cutoff_ts = now - self._min_age_sec
        # We compute a priority score entirely in SQL so we don't have to
        # load all rows into Python memory.
        #
        # score = importance * 0.6
        #       + recency_factor * 0.25   -- recency_factor = 1/(1 + age_days/90)
        #       + tier_bonus * 0.15
        #
        # Lower score → evicted first.
        sql = """
            SELECT id
            FROM memory_items
            WHERE deleted = 0
              AND tier != 'permanent'
              AND created_at <= ?
              {user_filter}
            ORDER BY
                (
                  importance * 0.6
                  + (1.0 / (1.0 + CAST(? - created_at AS REAL) / 7776000.0)) * 0.25
                  + CASE tier
                      WHEN 'long_term'  THEN 0.6
                      WHEN 'short_term' THEN 0.3
                      ELSE 0.0
                    END * 0.15
                ) ASC
            LIMIT ?
        """
        user_filter = "AND user_id = ?" if user_id else ""
        sql = sql.format(user_filter=user_filter)
        params: list = [cutoff_ts, now]
        if user_id:
            params.append(user_id)
        params.append(limit)
        rows = self._store._conn.execute(sql, params).fetchall()
        return [row[0] for row in rows]

    def _soft_delete(self, ids: list) -> None:
        placeholders = ",".join("?" * len(ids))
        self._store._conn.execute(
            f"UPDATE memory_items SET deleted = 1 WHERE id IN ({placeholders})",
            ids,
        )
        self._store._conn.commit()
