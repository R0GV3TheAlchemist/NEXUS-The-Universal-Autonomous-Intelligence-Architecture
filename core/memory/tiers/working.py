"""
core/memory/tiers/working.py
WorkingMemoryStore — current-turn volatile store.

Data lives in a plain dict; everything evicts at turn end (evict_expired)
or when a specific Gaian's scope is flushed (evict_for_gaian).

Canon refs: C34, C01
"""
from __future__ import annotations

from typing import Any


class WorkingMemoryStore:
    """Ephemeral, in-process, zero-persistence memory for the current turn."""

    def __init__(self) -> None:
        # { (gaian_id_or_None, key): value }
        self._data: dict[tuple[str | None, str], Any] = {}

    # ── MemoryStore Protocol ───────────────────────────────────────── #

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,  # ignored — working memory never TTLs mid-turn
    ) -> None:
        self._data[(gaian_id, key)] = value

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,
    ) -> Any | None:
        return self._data.get((gaian_id, key))

    async def search(
        self,
        query: Any,  # MemoryQuery — imported lazily to avoid circular deps
    ) -> list[dict]:
        """Simple substring match on string values; returns all matches."""
        text = getattr(query, "query_text", "").lower()
        gid  = getattr(query, "gaian_id", None)
        results = []
        for (g, k), v in self._data.items():
            if gid is not None and g != gid:
                continue
            haystack = (str(v) + " " + k).lower()
            rel = 0.8 if text and text in haystack else 0.3
            results.append({"key": k, "value": v, "_relevance": rel, "_recency": 0.9})
        return results

    async def evict_expired(self) -> int:
        """Flush ALL working memory (called at turn end). Returns count removed."""
        count = len(self._data)
        self._data.clear()
        return count

    # ── Extra API ─────────────────────────────────────────────────── #

    async def evict_for_gaian(self, gaian_id: str) -> int:
        """Remove all entries scoped to a specific Gaian."""
        keys = [k for k in self._data if k[0] == gaian_id]
        for k in keys:
            del self._data[k]
        return len(keys)

    def __len__(self) -> int:
        return len(self._data)
