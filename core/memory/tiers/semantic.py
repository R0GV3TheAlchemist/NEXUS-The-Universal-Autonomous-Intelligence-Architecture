"""
core/memory/tiers/semantic.py
Semantic Memory Tier — Sprint G-8

Permanent store for canon facts, Crystal DB knowledge graph nodes,
and domain-level truths. No TTL expiry.

In production this tier is backed by the Crystal Knowledge Graph
(Issue #162). This sprint ships an in-process dict stub that satisfies
the MemoryStore protocol so the full hierarchy can be tested end-to-end
before the graph backend is wired.

Semantic records are expected to carry:
  {
    'key':        str,   # e.g. 'canon:C32', 'crystal:node:solfeggio-mi'
    'value':      Any,
    'canon_refs': list[str],
    'source':     str,   # 'crystal_db' | 'canon_loader' | 'manual'
    'tags':       list[str],
  }

Canon Refs: C34, C01
"""
from __future__ import annotations

import time
from typing import Any

from core.memory.hierarchy import MemoryQuery


class SemanticMemoryStore:
    """In-process semantic store (Crystal DB stub for Sprint G-8)."""

    def __init__(self) -> None:
        # {key: record_dict}  (no gaian scoping — semantic memory is universal)
        self._data: dict[str, dict] = {}

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,  # ignored — semantic memory is global
        ttl_hours: float | None = None,  # ignored — semantic memory is permanent
        canon_refs: list[str] | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
    ) -> None:
        self._data[key] = {
            "key":        key,
            "value":      value,
            "canon_refs": canon_refs or ["C34"],
            "source":     source,
            "tags":       tags or [],
            "written_at": time.time(),
        }

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        record = self._data.get(key)
        return record["value"] if record else None

    async def search(self, query: MemoryQuery) -> list[dict]:
        needle = query.query_text.lower()
        results = []
        for k, record in self._data.items():
            text = " ".join([
                str(record.get("value", "")),
                k,
                " ".join(record.get("tags", [])),
                " ".join(record.get("canon_refs", [])),
            ]).lower()
            relevance = 1.0 if needle and needle in text else 0.1
            results.append({
                **record,
                "_relevance": relevance,
                "_recency":   1.0,  # semantic memory has no recency decay
            })
        return results

    async def evict_expired(self) -> int:
        return 0  # semantic memory never expires
