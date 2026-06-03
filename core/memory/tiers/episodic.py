"""
core/memory/tiers/episodic.py
EpisodicMemoryStore — in-memory, tag-indexed, TTL-aware (days–weeks).

Stores life-moment records with optional tags. Eviction is lazy
(checked on every read) plus explicit via evict_expired().

Canon refs: C34, C01
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Episode:
    gaian_id:   str | None
    key:        str
    value:      Any
    tags:       list[str]
    created_at: float
    expires_at: float | None  # None = permanent


class EpisodicMemoryStore:
    """In-memory episodic store with tag indexing and TTL expiry."""

    DEFAULT_TTL_HOURS = 720.0  # 30 days

    def __init__(self) -> None:
        # keyed by (gaian_id, key)
        self._episodes: dict[tuple[str | None, str], _Episode] = {}

    def _now(self) -> float:
        return time.time()

    def _expired(self, ep: _Episode) -> bool:
        return ep.expires_at is not None and ep.expires_at < self._now()

    # ── MemoryStore Protocol ───────────────────────────────────────── #

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
        tags: list[str] | None = None,
    ) -> None:
        ttl = ttl_hours if ttl_hours is not None else self.DEFAULT_TTL_HOURS
        now = self._now()
        expires = now + ttl * 3600 if ttl > 0 else None
        self._episodes[(gaian_id, key)] = _Episode(
            gaian_id=gaian_id,
            key=key,
            value=value,
            tags=tags or [],
            created_at=now,
            expires_at=expires,
        )

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,
    ) -> Any | None:
        ep = self._episodes.get((gaian_id, key))
        if ep is None or self._expired(ep):
            return None
        return ep.value

    async def search(
        self,
        query: Any,
    ) -> list[dict]:
        text = getattr(query, "query_text", "").lower()
        gid  = getattr(query, "gaian_id", None)
        now  = self._now()
        results = []
        for ep in self._episodes.values():
            if self._expired(ep):
                continue
            if gid is not None and ep.gaian_id != gid:
                continue
            haystack = (ep.key + " " + str(ep.value) + " " + " ".join(ep.tags)).lower()
            rel = 0.8 if text and text in haystack else 0.3
            age_score = max(0.0, 1.0 - (now - ep.created_at) / (720 * 3600))
            results.append({
                "key": ep.key,
                "value": ep.value,
                "tags": ep.tags,
                "_relevance": rel,
                "_recency":   age_score,
            })
        return results

    async def evict_expired(self) -> int:
        stale = [k for k, ep in self._episodes.items() if self._expired(ep)]
        for k in stale:
            del self._episodes[k]
        return len(stale)
