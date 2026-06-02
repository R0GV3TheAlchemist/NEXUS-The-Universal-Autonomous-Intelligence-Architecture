"""
core/memory/tiers/long_term.py
GAIA Long-Term Memory Tier — Sprint G-8 stub

Permanent Gaian-identity store. Backed by Tauri Store in production.
This stub uses an in-process dict; swap for Tauri Store integration in G-9.

Canon Refs: C34 (Presence), C01 (Sovereignty)
"""
from __future__ import annotations

from typing import Any

from core.memory.hierarchy import MemoryQuery


class LongTermMemoryStore:
    """Permanent identity + settled-arc store. No TTL. Production backend: Tauri Store."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,  # ignored — long-term is permanent
    ) -> None:
        self._store[key] = {"value": value, "gaian_id": gaian_id}

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if gaian_id is not None and entry.get("gaian_id") != gaian_id:
            return None
        return entry["value"]

    async def search(self, query: MemoryQuery) -> list[dict]:
        results = []
        for key, entry in self._store.items():
            if query.gaian_id and entry.get("gaian_id") != query.gaian_id:
                continue
            results.append({
                "key": key,
                "value": entry["value"],
                "_relevance": 0.8,  # identity facts are highly relevant by default
                "_recency": 0.0,
            })
        return results

    async def evict_expired(self) -> int:
        return 0  # long-term memory never expires
