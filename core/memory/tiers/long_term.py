"""
core/memory/tiers/long_term.py
LongTermMemoryStore — permanent, Gaian-scoped identity + settled-arc store.

No TTL; evict_expired() always returns 0.
Each record is scoped to a specific Gaian; different Gaians can hold
different values under the same key.

Canon refs: C34, C01
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _LongTermEntry:
    gaian_id:  str | None
    key:       str
    value:     Any
    arc_type:  str
    created_at: float


class LongTermMemoryStore:
    """Permanent in-memory long-term identity store, keyed by (gaian_id, key)."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str | None, str], _LongTermEntry] = {}

    # ── MemoryStore Protocol ───────────────────────────────────────── #

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,  # unused — permanent
        arc_type: str = "general",
    ) -> None:
        self._entries[(gaian_id, key)] = _LongTermEntry(
            gaian_id=gaian_id,
            key=key,
            value=value,
            arc_type=arc_type,
            created_at=time.time(),
        )

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,
    ) -> Any | None:
        entry = self._entries.get((gaian_id, key))
        return entry.value if entry is not None else None

    async def search(
        self,
        query: Any,
    ) -> list[dict]:
        text = getattr(query, "query_text", "").lower()
        gid  = getattr(query, "gaian_id", None)
        results = []
        for (g, k), entry in self._entries.items():
            if gid is not None and g != gid:
                continue
            haystack = (k + " " + str(entry.value) + " " + entry.arc_type).lower()
            rel = 0.85 if text and text in haystack else 0.2
            results.append({
                "key":        k,
                "value":      entry.value,
                "_relevance": rel,
                "_recency":   0.5,  # identity facts are timeless
                "_arc_type":  entry.arc_type,
            })
        return results

    async def evict_expired(self) -> int:
        """Long-term store is permanent — always returns 0."""
        return 0
