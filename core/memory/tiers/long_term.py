"""
core/memory/tiers/long_term.py

LongTermMemoryStore — permanent, Gaian-identity-scoped.
Holds arc history, personality evolution, deep identity records.
Never evicted.
Issue: #213
"""

from __future__ import annotations

from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore


class LongTermMemoryStore(MemoryStore):
    def __init__(self) -> None:
        # keyed by (key, gaian_id) to enforce Gaian scoping
        self._data: dict[tuple[str, Optional[str]], Any] = {}

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None,
        arc_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        self._data[(key, gaian_id)] = value

    async def read(self, key: str, gaian_id: Optional[str] = None) -> Optional[Any]:
        return self._data.get((key, gaian_id))

    async def search(self, query: MemoryQuery) -> list[dict]:
        text = query.text.lower()
        results = []
        for (key, gid), value in self._data.items():
            if query.gaian_id and gid and gid != query.gaian_id:
                continue
            if text in key.lower() or text in str(value).lower():
                results.append({"key": key, "value": value, "_relevance": 0.8, "_recency": 0.4})
        return results

    async def evict_expired(self) -> int:
        return 0  # Long-term memory is permanent
