"""M1 Episodic Memory Store — Canon C17: records of specific sessions and events.

Episodic memory is the Gaian Twin's autobiographical record.
It stores what happened, when, and in what session.
Persisted only with Human Principal consent at session close.

This is the primary layer that bridges sessions — without it, GAIA has amnesia.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag


class EpisodicMemoryStore:
    """M1: Persistent autobiographical record of sessions and events.

    Backed by an in-memory store (production would swap this for a
    database backend — SQLite, PostgreSQL, or a vector store).
    The interface is backend-agnostic by design.
    """

    def __init__(self, gaian_id: str, human_principal_id: str) -> None:
        self.gaian_id = gaian_id
        self.human_principal_id = human_principal_id
        self._records: dict[str, MemoryRecord] = {}  # id -> record
        self._session_index: dict[str, list[str]] = {}  # session_id -> [record_ids]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(
        self,
        content: str,
        session_id: str,
        tags: Optional[list[MemoryTag]] = None,
        structured_data: Optional[dict[str, Any]] = None,
        confidence: float = 1.0,
        source: str = "SESSION",
        canon_ref: Optional[str] = None,
    ) -> MemoryRecord:
        """Store a new episodic memory record."""
        record = MemoryRecord(
            layer=MemoryLayer.M1_EPISODIC,
            scope=MemoryScope.PRIVATE,
            gaian_id=self.gaian_id,
            human_principal_id=self.human_principal_id,
            session_id=session_id,
            content=content,
            structured_data=structured_data or {},
            tags=tags or [],
            confidence=confidence,
            source=source,
            canon_ref=canon_ref,
        )
        self._records[record.id] = record
        self._session_index.setdefault(session_id, []).append(record.id)
        return record

    def transfer_from_buffer(
        self,
        buffer_records: list[MemoryRecord],
        session_id: str,
        filter_tags: Optional[list[MemoryTag]] = None,
    ) -> list[MemoryRecord]:
        """Transfer records from M0 SessionBuffer into M1.

        Only active records are transferred.
        If filter_tags is provided, only records with at least one matching tag
        are transferred — allowing the HP to be selective.
        """
        transferred = []
        for r in buffer_records:
            if not r.is_active:
                continue
            if filter_tags and not any(t in r.tags for t in filter_tags):
                continue
            promoted = MemoryRecord(
                layer=MemoryLayer.M1_EPISODIC,
                scope=r.scope,
                gaian_id=self.gaian_id,
                human_principal_id=self.human_principal_id,
                session_id=session_id,
                content=r.content,
                structured_data=r.structured_data,
                tags=r.tags,
                confidence=r.confidence,
                source=r.source,
                canon_ref=r.canon_ref,
            )
            self._records[promoted.id] = promoted
            self._session_index.setdefault(session_id, []).append(promoted.id)
            transferred.append(promoted)
        return transferred

    def revoke(
        self,
        record_id: str,
        audit_id: str,
    ) -> bool:
        """Revoke a specific memory record. Returns True if found and revoked."""
        record = self._records.get(record_id)
        if not record:
            return False
        record.revoke(audit_id)
        return True

    def revoke_session(
        self,
        session_id: str,
        audit_id: str,
    ) -> int:
        """Revoke all records from a specific session. Returns count revoked."""
        record_ids = self._session_index.get(session_id, [])
        count = 0
        for rid in record_ids:
            record = self._records.get(rid)
            if record and record.is_active:
                record.revoke(audit_id)
                count += 1
        return count

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        return self._records.get(record_id)

    def all(self, active_only: bool = True) -> list[MemoryRecord]:
        """All episodic records, sorted oldest-first."""
        records = list(self._records.values())
        if active_only:
            records = [r for r in records if r.is_active]
        return sorted(records, key=lambda r: r.created_at)

    def by_session(self, session_id: str, active_only: bool = True) -> list[MemoryRecord]:
        """All records from a specific session."""
        ids = self._session_index.get(session_id, [])
        records = [self._records[rid] for rid in ids if rid in self._records]
        if active_only:
            records = [r for r in records if r.is_active]
        return sorted(records, key=lambda r: r.created_at)

    def by_tag(self, tag: MemoryTag, active_only: bool = True) -> list[MemoryRecord]:
        """All records with a specific tag."""
        return [
            r for r in self.all(active_only)
            if tag in r.tags
        ]

    def sessions(self) -> list[str]:
        """All session IDs that have episodic records."""
        return list(self._session_index.keys())

    def count(self, active_only: bool = True) -> int:
        return len(self.all(active_only))

    def __repr__(self) -> str:
        return (
            f"<EpisodicMemoryStore gaian={self.gaian_id[:8]} "
            f"records={self.count()} sessions={len(self.sessions())}>"
        )
