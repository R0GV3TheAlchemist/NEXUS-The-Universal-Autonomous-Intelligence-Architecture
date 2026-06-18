"""
core/memory/tiers/semantic.py

SEMANTIC tier — in-process dict, permanent, canon-indexed.
Stores canonical GAIA doctrine, facts, and ontology entries.
Eviction always returns 0 (permanent tier).

Canon: C34 (Memory Sovereignty), C01 (GAIA as orchestration)  Issue: #213
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore


@dataclass
class _SemanticEntry:
    value:      Any
    tags:       list[str]  = field(default_factory=list)
    canon_refs: list[str]  = field(default_factory=list)
    source:     str        = ""


class SemanticMemoryStore(MemoryStore):
    """
    Permanent semantic / canonical fact store.
    Not scoped by gaian_id — semantic facts are global.
    """

    def __init__(self) -> None:
        self._store: dict[str, _SemanticEntry] = {}

    # ------------------------------------------------------------------ #
    # MemoryStore ABC
    # ------------------------------------------------------------------ #

    async def write(
        self, key: str, value: Any,
        canon_refs: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        source: str = "",
        **kwargs
    ) -> None:
        self._store[key] = _SemanticEntry(
            value=value,
            tags=tags or [],
            canon_refs=canon_refs or [],
            source=source,
        )

    async def read(
        self, key: str, gaian_id: Optional[str] = None
    ) -> Optional[Any]:
        entry = self._store.get(key)
        return entry.value if entry else None

    async def search(self, query: MemoryQuery) -> list[dict]:
        text = query.text.lower()
        results = []
        for key, entry in self._store.items():
            haystack = f"{key} {entry.value} {' '.join(entry.tags)} {' '.join(entry.canon_refs)}".lower()
            relevance = 0.95 if text in haystack else 0.05
            results.append({
                "key": key, "value": entry.value,
                "_relevance": relevance, "_recency": 0.5,
                "_tier": "semantic",
                "_canon_refs": entry.canon_refs,
                "_source": entry.source,
            })
        return results

    async def evict_expired(self) -> int:
        """Semantic tier is permanent — nothing to evict."""
        return 0
