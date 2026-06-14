"""SQLAlchemy ORM models for the GAIA-OS Numerology module.

Three tables:
  gaia_numerology_profiles  — raw identity inputs (name + birthdate)
  gaia_numerology_charts    — computed chart header tied to a profile
  gaia_numerology_numbers   — one row per number position per chart

See canon/C160_Numerology_Vibrational_Identity_Engine.md for doctrinal context.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from gaia.db.base import Base

if TYPE_CHECKING:
    pass  # forward-reference guard


# ---------------------------------------------------------------------------
# NumerologyProfile
# ---------------------------------------------------------------------------

class NumerologyProfile(Base):
    """Stores the raw identity inputs (birth name + date) for a user.

    One profile per user per name/date combination.  Multiple charts can be
    computed from a single profile (e.g. re-runs, system upgrades).
    """

    __tablename__ = "gaia_numerology_profiles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="FK to Gaian user identity; NULL for anonymous/ephemeral sessions",
    )
    full_name = Column(
        String(512),
        nullable=False,
        comment="Full birth name as registered; source for Expression/Soul Urge/Personality",
    )
    # Normalised name stored separately so the engine never has to re-normalise
    # (strip accents, collapse whitespace, uppercase) at query time.
    normalized_name = Column(
        String(512),
        nullable=False,
        comment="Name after unicode normalisation and whitespace collapse, stored for fast diffing",
    )
    birth_date = Column(
        Date(),
        nullable=False,
        comment="ISO 8601 birth date used for Life Path and Personal Year",
    )
    system = Column(
        String(32),
        nullable=False,
        default="pythagorean",
        server_default="pythagorean",
        comment="Numerology system: 'pythagorean' (default) | 'chaldean' (future)",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    # Soft-delete per C139 (Right to Be Forgotten).  NULL = active.
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft-delete timestamp; NULL means active (C139 compliance)",
    )

    # Relationships
    charts: Mapped[List["NumerologyChart"]] = relationship(
        "NumerologyChart",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="NumerologyChart.created_at.desc()",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_gaia_numerology_profiles_user_id", "user_id"),
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def latest_chart(self) -> Optional["NumerologyChart"]:
        """Return the most recently computed chart, or None."""
        return self.charts[0] if self.charts else None

    def soft_delete(self) -> None:
        """Mark the profile as deleted without removing the row."""
        self.deleted_at = datetime.utcnow()

    def __repr__(self) -> str:
        return (
            f"<NumerologyProfile id={self.id!s:.8} "
            f"user={self.user_id!s:.8} "
            f"name={self.full_name!r:.30} "
            f"birth={self.birth_date}>"
        )


# ---------------------------------------------------------------------------
# NumerologyChart
# ---------------------------------------------------------------------------

class NumerologyChart(Base):
    """Computed numerology chart header for a profile.

    Stores the five core numbers, the Personal Year, master-number flags,
    and a raw JSONB payload for forward compatibility with new fields.

    Number positions are also broken out into NumerologyNumber rows for
    easy querying (e.g. "all users with Life Path 7").
    """

    __tablename__ = "gaia_numerology_charts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gaia_numerology_profiles.id", ondelete="CASCADE", name="fk_chart_profile"),
        nullable=False,
        index=True,
    )

    # Five core numbers ---------------------------------------------------
    life_path = Column(SmallInteger(), nullable=False)
    expression = Column(SmallInteger(), nullable=False)
    soul_urge = Column(SmallInteger(), nullable=False)
    personality = Column(SmallInteger(), nullable=False)
    birthday = Column(SmallInteger(), nullable=False)

    # Timing numbers ------------------------------------------------------
    personal_year = Column(
        SmallInteger(),
        nullable=False,
        comment="Personal Year at time of computation",
    )
    computed_for_year = Column(
        SmallInteger(),
        nullable=False,
        comment="Calendar year against which personal_year was computed",
    )

    # Master number flags -------------------------------------------------
    life_path_is_master = Column(Boolean(), nullable=False, default=False, server_default="false")
    expression_is_master = Column(Boolean(), nullable=False, default=False, server_default="false")
    soul_urge_is_master = Column(Boolean(), nullable=False, default=False, server_default="false")

    # Forward-compatibility payload ---------------------------------------
    raw_chart = Column(
        JSONB(astext_type=Text()),
        nullable=True,
        comment="Full chart serialised as JSONB; source of truth for fields not yet promoted to columns",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships -------------------------------------------------------
    profile: Mapped["NumerologyProfile"] = relationship(
        "NumerologyProfile",
        back_populates="charts",
    )
    numbers: Mapped[List["NumerologyNumber"]] = relationship(
        "NumerologyNumber",
        back_populates="chart",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index(
            "ix_gaia_numerology_charts_profile_created",
            "profile_id",
            "created_at",
        ),
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_number(self, number_type: str) -> Optional["NumerologyNumber"]:
        """Return the NumerologyNumber row for a given type, e.g. 'life_path'."""
        return next((n for n in self.numbers if n.number_type == number_type), None)

    def __repr__(self) -> str:
        return (
            f"<NumerologyChart id={self.id!s:.8} "
            f"profile={self.profile_id!s:.8} "
            f"lp={self.life_path} "
            f"year={self.personal_year}/{self.computed_for_year}>"
        )


# ---------------------------------------------------------------------------
# NumerologyNumber
# ---------------------------------------------------------------------------

# Canonical set of number position slugs (used as the number_type column value)
NUMBER_TYPE_LIFE_PATH = "life_path"
NUMBER_TYPE_EXPRESSION = "expression"
NUMBER_TYPE_SOUL_URGE = "soul_urge"
NUMBER_TYPE_PERSONALITY = "personality"
NUMBER_TYPE_BIRTHDAY = "birthday"
NUMBER_TYPE_PERSONAL_YEAR = "personal_year"
NUMBER_TYPE_CHALLENGE_1 = "challenge_1"
NUMBER_TYPE_CHALLENGE_2 = "challenge_2"
NUMBER_TYPE_CHALLENGE_3 = "challenge_3"
NUMBER_TYPE_CHALLENGE_MAIN = "challenge_main"

ALL_NUMBER_TYPES = (
    NUMBER_TYPE_LIFE_PATH,
    NUMBER_TYPE_EXPRESSION,
    NUMBER_TYPE_SOUL_URGE,
    NUMBER_TYPE_PERSONALITY,
    NUMBER_TYPE_BIRTHDAY,
    NUMBER_TYPE_PERSONAL_YEAR,
    NUMBER_TYPE_CHALLENGE_1,
    NUMBER_TYPE_CHALLENGE_2,
    NUMBER_TYPE_CHALLENGE_3,
    NUMBER_TYPE_CHALLENGE_MAIN,
)


class NumerologyNumber(Base):
    """One row per number position per chart.

    Stores the raw (pre-reduction) value, the final reduced value,
    whether it is a Master Number, and the full reduction path for
    auditability and UI step-by-step display.
    """

    __tablename__ = "gaia_numerology_numbers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    chart_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gaia_numerology_charts.id", ondelete="CASCADE", name="fk_number_chart"),
        nullable=False,
        index=True,
    )
    number_type = Column(
        String(32),
        nullable=False,
        comment="One of the NUMBER_TYPE_* constants; identifies the position in the chart",
    )
    raw_value = Column(
        Integer(),
        nullable=False,
        comment="Sum before any reduction is applied",
    )
    reduced_value = Column(
        SmallInteger(),
        nullable=False,
        comment="Final value after Pythagorean/Chaldean reduction (1-9, 11, 22, 33)",
    )
    is_master_number = Column(
        Boolean(),
        nullable=False,
        default=False,
        comment="True when the reduced value is 11, 22, or 33",
    )
    # JSON array of intermediate steps, e.g. [29, 11] or [38, 11] or [48, 12, 3]
    reduction_path = Column(
        JSONB(astext_type=Text()),
        nullable=False,
        comment="Ordered list of values from raw_value to reduced_value, inclusive",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    chart: Mapped["NumerologyChart"] = relationship(
        "NumerologyChart",
        back_populates="numbers",
    )

    __table_args__ = (
        UniqueConstraint(
            "chart_id",
            "number_type",
            name="uq_numerology_number_chart_type",
        ),
        Index("ix_gaia_numerology_numbers_chart_id", "chart_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<NumerologyNumber chart={self.chart_id!s:.8} "
            f"type={self.number_type} "
            f"value={self.reduced_value}"
            f"{'*' if self.is_master_number else ''}>"
        )
