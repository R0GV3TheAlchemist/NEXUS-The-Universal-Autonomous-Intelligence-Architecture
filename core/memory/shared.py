"""M4 Shared Memory Store — Canon C17: explicitly authorised cross-instance shared context.

Shared memory requires explicit multi-Principal authorisation.
It is the bridge between Gaian instances — used for collective intelligence,
collaborative sessions, and Noosphere-level pattern sharing.

C17: M4 requires explicit multi-Principal authorisation.
"""

from __future__ import annotations

from typing import Any, Optional

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag


class SharedMemoryStore:
    """M4: Cross-instance shared context with explicit multi-Principal authorisation."""

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        # authorisation_log: record_id -> list of authorising HP IDs
        self._authorisations: dict[str, set[str]] = {}

    def store(
        self,
        content: str,
        session_id: str,
        authorising_principals: list[str],
        gaian_id: str,
        tags: Optional[list[MemoryTag]] = None,
        structured_data: Optional[dict[str, Any]] = None,
        confidence: float = 0.9,
        canon_ref: Optional[str] = None,
    ) -> MemoryRecord:
        """Store a shared memory record. Requires at least two authorising principals."""
        if len(authorising_principals) < 2:
            raise ValueError(
                "M4 Shared Memory requires explicit multi-Principal authorisation. "
                f"Provided: {len(authorising_principals)} principal(s). Minimum: 2."
            )
        record = MemoryRecord(
            layer=MemoryLayer.M4_SHARED,
            scope=MemoryScope.SHARED,
            gaian_id=gaian_id,
            human_principal_id=authorising_principals[0],  # Primary authoriser
            session_id=session_id,
            content=content,
            structured_data=structured_data or {},
            tags=tags or [],
            confidence=confidence,
            source="MULTI_PRINCIPAL",
            canon_ref=canon_ref,
        )
        self._records[record.id] = record
        self._authorisations[record.id] = set(authorising_principals)
        return record

    def get_authorisations(self, record_id: str) -> set[str]:
        """Return the set of HP IDs that authorised this shared record."""
        return set(self._authorisations.get(record_id, set()))

    def accessible_by(self, human_principal_id: str) -> list[MemoryRecord]:
        """Return all active shared records accessible to a given HP."""
        result = []
        for record in self._records.values():
            if not record.is_active:
                continue
            if human_principal_id in self._authorisations.get(record.id, set()):
                result.append(record)
        return result

    def revoke(self, record_id: str, audit_id: str) -> bool:
        record = self._records.get(record_id)
        if not record or not record.is_active:
            return False
        record.revoke(audit_id)
        return True

    def all(self, active_only: bool = True) -> list[MemoryRecord]:
        records = list(self._records.values())
        if active_only:
            records = [r for r in records if r.is_active]
        return records

    def count(self) -> int:
        return len(self.all())

    def __repr__(self) -> str:
        return f"<SharedMemoryStore records={self.count()}>"
