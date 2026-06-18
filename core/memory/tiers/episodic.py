"""
core/memory/tiers/episodic.py

EPISODIC tier — in-process dict, default 30-day (720 h) TTL.
Stores tagged session summaries and experiential memories.

Canon: C34 (Memory Sovereignty)  Issue: #213
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore, MemoryTier

_DEFAULT_TTL_HOURS = MemoryTier.EPISODIC.default_ttl_hours  # 720.0


@dataclass
class _EpisodicEntry:
    value:      Any
    gaian_id:   str
    tags:       list[str]
    created_at: float   = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now > self.expires_at


class EpisodicMemoryStore(MemoryStore):
    """In-process episodic memory with tag support and TTL eviction."""

    _GLOBAL = "__global__"

    def __init__(self) -> None:
        # {(gaian_id, key): _EpisodicEntry}
        self._store: dict[tuple[str, str], _EpisodicEntry] = {}

    # ------------------------------------------------------------------ #
    # MemoryStore ABC
    # ------------------------------------------------------------------ #

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None,
        ttl_hours: Optional[float] = None,
        tags: Optional[list[str]] = None,
        **kwargs
    ) -> None:
        gid = gaian_id or self._GLOBAL
        ttl = ttl_hours if ttl_hours is not None else _DEFAULT_TTL_HOURS
        expires_at = (time.time() + ttl * 3600) if ttl > 0 else None
        self._store[(gid, key)] = _EpisodicEntry(
            value=value,
            gaian_id=gid,
            tags=tags or [],
            expires_at=expires_at,
        )

    async def read(
        self, key: str, gaian_id: Optional[str] = None
    ) -> Optional[Any]:
        gid = gaian_id or self._GLOBAL
        entry = self._store.get((gid, key))
        if entry is None:
            return None
        if entry.is_expired(time.time()):
            return None
        return entry.value

    async def search(self, query: MemoryQuery) -> list[dict]:
        gid = query.gaian_id or self._GLOBAL
        now = time.time()
        text = query.text.lower()
        results = []
        for (g, k), entry in self._store.items():
            if g != gid or entry.is_expired(now):
                continue
            haystack = f"{k} {entry.value} {' '.join(entry.tags)}".lower()
            relevance = 0.85 if text in haystack else 0.15
            age_sec = now - entry.created_at
            recency = max(0.0, 1.0 - age_sec / (_DEFAULT_TTL_HOURS * 3600))
            results.append({
                "key": k, "value": entry.value,
                "_relevance": relevance, "_recency": recency,
                "_tier": "episodic", "_tags": entry.tags,
            })
        return results

    async def evict_expired(self) -> int:
        now = time.time()
        stale = [k for k, e in self._store.items() if e.is_expired(now)]
        for k in stale:
            del self._store[k]
        return len(stale)
