"""
core/memory/tiers/semantic.py

SemanticMemoryStore — permanent, canon-indexed facts and doctrines.
Never evicted. Searched by text matching (embedding search pluggable later).
Issue: #213
"""

from __future__ import annotations

from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore


class SemanticMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    async def write(
        self, key: str, value: Any,
        canon_refs: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        source: Optional[str] = None,
        **kwargs,
    ) -> None:
        self._data[key] = {
            "value":      value,
            "canon_refs": canon_refs or [],
            "tags":       tags or [],
            "source":     source,
        }

    async def read(self, key: str, gaian_id: Optional[str] = None) -> Optional[Any]:
        entry = self._data.get(key)
        return entry["value"] if entry else None

    async def search(self, query: MemoryQuery) -> list[dict]:
        text = query.text.lower()
        results = []
        for key, entry in self._data.items():
            if (text in key.lower()
                    or text in str(entry["value"]).lower()
                    or any(text in t.lower() for t in entry.get("tags", []))):
                results.append({"key": key, "value": entry["value"], "_relevance": 0.9, "_recency": 0.3})
        return results

    async def evict_expired(self) -> int:
        return 0  # Semantic memory is permanent
