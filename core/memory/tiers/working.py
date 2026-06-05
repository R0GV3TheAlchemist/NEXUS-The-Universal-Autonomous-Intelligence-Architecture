"""
core/memory/tiers/working.py

WorkingMemoryStore — in-process dict, session-scoped.
Evicted in full at session end (TTL = 0 hours conceptually).
Issue: #213
"""

from __future__ import annotations

from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore


class WorkingMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, Optional[str]]] = {}  # key -> (value, gaian_id)

    def __len__(self) -> int:
        return len(self._data)

    async def write(self, key: str, value: Any, gaian_id: Optional[str] = None, **kwargs) -> None:
        self._data[key] = (value, gaian_id)

    async def read(self, key: str, gaian_id: Optional[str] = None) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is None:
            return None
        val, gid = entry
        if gaian_id and gid and gid != gaian_id:
            return None
        return val

    async def search(self, query: MemoryQuery) -> list[dict]:
        text = query.text.lower()
        results = []
        for key, (value, _) in self._data.items():
            if text in str(value).lower() or text in key.lower():
                results.append({"key": key, "value": value, "_relevance": 0.5, "_recency": 0.8})
        return results

    async def evict_expired(self) -> int:
        count = len(self._data)
        self._data.clear()
        return count

    async def evict_for_gaian(self, gaian_id: str) -> int:
        keys = [k for k, (_, gid) in self._data.items() if gid == gaian_id]
        for k in keys:
            del self._data[k]
        return len(keys)
