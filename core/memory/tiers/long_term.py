"""
core/memory/tiers/long_term.py

LONG-TERM tier — in-process dict, permanent, Gaian-identity-scoped.
Stores persistent identity arcs, personality profiles, and relationship
context for each Gaian entity.
Eviction always returns 0 (permanent tier).

Canon: C34 (Memory Sovereignty), C01 (GAIA as orchestration)  Issue: #213
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore


@dataclass
class _LongTermEntry:
    value:    Any
    gaian_id: str
    arc_type: str         = ""
    tags:     list[str]   = field(default_factory=list)


class LongTermMemoryStore(MemoryStore):
    """
    Permanent long-term store, scoped per Gaian entity.
    Two Gaians may store different values under the same key.
    """

    _GLOBAL = "__global__"

    def __init__(self) -> None:
        # {(gaian_id, key): _LongTermEntry}
        self._store: dict[tuple[str, str], _LongTermEntry] = {}

    # ------------------------------------------------------------------ #
    # MemoryStore ABC
    # ------------------------------------------------------------------ #

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None,
        arc_type: str = "",
        tags: Optional[list[str]] = None,
        **kwargs
    ) -> None:
        gid = gaian_id or self._GLOBAL
        self._store[(gid, key)] = _LongTermEntry(
            value=value,
            gaian_id=gid,
            arc_type=arc_type,
            tags=tags or [],
        )

    async def read(
        self, key: str, gaian_id: Optional[str] = None
    ) -> Optional[Any]:
        gid = gaian_id or self._GLOBAL
        entry = self._store.get((gid, key))
        return entry.value if entry else None

    async def search(self, query: MemoryQuery) -> list[dict]:
        gid = query.gaian_id or self._GLOBAL
        text = query.text.lower()
        results = []
        for (g, k), entry in self._store.items():
            if g != gid:
                continue
            haystack = f"{k} {entry.value} {entry.arc_type} {' '.join(entry.tags)}".lower()
            relevance = 0.9 if text in haystack else 0.1
            results.append({
                "key": k, "value": entry.value,
                "_relevance": relevance, "_recency": 0.5,
                "_tier": "long_term",
                "_arc_type": entry.arc_type,
            })
        return results

    async def evict_expired(self) -> int:
        """Long-term tier is permanent — nothing to evict."""
        return 0
