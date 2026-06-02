"""
core/memory/tiers/long_term.py
Long-Term Memory Tier — Sprint G-8

Permanent store for Gaian identity, settled personality arcs,
and the core relationship map. No TTL expiry.

In production this tier is backed by the Gaian profile store
(Tauri Store plugin / SQLite sidecar). This sprint ships an
in-process dict stub that satisfies the MemoryStore protocol.

Long-term records are expected to carry:
  {
    'key':         str,   # e.g. 'identity:core', 'arc:individuation'
    'value':       Any,
    'gaian_id':    str,
    'arc_type':    str,   # 'identity' | 'personality' | 'relationship'
    'settled_at':  float, # Unix epoch when this arc was considered settled
    'canon_refs':  list[str],
  }

Canon Refs: C34, C01
"""
from __future__ import annotations

import time
from typing import Any

from core.memory.hierarchy import MemoryQuery


class LongTermMemoryStore:
    """In-process long-term store (Tauri Store stub for Sprint G-8)."""

    def __init__(self) -> None:
        # {(gaian_id, key): record_dict}  (always gaian-scoped)
        self._data: dict[tuple[str | None, str], dict] = {}

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,  # ignored — long-term is permanent
        arc_type: str = "identity",
        canon_refs: list[str] | None = None,
    ) -> None:
        self._data[(gaian_id, key)] = {
            "key":        key,
            "value":      value,
            "gaian_id":   gaian_id,
            "arc_type":   arc_type,
            "settled_at": time.time(),
            "canon_refs": canon_refs or ["C34"],
        }

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        record = self._data.get((gaian_id, key))
        return record["value"] if record else None

    async def search(self, query: MemoryQuery) -> list[dict]:
        needle = query.query_text.lower()
        results = []
        for (gid, k), record in self._data.items():
            if query.gaian_id and gid != query.gaian_id:
                continue
            text = " ".join([
                str(record.get("value", "")),
                record.get("arc_type", ""),
                " ".join(record.get("canon_refs", [])),
            ]).lower()
            relevance = 1.0 if needle and needle in text else 0.1
            results.append({
                **record,
                "_relevance": relevance,
                "_recency":   1.0,  # long-term memory has no recency decay
            })
        return results

    async def evict_expired(self) -> int:
        return 0  # long-term memory never expires
