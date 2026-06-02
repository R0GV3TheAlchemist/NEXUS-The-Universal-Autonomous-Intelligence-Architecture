"""
core/memory/tiers/semantic.py
GAIA Semantic Memory Tier — Sprint G-8 stub

Permanent fact store. Backed by Crystal DB in production.
This stub uses an in-process dict; swap for Crystal DB integration in G-9.

Canon Refs: C34 (Presence), C01 (Sovereignty)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.memory.hierarchy import MemoryQuery


class SemanticMemoryStore:
    """Permanent canon-fact store. No TTL. Production backend: Crystal DB."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None:
        self._store[key] = {"value": value, "gaian_id": gaian_id}

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if gaian_id is not None and entry.get("gaian_id") != gaian_id:
            return None
        return entry["value"]

    async def search(self, query: MemoryQuery) -> list[dict]:  # type: ignore[name-defined]
        results = []
        for key, entry in self._store.items():
            if query.gaian_id and entry.get("gaian_id") != query.gaian_id:
                continue
            results.append({
                "key": key,
                "value": entry["value"],
                "_relevance": 0.5,
                "_recency": 0.0,
            })
        return results

    async def evict_expired(self) -> int:
        return 0
