"""
core/memory/pruner.py

MemoryPruner — capacity enforcement and TTL eviction for the memory layer.
Canon Reference: C01 (Gaian Sovereignty), C-SENTINEL Article 4
Issue: #213
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class PruneReport:
    rows_before: int
    rows_pruned:  int
    rows_after:   int
    duration_ms:  float


class MemoryPruner:
    """
    Enforces memory capacity limits and evicts expired TTL items.

    - PERMANENT tier items are never pruned.
    - Pruning removes the lowest-priority items (importance score) first.
    - TTL eviction soft-deletes items whose ttl_seconds has elapsed.
    """

    def __init__(
        self,
        store,                       # MemoryStore instance
        capacity: int   = 1000,
        batch_size: int = 100,
        min_age_sec: int = 60,
    ) -> None:
        self._store      = store
        self._capacity   = capacity
        self._batch_size = batch_size
        self._min_age    = min_age_sec

    def run(self, user_id: Optional[str] = None) -> PruneReport:
        """Run a full prune cycle: TTL eviction + capacity enforcement."""
        t0 = time.monotonic()
        before = self._store.count(user_id=user_id)
        self.prune_expired_ttl(user_id=user_id)
        self._enforce_capacity(user_id=user_id)
        after = self._store.count(user_id=user_id)
        return PruneReport(
            rows_before=before,
            rows_pruned=before - after,
            rows_after=after,
            duration_ms=(time.monotonic() - t0) * 1000,
        )

    def prune_expired_ttl(self, user_id: Optional[str] = None) -> int:
        """
        Soft-delete items whose TTL has elapsed.
        Returns the number of items pruned.
        """
        now = int(time.time())
        query = """
            UPDATE memory_items
            SET deleted = 1
            WHERE deleted = 0
              AND ttl_seconds IS NOT NULL
              AND (created_at + ttl_seconds) <= ?
        """
        args: list = [now]
        if user_id:
            query += " AND user_id = ?"
            args.append(user_id)
        cur = self._store._conn.execute(query, args)
        self._store._conn.commit()
        return cur.rowcount

    def _enforce_capacity(self, user_id: Optional[str] = None) -> int:
        """Soft-delete lowest-importance non-permanent items above capacity."""
        count = self._store.count(user_id=user_id)
        if count <= self._capacity:
            return 0

        excess = count - self._capacity
        to_delete = min(excess + self._batch_size, count)

        query = """
            UPDATE memory_items
            SET deleted = 1
            WHERE id IN (
                SELECT id FROM memory_items
                WHERE deleted = 0
                  AND tier != 'permanent'
                  {uid_clause}
                ORDER BY importance ASC, created_at ASC
                LIMIT ?
            )
        """.format(uid_clause="AND user_id = ?" if user_id else "")

        args: list = []
        if user_id:
            args.append(user_id)
        args.append(to_delete)

        cur = self._store._conn.execute(query, args)
        self._store._conn.commit()
        return cur.rowcount
