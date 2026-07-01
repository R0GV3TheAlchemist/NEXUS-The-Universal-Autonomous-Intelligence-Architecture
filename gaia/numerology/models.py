"""Pydantic request/response schemas for the Numerology API.

Kept in gaia/numerology/models.py so the route stub's original import
  `from gaia.numerology.models import NumerologyInput, NumerologyChart`
resolves without change.

See canon/C160_Numerology_Vibrational_Identity_Engine.md § 8 for the
canonical API surface these schemas implement.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared sub-schemas
# ---------------------------------------------------------------------------

class NumberDetail(BaseModel):
    """A single computed number position."""

    number_type: str = Field(
        description="Position slug: life_path | expression | soul_urge | personality | birthday | personal_year | challenge_*"
    )
    raw_value: int = Field(description="Sum before any reduction")
    reduced_value: int = Field(description="Final value after Pythagorean reduction (0-9, 11, 22, 33). 0 = absent energy.")
    is_master_number: bool = Field(default=False)
    reduction_path: List[int] = Field(
        description="Ordered steps from raw_value to reduced_value, inclusive"
    )
    archetype: Optional[str] = Field(default=None, description="Archetype label, e.g. 'The Seeker'")
    theme: Optional[str] = Field(default=None, description="Core theme of this archetype")


class PersonalYearEntry(BaseModel):
    """A single year in the personal year progression cycle."""

    year: int = Field(description="Calendar year")
    reduced_value: int = Field(description="Personal year number for this calendar year")
    is_master_number: bool = Field(default=False)
    archetype: Optional[str] = Field(default=None)
    theme: Optional[str] = Field(default=None)


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class NumerologyInput(BaseModel):
    """Input required to compute or retrieve a numerology chart."""

    full_name: str = Field(
        min_length=1,
        max_length=512,
        description="Full birth name as registered (including middle names). Used for Expression, Soul Urge, and Personality numbers.",
        examples=["Nikola Tesla", "Ada Lovelace"],
    )
    birth_date: date = Field(
        description="Date of birth in ISO 8601 format (YYYY-MM-DD).",
        examples=["1856-07-10"],
    )
    user_id: Optional[UUID] = Field(
        default=None,
        description="Gaian user UUID. When provided, the chart is persisted and linked to this identity.",
    )
    system: str = Field(
        default="pythagorean",
        description="Numerology system. Currently only 'pythagorean' is supported.",
    )
    force_recompute: bool = Field(
        default=False,
        description="When True, always generate a fresh chart even if one already exists for this name/date.",
    )
    cycle_years: int = Field(
        default=3,
        ge=0,
        le=9,
        description="How many future years to include in personal_year_cycle (0 to omit, max 9).",
    )

    @field_validator("system")
    @classmethod
    def system_must_be_supported(cls, v: str) -> str:
        supported = {"pythagorean"}
        if v not in supported:
            raise ValueError(f"Unsupported system '{v}'. Choose from: {sorted(supported)}")
        return v

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("birth_date must be in the past.")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class NumerologyChart(BaseModel):
    """Full computed numerology chart — the primary API response."""

    chart_id: Optional[UUID] = Field(
        default=None,
        description="Database UUID of the persisted chart. None for ephemeral (no user_id) requests.",
    )
    profile_id: Optional[UUID] = Field(
        default=None,
        description="Database UUID of the NumerologyProfile row.",
    )
    full_name: str
    birth_date: date
    system: str

    # Five core numbers
    life_path: NumberDetail
    expression: NumberDetail
    soul_urge: NumberDetail
    personality: NumberDetail
    birthday: NumberDetail

    # Timing
    personal_year: NumberDetail
    computed_for_year: int = Field(description="Calendar year against which personal_year was computed")

    # Personal year progression — current year + next N years
    personal_year_cycle: List[PersonalYearEntry] = Field(
        default_factory=list,
        description="Personal year values for the current year and the next cycle_years years. "
                    "Enables GAIA to surface proactive year-ahead guidance without additional API calls.",
    )

    # Optional challenge numbers
    challenges: List[NumberDetail] = Field(default_factory=list)

    # Convenience summary
    master_numbers_present: List[int] = Field(
        default_factory=list,
        description="List of master numbers (11, 22, 33) appearing anywhere in this chart",
    )

    model_config = {"from_attributes": True}


class NumerologyChartListResponse(BaseModel):
    """Paginated list of charts for a user."""

    charts: List[NumerologyChart]
    total: int
    user_id: UUID
