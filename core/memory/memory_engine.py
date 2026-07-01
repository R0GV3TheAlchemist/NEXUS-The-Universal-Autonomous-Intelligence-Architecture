"""
GAIA Memory Engine — Core Store, CRUD & Staleness Integration
Issue #453

The heart of GAIA's sovereign persistent memory.
Handles create, read, update, delete, search, and
orthestrates staleness decay and contradiction detection.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, Session

from core.memory.memory_models import (
    Base, MemoryRecord, MemoryAuditLog,
    MemoryType, ConfidenceLevel, EvidenceLevel, SourceType
)
from core.memory.staleness import compute_staleness, detect_contradictions
from core.memory.sovereignty import SovereigntyLayer


class MemoryEngine:
    """
    GAIA Memory Engine.

    Provides sovereign, trauma-informed, falsifiable persistent memory
    across sessions. No other major AI system does all three.

    Usage:
        engine = MemoryEngine(db_url="sqlite:///gaia_memory.db")
        engine.remember(
            user_id="user@example.com",
            content="User resonates with Black Tourmaline for grounding.",
            type=MemoryType.EMOTIONAL,
            session_id="session-abc"
        )
    """

    def __init__(self, db_url: str = "sqlite:///gaia_memory.db"):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.sovereignty = SovereigntyLayer(self.SessionLocal)

    def _hash_user_id(self, user_id: str) -> str:
        """Anonymise user identity. No PII stored raw."""
        return hashlib.sha256(user_id.encode()).hexdigest()

    def _audit(self, db: Session, memory_id: str, user_id_hash: str,
               action: str, actor: str, session_id: Optional[str] = None,
               details: Optional[Dict] = None):
        """Write an immutable audit log entry."""
        log = MemoryAuditLog(
            log_id=str(uuid.uuid4()),
            memory_id=memory_id,
            user_id_hash=user_id_hash,
            action=action,
            actor=actor,
            session_id=session_id,
            details=details or {}
        )
        db.add(log)

    def remember(
        self,
        user_id: str,
        content: str,
        type: MemoryType,
        session_id: Optional[str] = None,
        space_id: Optional[str] = None,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        evidence_level: EvidenceLevel = EvidenceLevel.GAIAN_OBSERVED,
        source_type: SourceType = SourceType.CONVERSATION,
        trauma_flags: Optional[List[str]] = None,
        never_clinical: bool = False,
        requires_opt_in: bool = False,
        canon_refs: Optional[List[str]] = None,
        correspondence_refs: Optional[Dict] = None,
    ) -> MemoryRecord:
        """
        Create a new memory record.

        Automatically:
        - Checks requires_opt_in consent
        - Detects contradictions with existing memories
        - Writes audit log entry
        - Returns the created record
        """
        user_id_hash = self._hash_user_id(user_id)

        with self.SessionLocal() as db:
            # Consent gate
            if requires_opt_in:
                if not self.sovereignty.has_consent(user_id_hash, type):
                    raise PermissionError(
                        f"Memory type '{type}' requires opt-in consent from user."
                    )

            memory_id = str(uuid.uuid4())

            record = MemoryRecord(
                memory_id=memory_id,
                user_id_hash=user_id_hash,
                space_id=space_id,
                type=type,
                content=content,
                confidence=confidence,
                evidence_level=evidence_level,
                created_at=datetime.utcnow(),
                last_reinforced=datetime.utcnow(),
                staleness_score=0.0,
                requires_opt_in=requires_opt_in,
                trauma_flags=trauma_flags or [],
                never_clinical=never_clinical,
                source_session_id=session_id,
                source_type=source_type,
                canon_refs=canon_refs or [],
                correspondence_refs=correspondence_refs or {},
                user_overridable=True,
                user_deletable=True,
                exportable=True,
            )

            # Contradiction detection
            contradictions = detect_contradictions(db, user_id_hash, content, type)
            if contradictions:
                record.contradiction_candidates = [c.memory_id for c in contradictions]

            db.add(record)

            self._audit(
                db, memory_id, user_id_hash,
                action="create", actor="system",
                session_id=session_id,
                details={"type": type.value, "confidence": confidence.value}
            )

            db.commit()
            db.refresh(record)
            return record

    def recall(
        self,
        user_id: str,
        query: Optional[str] = None,
        type: Optional[MemoryType] = None,
        space_id: Optional[str] = None,
        exclude_trauma: bool = True,
        max_staleness: float = 0.85,
        limit: int = 20,
    ) -> List[MemoryRecord]:
        """
        Retrieve memories for a user.

        Trauma-informed: by default, never surfaces memories
        with trauma_flags unless explicitly requested.

        Staleness-filtered: memories above max_staleness threshold
        are excluded from retrieval by default.
        """
        user_id_hash = self._hash_user_id(user_id)

        with self.SessionLocal() as db:
            q = db.query(MemoryRecord).filter(
                MemoryRecord.user_id_hash == user_id_hash,
                MemoryRecord.superseded_by.is_(None),
                MemoryRecord.staleness_score <= max_staleness,
            )

            if type:
                q = q.filter(MemoryRecord.type == type)

            if space_id:
                q = q.filter(
                    or_(MemoryRecord.space_id == space_id,
                        MemoryRecord.space_id.is_(None))
                )

            if exclude_trauma:
                # Only return memories with empty trauma_flags
                # This is the trauma-informed non-surfacing guarantee
                q = q.filter(MemoryRecord.trauma_flags == [])

            records = q.order_by(
                MemoryRecord.staleness_score.asc(),
                MemoryRecord.last_reinforced.desc()
            ).limit(limit).all()

            return records

    def reinforce(
        self,
        user_id: str,
        memory_id: str,
        session_id: Optional[str] = None
    ) -> MemoryRecord:
        """Reinforce a memory — resets staleness, updates last_reinforced."""
        user_id_hash = self._hash_user_id(user_id)

        with self.SessionLocal() as db:
            record = db.query(MemoryRecord).filter(
                MemoryRecord.memory_id == memory_id,
                MemoryRecord.user_id_hash == user_id_hash
            ).first()

            if not record:
                raise ValueError(f"Memory {memory_id} not found for this user.")

            record.last_reinforced = datetime.utcnow()
            record.staleness_score = 0.0

            self._audit(
                db, memory_id, user_id_hash,
                action="reinforce", actor="system",
                session_id=session_id
            )

            db.commit()
            db.refresh(record)
            return record

    def correct(
        self,
        user_id: str,
        memory_id: str,
        new_content: str,
        session_id: Optional[str] = None
    ) -> MemoryRecord:
        """
        User-initiated memory correction.
        Supersedes the old record and creates a corrected one.
        Does NOT silently overwrite — full audit trail maintained.
        """
        user_id_hash = self._hash_user_id(user_id)

        with self.SessionLocal() as db:
            old = db.query(MemoryRecord).filter(
                MemoryRecord.memory_id == memory_id,
                MemoryRecord.user_id_hash == user_id_hash
            ).first()

            if not old:
                raise ValueError(f"Memory {memory_id} not found for this user.")

            if not old.user_overridable:
                raise PermissionError(f"Memory {memory_id} is not user-overridable.")

            new_id = str(uuid.uuid4())
            corrected = MemoryRecord(
                memory_id=new_id,
                user_id_hash=user_id_hash,
                space_id=old.space_id,
                type=old.type,
                content=new_content,
                confidence=ConfidenceLevel.HIGH,
                evidence_level=EvidenceLevel.GAIAN_OBSERVED,
                created_at=datetime.utcnow(),
                last_reinforced=datetime.utcnow(),
                staleness_score=0.0,
                requires_opt_in=old.requires_opt_in,
                trauma_flags=old.trauma_flags,
                never_clinical=old.never_clinical,
                source_session_id=session_id,
                source_type=SourceType.USER_CORRECTION,
                canon_refs=old.canon_refs,
                correspondence_refs=old.correspondence_refs,
                user_overridable=True,
                user_deletable=True,
                exportable=True,
            )
            db.add(corrected)

            old.superseded_by = new_id
            self._audit(
                db, memory_id, user_id_hash,
                action="correction", actor="user",
                session_id=session_id,
                details={"superseded_by": new_id, "new_content_preview": new_content[:80]}
            )
            self._audit(
                db, new_id, user_id_hash,
                action="create", actor="user",
                session_id=session_id,
                details={"source": "user_correction", "corrects": memory_id}
            )

            db.commit()
            db.refresh(corrected)
            return corrected

    def decay_all(self, user_id: str) -> int:
        """Run staleness decay across all memories for this user. Returns count updated."""
        user_id_hash = self._hash_user_id(user_id)

        with self.SessionLocal() as db:
            records = db.query(MemoryRecord).filter(
                MemoryRecord.user_id_hash == user_id_hash,
                MemoryRecord.superseded_by.is_(None)
            ).all()

            updated = 0
            for record in records:
                new_score = compute_staleness(
                    last_reinforced=record.last_reinforced or record.created_at,
                    confidence=record.confidence,
                    evidence_level=record.evidence_level
                )
                if abs(new_score - record.staleness_score) > 0.001:
                    record.staleness_score = new_score
                    updated += 1

            db.commit()
            return updated

    def delete(
        self,
        user_id: str,
        memory_id: str,
        session_id: Optional[str] = None
    ) -> bool:
        """User-deletable sovereignty guarantee."""
        user_id_hash = self._hash_user_id(user_id)

        with self.SessionLocal() as db:
            record = db.query(MemoryRecord).filter(
                MemoryRecord.memory_id == memory_id,
                MemoryRecord.user_id_hash == user_id_hash
            ).first()

            if not record:
                raise ValueError(f"Memory {memory_id} not found for this user.")

            if not record.user_deletable:
                raise PermissionError(f"Memory {memory_id} is not user-deletable.")

            self._audit(
                db, memory_id, user_id_hash,
                action="delete", actor="user",
                session_id=session_id
            )

            db.delete(record)
            db.commit()
            return True
