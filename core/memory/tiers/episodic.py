"""
core/memory/tiers/episodic.py
Episodic Memory Tier — Sprint G-8

Stores session moments, stage transitions, and ceremony records.
Default TTL: 30 days (720 hours). In production this tier will be
backed by ArcadeDB / graph DB; this implementation uses an in-process
dict with TTL for Sprint G-8 — a graph-backed implementation is
scheduled for Sprint G-10 (Crystal DB integration, Issue #162).

Each episodic record is a dict with at minimum:
  {
    'key':         str,
    'value':       Any,   # The raw session/ceremony data
    'gaian_id':    str | None,
    'written_at':  float,  # Unix epoch
    'expires_at':  float | None,
    '_relevance':  float,  # set during search
    '_recency':    float,  # set during search
    'canon_refs':  list[str],
    'tags':        list[str],  # e.g. ['shadow-work', 'ceremony', 'identity-shift']
  }

Canon Refs: C34, C01
"""
from __future__ import annotations

import time
from typing import Any

from core.memory.hierarchy import MemoryQuery, MemoryTier

_DEFAULT_TTL_HOURS = MemoryTier.EPISODIC.default_ttl_hours  # 720.0


class EpisodicMemoryStore:
    """In-process episodic store with TTL, tags, and canon_refs.

    Sprint G-8 implementation. Graph-DB backend added in G-10.
    """

    def __init__(self) -> None:
        # {(gaian_id, key): record_dict}
        self._data: dict[tuple[str | None, str], dict] = {}

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
        tags: list[str] | None = None,
        canon_refs: list[str] | None = None,
    ) -> None:
        now = time.time()
        ttl = ttl_hours if ttl_hours is not None else _DEFAULT_TTL_HOURS
        expires_at = (now + ttl * 3600) if (ttl and ttl > 0) else None
        self._data[(gaian_id, key)] = {
            "key":        key,
            "value":      value,
            "gaian_id":   gaian_id,
            "written_at": now,
            "expires_at": expires_at,
            "canon_refs": canon_refs or ["C34"],
            "tags":       tags or [],
        }

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        record = self._data.get((gaian_id, key))
        if record is None:
            return None
        if record["expires_at"] and time.time() > record["expires_at"]:
            del self._data[(gaian_id, key)]
            return None
        return record["value"]

    async def search(self, query: MemoryQuery) -> list[dict]:
        now = time.time()
        needle = query.query_text.lower()
        results = []
        for (gid, k), record in self._data.items():
            if query.gaian_id and gid != query.gaian_id:
                continue
            if record["expires_at"] and now > record["expires_at"]:
                continue
            text = " ".join([
                str(record.get("value", "")),
                " ".join(record.get("tags", [])),
                " ".join(record.get("canon_refs", [])),
            ]).lower()
            relevance = 1.0 if needle and needle in text else 0.15
            age_days = (now - record["written_at"]) / 86400
            recency = 1.0 / (1.0 + age_days / 7.0)  # decays over weeks
            results.append({
                **record,
                "_relevance": relevance,
                "_recency":   recency,
            })
        return results

    async def evict_expired(self) -> int:
        now = time.time()
        expired = [
            k for k, r in self._data.items()
            if r["expires_at"] and now > r["expires_at"]
        ]
        for k in expired:
            del self._data[k]
        return len(expired)
