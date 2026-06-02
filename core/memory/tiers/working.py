"""
core/memory/tiers/working.py
Working Memory Tier — Sprint G-8

In-memory dict, per-session. Zero persistence. Evicts automatically
when `evict_expired()` is called at turn end, or when the process ends.

TTL: session-scoped (0 hours — evicts at explicit eviction call).

Canon Refs: C34, C01
"""
from __future__ import annotations

import time
from typing import Any

from core.memory.hierarchy import MemoryQuery


class WorkingMemoryStore:
    """Pure in-memory store for working context (current turn state).

    Thread-safe for asyncio (single-threaded event loop). Not safe
    for multi-process use; use a separate store instance per worker.
    """

    def __init__(self) -> None:
        # {(gaian_id, key): (value, written_at_epoch)}
        self._data: dict[tuple[str | None, str], tuple[Any, float]] = {}
        self._evict_at_turn_end: bool = True

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,  # ignored — working memory always session-scoped
    ) -> None:
        self._data[(gaian_id, key)] = (value, time.monotonic())

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        entry = self._data.get((gaian_id, key))
        return entry[0] if entry else None

    async def search(self, query: MemoryQuery) -> list[dict]:
        """Brute-force substring match across all working-memory entries."""
        now = time.monotonic()
        results = []
        for (gid, k), (v, written_at) in self._data.items():
            if query.gaian_id and gid != query.gaian_id:
                continue
            text = str(v).lower()
            relevance = 1.0 if query.query_text.lower() in text else 0.1
            age_seconds = now - written_at
            recency = 1.0 / (1.0 + age_seconds / 60.0)  # decays over minutes
            results.append({
                "key":        k,
                "value":      v,
                "_gaian_id":  gid,
                "_relevance": relevance,
                "_recency":   recency,
            })
        return results

    async def evict_expired(self) -> int:
        """Evict all working memory (full flush). Called at turn end."""
        count = len(self._data)
        self._data.clear()
        return count

    async def evict_for_gaian(self, gaian_id: str) -> int:
        """Evict all entries scoped to a specific Gaian."""
        keys_to_remove = [k for k in self._data if k[0] == gaian_id]
        for k in keys_to_remove:
            del self._data[k]
        return len(keys_to_remove)

    def __len__(self) -> int:
        return len(self._data)
