"""SQLAlchemy ORM models for the crystal_correspondence system — v2.0.

The CrystalCorrespondence model maps every column introduced by the v1.0
and v2.0 Alembic migrations. All v2.0 columns are nullable so existing
v1.0 records remain valid.

Key design decisions
--------------------
* Indexed scalar columns exist for every axis that drives frequent filter/sort
  queries (color, frequency, alchemical stage, chakra, coherence, etc.).
* JSONB columns hold the full rich payload for each correspondence axis.
  They are indexed via GIN in the DB (see migration) and exposed as typed
  Python dicts here.
* Helper methods on CrystalCorrespondence provide a clean API for the
  ingestion pipeline, test suite, and engine integrations — so nothing
  needs to manually dig into raw JSONB keys.
* The ProvenanceLog model is unchanged from v1.0 (backward compatible).
"""
from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer,
    Numeric, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CrystalCorrespondence(Base):
    """One row per crystal subject_id.  v2.0 schema."""

    __tablename__ = "crystal_correspondence"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Core identity ────────────────────────────────────────────────────────
    subject_id:   Mapped[str]       = mapped_column(Text, nullable=False, unique=True)
    common_name:  Mapped[str]       = mapped_column(Text, nullable=False)
    aliases:      Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    # ── Physical indexed scalars (v1.0) ─────────────────────────────────────
    mineral_formula:    Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_color:      Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    frequency_hz_low:   Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True, index=True)
    frequency_hz_high:  Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True, index=True)
    alchemical_stage:   Mapped[str | None] = mapped_column(Text, nullable=True, index=True)  # v1.0 compat
    primary_gaia_layer: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    primary_element:    Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    # ── Physical indexed scalars (v2.0) ─────────────────────────────────────
    crystal_system:           Mapped[str | None]   = mapped_column(Text, nullable=True, index=True)
    mohs_hardness_low:        Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    mohs_hardness_high:       Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    piezoelectric:            Mapped[bool | None]  = mapped_column(Boolean, nullable=True, index=True)
    pyroelectric:             Mapped[bool | None]  = mapped_column(Boolean, nullable=True)
    luminance_profile:        Mapped[str | None]   = mapped_column(Text, nullable=True)

    # ── Alchemical indexed scalars (v2.0) ──────────────────────────────────
    alchemical_stage_primary: Mapped[str | None]   = mapped_column(Text, nullable=True, index=True)

    # ── Chakra indexed scalar (v2.0) ───────────────────────────────────────
    primary_chakra:           Mapped[str | None]   = mapped_column(Text, nullable=True, index=True)

    # ── Consequential indexed scalars (v2.0) ──────────────────────────────
    coherence_impact_scalar:  Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True, index=True)
    grey_state_risk_level:    Mapped[str | None]   = mapped_column(Text, nullable=True, index=True)

    # ── Versioning & review scalars (v2.0) ──────────────────────────────
    record_version:    Mapped[str | None]  = mapped_column(Text, nullable=True, default="1.0.0", index=True)
    review_status:     Mapped[str | None]  = mapped_column(Text, nullable=True, default="draft", index=True)
    reviewed_by:       Mapped[str | None]  = mapped_column(Text, nullable=True)
    next_review_date:  Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    # ── v1.0 JSONB payload (full correspondence object) ────────────────────
    correspondences: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    schema_version:  Mapped[str]            = mapped_column(Text, nullable=False, default="2.0.0", index=True)
    provenance:      Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False,
        default=lambda: {"source": "GAIA-OS", "confidence": "high", "last_updated": None},
    )

    # ── v2.0 JSONB axis columns ──────────────────────────────────────────
    physical_properties:      Mapped[dict | None]  = mapped_column(JSONB, nullable=True, default=dict)
    resonant_frequencies:     Mapped[list | None]  = mapped_column(JSONB, nullable=True, default=list)
    chakra_system:            Mapped[list | None]  = mapped_column(JSONB, nullable=True, default=list)
    alchemical:               Mapped[dict | None]  = mapped_column(JSONB, nullable=True, default=dict)
    healing:                  Mapped[dict | None]  = mapped_column(JSONB, nullable=True, default=dict)
    consequential_properties: Mapped[dict | None]  = mapped_column(JSONB, nullable=True, default=dict)
    provenance_v2:            Mapped[dict | None]  = mapped_column(JSONB, nullable=True, default=dict)
    sovereignty_flags:        Mapped[dict | None]  = mapped_column(JSONB, nullable=True, default=dict)
    change_log:               Mapped[list | None]  = mapped_column(JSONB, nullable=True, default=list)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationship ────────────────────────────────────────────────────────
    provenance_log: Mapped[list["CrystalCorrespondenceProvenanceLog"]] = relationship(
        back_populates="crystal",
        cascade="all, delete-orphan",
        order_by="CrystalCorrespondenceProvenanceLog.changed_at",
    )

    # ───────────────────────────────────────────────────────────────────
    # v1.0 HELPER METHODS (correspondence axis accessors from JSONB)
    # ───────────────────────────────────────────────────────────────────

    def gaia_layers(self) -> list[dict]:
        """Return GAIA layer entries from correspondences JSONB."""
        return (self.correspondences or {}).get("gaia_layers", [])

    def primary_archetype(self) -> str | None:
        archetypes = (self.correspondences or {}).get("archetypes", [])
        return archetypes[0].get("name") if archetypes else None

    def emotion_set(self) -> list[str]:
        return [
            e.get("primary", "") for e in (self.correspondences or {}).get("emotions", [])
        ]

    def safety_flags(self) -> list[str]:
        sp = (self.correspondences or {}).get("safety_profile", {})
        return sp.get("trauma_flags", [])

    # ───────────────────────────────────────────────────────────────────
    # v2.0 HELPER METHODS
    # ───────────────────────────────────────────────────────────────────

    def chakra_set(self) -> list[str]:
        """Return list of chakra names from the chakra_system JSONB column."""
        entries = self.chakra_system or []
        return [c.get("chakra", "") for c in entries]

    def alchemical_stage(self) -> str | None:
        """Return primary alchemical stage — from indexed scalar if populated,
        else fall back to the alchemical JSONB column."""
        if self.alchemical_stage_primary:
            return self.alchemical_stage_primary
        return (self.alchemical or {}).get("stage_primary")

    def coherence_impact(self) -> dict:
        """Return the full coherence_impact object from consequential_properties."""
        cp = self.consequential_properties or {}
        return cp.get("coherence_impact", {})

    def coherence_scalar(self) -> float | None:
        """Return the scalar coherence impact value (-1.0 to +1.0)."""
        if self.coherence_impact_scalar is not None:
            return float(self.coherence_impact_scalar)
        return self.coherence_impact().get("scalar")

    def grey_state_risks(self) -> dict:
        """Return grey_state_risk object from consequential_properties."""
        cp = self.consequential_properties or {}
        return cp.get("grey_state_risk", {})

    def healing_entries(self, domain: str = "physical") -> list[dict]:
        """Return healing entries for a given domain.

        Parameters
        ----------
        domain : str
            One of 'physical', 'emotional_mental', 'spiritual_energetic'.
        """
        h = self.healing or {}
        return h.get(domain, [])

    def interaction_partners(self) -> list[dict]:
        """Return interaction_matrix entries from consequential_properties."""
        cp = self.consequential_properties or {}
        return cp.get("interaction_matrix", [])

    def synergy_partners(self) -> list[str]:
        """Return subject_ids of crystals this one has a synergy relationship with."""
        return [
            entry["partner"]
            for entry in self.interaction_partners()
            if entry.get("type") == "synergy"
        ]

    def antagonism_partners(self) -> list[str]:
        """Return subject_ids of crystals this one has an antagonism with."""
        return [
            entry["partner"]
            for entry in self.interaction_partners()
            if entry.get("type") == "antagonism"
        ]

    def measurable_outcomes(self) -> list[dict]:
        """Return measurable_outcomes list from consequential_properties."""
        cp = self.consequential_properties or {}
        return cp.get("measurable_outcomes", [])

    def long_term_consequences(self) -> list[dict]:
        """Return long_term_consequences list from consequential_properties."""
        cp = self.consequential_properties or {}
        return cp.get("long_term_consequences", [])

    def resonant_hz_values(self) -> list[float]:
        """Return flat list of Hz values from the resonant_frequencies JSONB column."""
        return [entry["hz"] for entry in (self.resonant_frequencies or []) if "hz" in entry]

    def color_spectrum(self) -> list[dict]:
        """Return color_spectrum entries from physical_properties JSONB column."""
        pp = self.physical_properties or {}
        return pp.get("color_spectrum", [])

    def primary_color_hex(self) -> str | None:
        """Return hex code of the primary colour entry, if present."""
        for entry in self.color_spectrum():
            if entry.get("is_primary"):
                return entry.get("hex")
        return None

    def is_user_overridable(self) -> bool:
        """Return True if Architects may submit personal override correspondences."""
        sf = self.sovereignty_flags or {}
        return bool(sf.get("user_overridable", False))

    def community_contributions_enabled(self) -> bool:
        """Return True if Gaian community observations can be appended."""
        sf = self.sovereignty_flags or {}
        return bool(sf.get("community_contributions_enabled", False))

    def transmutation_corridor(self) -> str | None:
        """Return the primary transmutation corridor from the alchemical JSONB."""
        return (self.alchemical or {}).get("transmutation_corridor")

    def __repr__(self) -> str:
        return (
            f"<CrystalCorrespondence id={self.id} "
            f"subject_id={self.subject_id!r} "
            f"alchemical={self.alchemical_stage()!r} "
            f"coherence={self.coherence_scalar()!r}>"
        )


class CrystalCorrespondenceProvenanceLog(Base):
    """Append-only change log — unchanged from v1.0."""

    __tablename__ = "crystal_correspondence_provenance_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crystal_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crystal_correspondence.id", ondelete="CASCADE"),
        nullable=False,
    )
    version:             Mapped[str]            = mapped_column(Text, nullable=False)
    changed_by:          Mapped[str | None]     = mapped_column(Text, nullable=True)
    change_note:         Mapped[str | None]     = mapped_column(Text, nullable=True)
    snapshot:            Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    provenance_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    crystal: Mapped["CrystalCorrespondence"] = relationship(back_populates="provenance_log")

    def __repr__(self) -> str:
        return (
            f"<ProvenanceLog crystal_id={self.crystal_id} "
            f"version={self.version!r} at={self.changed_at}>"
        )
