"""SQLite-backed Stewardship Repository — SQLAlchemy 2.x.

Canon References: C17 (Persistent Memory), C18 (ATLAS Node Stewardship)
Issue: #440 (Session Bootstrap infra)

Migrated to SQLAlchemy 2.x:
  - All session.execute() raw SQL wrapped in text()
  - session.query() replaced with select() + session.scalars()
  - engine.connect() replaced with engine.begin()
  - get_session() context manager from core.infra.database used throughout
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, Float, select, text
from sqlalchemy.orm import Mapped, mapped_column

from core.infra.database import Base, get_session


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

class ATLASNodeStewardshipRecord(Base):
    """Persists a Gaian's stewardship relationship with an ATLAS Node."""

    __tablename__ = "atlas_node_stewardship"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    gaian_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    architect_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    atlas_node_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    stewardship_type: Mapped[str] = mapped_column(String(64), nullable=False, default="OBSERVE")
    health_score_at_registration: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gaian_id": self.gaian_id,
            "architect_id": self.architect_id,
            "atlas_node_id": self.atlas_node_id,
            "stewardship_type": self.stewardship_type,
            "health_score_at_registration": self.health_score_at_registration,
            "notes": self.notes,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "last_interaction_at": (
                self.last_interaction_at.isoformat() if self.last_interaction_at else None
            ),
        }


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class SQLiteStewardshipRepository:
    """CRUD repository for ATLASNodeStewardshipRecord using SQLAlchemy 2.x."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: ATLASNodeStewardshipRecord) -> None:
        """Insert or update a stewardship record."""
        with get_session() as session:
            existing = session.scalars(
                select(ATLASNodeStewardshipRecord).where(
                    ATLASNodeStewardshipRecord.gaian_id == record.gaian_id,
                    ATLASNodeStewardshipRecord.atlas_node_id == record.atlas_node_id,
                )
            ).first()
            if existing is None:
                session.add(record)
            else:
                existing.stewardship_type = record.stewardship_type
                existing.notes = record.notes
                existing.last_interaction_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_gaian_id(self, gaian_id: str) -> List[ATLASNodeStewardshipRecord]:
        """All stewardship records for a given Gaian."""
        with get_session() as session:
            return list(
                session.scalars(
                    select(ATLASNodeStewardshipRecord).where(
                        ATLASNodeStewardshipRecord.gaian_id == gaian_id
                    )
                ).all()
            )

    def get_by_atlas_node_id(self, atlas_node_id: str) -> List[ATLASNodeStewardshipRecord]:
        """All stewardship records for a given ATLAS Node."""
        with get_session() as session:
            return list(
                session.scalars(
                    select(ATLASNodeStewardshipRecord).where(
                        ATLASNodeStewardshipRecord.atlas_node_id == atlas_node_id
                    )
                ).all()
            )

    def list_all(self) -> List[ATLASNodeStewardshipRecord]:
        """Return all stewardship records."""
        with get_session() as session:
            return list(session.scalars(select(ATLASNodeStewardshipRecord)).all())

    def count(self) -> int:
        """Return total number of stewardship records."""
        with get_session() as session:
            result = session.execute(text("SELECT COUNT(*) FROM atlas_node_stewardship"))
            row = result.fetchone()
            return row[0] if row else 0

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, gaian_id: str, atlas_node_id: str) -> None:
        """Delete a stewardship record by gaian+node composite key."""
        with get_session() as session:
            record = session.scalars(
                select(ATLASNodeStewardshipRecord).where(
                    ATLASNodeStewardshipRecord.gaian_id == gaian_id,
                    ATLASNodeStewardshipRecord.atlas_node_id == atlas_node_id,
                )
            ).first()
            if record is not None:
                session.delete(record)
