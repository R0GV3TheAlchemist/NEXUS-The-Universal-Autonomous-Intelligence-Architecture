"""M2 Semantic Memory Store — Canon C17: accumulated knowledge and world model state.

Semantic memory is GAIA's growing understanding of the world —
not what happened (episodic), but what IS known.
Updated only from verified World Fabric data or HP-authorised sources.

Examples:
  - "The Edwards Aquifer recharge rate has declined 12% since 2020"
  - "Kyle prefers concise responses under high cognitive load"
  - "San Antonio is in the Balcones Fault Zone"
"""

from __future__ import annotations

from typing import Any, Optional

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag


class SemanticMemoryStore:
    """M2: Accumulated knowledge and world model state.

    Semantic records are keyed by a `concept` — a normalised string
    that identifies the knowledge claim. This prevents duplication
    and allows clean updates when a fact changes.

    Confidence is mandatory — M2 must never assert unverified knowledge
    as fact (C14 World Fabric governance: model output is not fact).
    """

    def __init__(self, gaian_id: str, human_principal_id: str) -> None:
        self.gaian_id = gaian_id
        self.human_principal_id = human_principal_id
        self._records: dict[str, MemoryRecord] = {}        # record_id -> record
        self._concept_index: dict[str, str] = {}           # concept -> record_id

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def assert_fact(
        self,
        concept: str,
        content: str,
        session_id: str,
        confidence: float = 0.9,
        source: str = "WORLD_FABRIC",
        structured_data: Optional[dict[str, Any]] = None,
        tags: Optional[list[MemoryTag]] = None,
        canon_ref: Optional[str] = None,
    ) -> MemoryRecord:
        """Assert or update a semantic fact.

        If a record for this concept already exists, it is superseded
        (revoked) and replaced with the new assertion.
        confidence must be in [0.0, 1.0].
        """
        concept_key = concept.strip().lower()
        existing_id = self._concept_index.get(concept_key)
        if existing_id:
            existing = self._records.get(existing_id)
            if existing and existing.is_active:
                existing.revoke(audit_id="SUPERSEDED_BY_UPDATE")

        record = MemoryRecord(
            layer=MemoryLayer.M2_SEMANTIC,
            scope=MemoryScope.PRIVATE,
            gaian_id=self.gaian_id,
            human_principal_id=self.human_principal_id,
            session_id=session_id,
            content=content,
            structured_data=structured_data or {},
            tags=tags or [MemoryTag.FACTUAL],
            confidence=max(0.0, min(1.0, confidence)),
            source=source,
            canon_ref=canon_ref,
        )
        self._records[record.id] = record
        self._concept_index[concept_key] = record.id
        return record

    def revoke_fact(self, concept: str, audit_id: str) -> bool:
        """Revoke a semantic fact by concept key."""
        concept_key = concept.strip().lower()
        record_id = self._concept_index.get(concept_key)
        if not record_id:
            return False
        record = self._records.get(record_id)
        if not record or not record.is_active:
            return False
        record.revoke(audit_id)
        return True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_fact(self, concept: str) -> Optional[MemoryRecord]:
        """Retrieve the current (active) record for a concept."""
        concept_key = concept.strip().lower()
        record_id = self._concept_index.get(concept_key)
        if not record_id:
            return None
        record = self._records.get(record_id)
        if record and record.is_active:
            return record
        return None

    def all(self, active_only: bool = True) -> list[MemoryRecord]:
        records = list(self._records.values())
        if active_only:
            records = [r for r in records if r.is_active]
        return sorted(records, key=lambda r: r.created_at)

    def above_confidence(
        self, threshold: float = 0.7, active_only: bool = True
    ) -> list[MemoryRecord]:
        """Return only records meeting a minimum confidence threshold."""
        return [r for r in self.all(active_only) if r.confidence >= threshold]

    def by_tag(self, tag: MemoryTag, active_only: bool = True) -> list[MemoryRecord]:
        return [r for r in self.all(active_only) if tag in r.tags]

    def count(self, active_only: bool = True) -> int:
        return len(self.all(active_only))

    def __repr__(self) -> str:
        return (
            f"<SemanticMemoryStore gaian={self.gaian_id[:8]} "
            f"facts={self.count()}>"
        )
