"""
core/memory/tiers/semantic.py
SemanticMemoryStore — permanent, keyword-searchable canon + fact store.

No TTL; evict_expired() always returns 0 (permanent tier).
Search is a simple bag-of-words substring match — plug in a real
embedding backend by subclassing and overriding search().

Canon refs: C34, C01
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _SemanticEntry:
    key:        str
    value:      Any
    tags:       list[str]
    canon_refs: list[str]
    source:     str
    created_at: float


class SemanticMemoryStore:
    """Permanent in-memory semantic store backed by keyword search."""

    def __init__(self) -> None:
        self._entries: dict[str, _SemanticEntry] = {}

    # ── MemoryStore Protocol ───────────────────────────────────────── #

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,  # unused — semantic is global
        ttl_hours: float | None = None,  # unused — permanent
        tags: list[str] | None = None,
        canon_refs: list[str] | None = None,
        source: str = "unknown",
    ) -> None:
        self._entries[key] = _SemanticEntry(
            key=key,
            value=value,
            tags=tags or [],
            canon_refs=canon_refs or [],
            source=source,
            created_at=time.time(),
        )

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,  # unused
    ) -> Any | None:
        entry = self._entries.get(key)
        return entry.value if entry is not None else None

    async def search(
        self,
        query: Any,
    ) -> list[dict]:
        text = getattr(query, "query_text", "").lower()
        results = []
        for entry in self._entries.values():
            haystack = (
                entry.key + " " +
                str(entry.value) + " " +
                " ".join(entry.tags) + " " +
                " ".join(entry.canon_refs)
            ).lower()
            rel = 0.9 if text and text in haystack else 0.2
            results.append({
                "key": entry.key,
                "value": entry.value,
                "_relevance": rel,
                "_recency":   0.5,  # semantic facts are timeless
                "_source":    entry.source,
                "_canon_refs": entry.canon_refs,
            })
        return results

    async def evict_expired(self) -> int:
        """Semantic store is permanent — always returns 0."""
        return 0
