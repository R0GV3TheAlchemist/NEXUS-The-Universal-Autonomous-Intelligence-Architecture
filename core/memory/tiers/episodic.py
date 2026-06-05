"""
core/memory/tiers/episodic.py

EpisodicMemoryStore — in-process dict, 720 h (30 day) TTL default.
Stores session summaries, significant events, and ceremony records.
Issue: #213
"""

from __future__ import annotations

import time
from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore

_DEFAULT_TTL_HOURS = 720.0


class EpisodicMemoryStore(MemoryStore):
    def __init__(self, default_ttl_hours: float = _DEFAULT_TTL_HOURS) -> None:
        self._default_ttl = default_ttl_hours * 3600
        self._data: dict[str, dict] = {}  # key -> {value, gaian_id, expires_at, tags}

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None,
        ttl_hours: Optional[float] = None,
        tags: Optional[list[str]] = None,
        **kwargs,
    ) -> None:
        ttl = (ttl_hours * 3600) if ttl_hours is not None else self._default_ttl
        self._data[key] = {
            "value":      value,
            "gaian_id":   gaian_id,
            "expires_at": time.time() + ttl,
            "tags":       tags or [],
        }

    async def read(self, key: str, gaian_id: Optional[str] = None) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            return None
        if gaian_id and entry["gaian_id"] and entry["gaian_id"] != gaian_id:
            return None
        return entry["value"]

    async def search(self, query: MemoryQuery) -> list[dict]:
        now = time.time()
        text = query.text.lower()
        results = []
        for key, entry in self._data.items():
            if entry["expires_at"] <= now:
                continue
            if text in key.lower() or text in str(entry["value"]).lower():
                results.append({"key": key, "value": entry["value"], "_relevance": 0.6, "_recency": 0.6})
        return results

    async def evict_expired(self) -> int:
        now = time.time()
        expired = [k for k, e in self._data.items() if e["expires_at"] <= now]
        for k in expired:
            del self._data[k]
        return len(expired)
