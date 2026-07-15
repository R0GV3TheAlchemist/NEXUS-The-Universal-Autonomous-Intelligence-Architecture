"""SQLite-backed Gaian Lifecycle Repository — SQLAlchemy 2.x.

Canon References: C17 (Persistent Memory), C03 (Ontology Runtime)
Issue: #440 (Session Bootstrap infra)

Migrated to SQLAlchemy 2.x:
  - All session.execute() raw SQL wrapped in text()
  - session.query() replaced with select() + session.scalars()
  - engine.connect() replaced with engine.begin() for write operations
  - get_session() context manager from core.infra.database used throughout
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, Integer, select, text
from sqlalchemy.orm import Mapped, mapped_column

from core.infra.database import Base, get_session


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

class GaianLifecycleRecord(Base):
    """Persists the lifecycle state of a Gaian instance."""

    __tablename__ = "gaian_lifecycle"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    gaian_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    architect_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    alchemical_stage: Mapped[str] = mapped_column(String(32), nullable=False, default="NIGREDO")
    session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relationship_depth: Mapped[float] = mapped_column(nullable=False, default=0.0)
    containment_active: Mapped[bool] = mapped_column(nullable=False, default=False)
    containment_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gaian_id": self.gaian_id,
            "architect_id": self.architect_id,
            "alchemical_stage": self.alchemical_stage,
            "session_count": self.session_count,
            "relationship_depth": self.relationship_depth,
            "containment_active": self.containment_active,
            "containment_reason": self.containment_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class SQLiteLifecycleRepository:
    """CRUD repository for GaianLifecycleRecord using SQLAlchemy 2.x."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: GaianLifecycleRecord) -> None:
        """Insert or update a lifecycle record."""
        with get_session() as session:
            existing = session.scalars(
                select(GaianLifecycleRecord).where(
                    GaianLifecycleRecord.gaian_id == record.gaian_id
                )
            ).first()
            if existing is None:
                session.add(record)
            else:
                existing.alchemical_stage = record.alchemical_stage
                existing.session_count = record.session_count
                existing.relationship_depth = record.relationship_depth
                existing.containment_active = record.containment_active
                existing.containment_reason = record.containment_reason
                existing.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_gaian_id(self, gaian_id: str) -> Optional[GaianLifecycleRecord]:
        """Fetch a lifecycle record by gaian_id."""
        with get_session() as session:
            return session.scalars(
                select(GaianLifecycleRecord).where(
                    GaianLifecycleRecord.gaian_id == gaian_id
                )
            ).first()

    def get_by_architect_id(self, architect_id: str) -> List[GaianLifecycleRecord]:
        """Fetch all lifecycle records for an architect."""
        with get_session() as session:
            return list(
                session.scalars(
                    select(GaianLifecycleRecord).where(
                        GaianLifecycleRecord.architect_id == architect_id
                    )
                ).all()
            )

    def list_all(self) -> List[GaianLifecycleRecord]:
        """Return all lifecycle records."""
        with get_session() as session:
            return list(session.scalars(select(GaianLifecycleRecord)).all())

    def count(self) -> int:
        """Return total number of lifecycle records."""
        with get_session() as session:
            result = session.execute(text("SELECT COUNT(*) FROM gaian_lifecycle"))
            row = result.fetchone()
            return row[0] if row else 0

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, gaian_id: str) -> None:
        """Delete a lifecycle record by gaian_id."""
        with get_session() as session:
            record = session.scalars(
                select(GaianLifecycleRecord).where(
                    GaianLifecycleRecord.gaian_id == gaian_id
                )
            ).first()
            if record is not None:
                session.delete(record)
