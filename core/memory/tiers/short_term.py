"""
core/memory/tiers/short_term.py
GAIA Short-Term Memory Tier — Sprint G-8 stub

TTL-bounded in-memory store. Default TTL: 48 hours.
Holds the last N turns of context; evicts on TTL expiry.

Canon Refs: C34 (Presence), C01 (Sovereignty)
"""
from __future__ import annotations

import time
from typing import Any

from core.memory.hierarchy import MemoryQuery

_DEFAULT_TTL_HOURS = 48.0


class ShortTermMemoryStore:
    """TTL-bounded in-memory store for recent context (last N turns)."""

    def __init__(self, default_ttl_hours: float = _DEFAULT_TTL_HOURS) -> None:
        self._store: dict[str, dict] = {}
        self._default_ttl = default_ttl_hours * 3600

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None:
        ttl = (ttl_hours * 3600) if ttl_hours is not None else self._default_ttl
        self._store[key] = {
            "value": value,
            "gaian_id": gaian_id,
            "ts": time.time(),
            "expires_at": time.time() + ttl,
        }

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        entry = self._store.get(key)
        if entry is None or time.time() > entry["expires_at"]:
            return None
        if gaian_id is not None and entry.get("gaian_id") != gaian_id:
            return None
        return entry["value"]

    async def search(self, query: MemoryQuery) -> list[dict]:
        now = time.time()
        results = []
        for key, entry in self._store.items():
            if now > entry.get("expires_at", 0):
                continue
            if query.gaian_id and entry.get("gaian_id") != query.gaian_id:
                continue
            age = now - entry.get("ts", now)
            recency = max(0.0, 1.0 - age / (self._default_ttl or 1))
            results.append({
                "key": key,
                "value": entry["value"],
                "_relevance": 0.5,
                "_recency": recency,
            })
        return results

    async def evict_expired(self) -> int:
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v.get("expires_at", 0)]
        for k in expired:
            del self._store[k]
        return len(expired)
