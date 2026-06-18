"""
core/memory/tiers/working.py

WORKING tier — in-process dict, session-scoped.
All entries are evicted on session end (evict_expired flushes everything).

Canon: C34 (Memory Sovereignty)  Issue: #213
"""
from __future__ import annotations

from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore


class WorkingMemoryStore(MemoryStore):
    """
    Ultra-fast, in-process working memory.

    Keys are scoped by (gaian_id, key); gaian_id defaults to the
    special sentinel '__global__' when not provided.
    """

    _GLOBAL = "__global__"

    def __init__(self) -> None:
        # {(gaian_id, key): value}
        self._store: dict[tuple[str, str], Any] = {}

    # ------------------------------------------------------------------ #
    # MemoryStore ABC
    # ------------------------------------------------------------------ #

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None, **kwargs
    ) -> None:
        self._store[(gaian_id or self._GLOBAL, key)] = value

    async def read(
        self, key: str, gaian_id: Optional[str] = None
    ) -> Optional[Any]:
        return self._store.get((gaian_id or self._GLOBAL, key))

    async def search(self, query: MemoryQuery) -> list[dict]:
        gid = query.gaian_id or self._GLOBAL
        text = query.text.lower()
        results = []
        for (g, k), v in self._store.items():
            if g != gid:
                continue
            haystack = f"{k} {v}".lower()
            relevance = 0.9 if text in haystack else 0.1
            results.append({
                "key": k, "value": v,
                "_relevance": relevance, "_recency": 1.0,
                "_tier": "working",
            })
        return results

    async def evict_expired(self) -> int:
        """Working memory has no TTL — evict *all* entries."""
        count = len(self._store)
        self._store.clear()
        return count

    # ------------------------------------------------------------------ #
    # Extras
    # ------------------------------------------------------------------ #

    async def evict_for_gaian(self, gaian_id: str) -> int:
        """Remove all entries belonging to a specific Gaian."""
        keys = [k for k in self._store if k[0] == gaian_id]
        for k in keys:
            del self._store[k]
        return len(keys)

    def __len__(self) -> int:
        return len(self._store)
