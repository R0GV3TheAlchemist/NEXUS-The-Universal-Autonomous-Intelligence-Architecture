"""
core/memory/tiers/working.py
GAIA Working Memory Tier — Sprint G-8

Volatile in-process store for the current turn.
Evicts all entries at turn end; zero persistence across sessions.

Canon Refs: C34 (Presence), C01 (Sovereignty)
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.memory.hierarchy import MemoryQuery


class WorkingMemoryStore:
    """In-memory dict store; lives only for the duration of the current turn."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None:
        self._store[key] = {"value": value, "gaian_id": gaian_id, "ts": time.time()}

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if gaian_id is not None and entry.get("gaian_id") != gaian_id:
            return None
        return entry["value"]

    async def search(self, query: MemoryQuery) -> list[dict]:  # type: ignore[name-defined]
        now = time.time()
        results = []
        for key, entry in self._store.items():
            if query.gaian_id and entry.get("gaian_id") != query.gaian_id:
                continue
            age = now - entry.get("ts", now)
            recency = max(0.0, 1.0 - age / 3600.0)
            results.append({
                "key": key,
                "value": entry["value"],
                "_relevance": 0.5,
                "_recency": recency,
            })
        return results

    async def evict_expired(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count
