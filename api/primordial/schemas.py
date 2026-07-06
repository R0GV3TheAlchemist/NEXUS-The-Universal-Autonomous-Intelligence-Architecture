"""
api/primordial/schemas.py
=========================
Pydantic request and response schemas for the primordial simulation API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Simulate
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    name:      str   = Field(default="unnamed-entity")
    love:      float = Field(default=1.0, ge=0.0, le=1.0)
    life:      float = Field(default=1.0, ge=0.0, le=1.0)
    integrity: float = Field(default=1.0, ge=0.0, le=1.0)
    hope:      float = Field(default=1.0, ge=0.0, le=1.0)
    truth:     float = Field(default=1.0, ge=0.0, le=1.0)
    burden:    float = Field(default=0.0, ge=0.0)
    save_to_canon: bool = Field(default=True)


class SimulateResponse(BaseModel):
    entity_name:         str
    survived:            bool
    emergent_order:      float
    retained_constants:  dict[str, float]
    broken_faculties:    list[str]
    surviving_faculties: list[str]
    stage_results:       list[dict[str, Any]]
    run_at:              str


# ---------------------------------------------------------------------------
# Recover
# ---------------------------------------------------------------------------

class InterventionInput(BaseModel):
    intervention_type: str = Field(
        description="One of: rest, witness, love, truth, all"
    )
    intensity: float = Field(default=0.7, ge=0.0, le=1.0)


class RecoverRequest(BaseModel):
    name:      str   = Field(default="recovering-entity")
    love:      float = Field(default=0.15, ge=0.0, le=1.0)
    life:      float = Field(default=0.12, ge=0.0, le=1.0)
    integrity: float = Field(default=0.20, ge=0.0, le=1.0)
    hope:      float = Field(default=0.10, ge=0.0, le=1.0)
    truth:     float = Field(default=0.20, ge=0.0, le=1.0)
    burden:    float = Field(default=2.0,  ge=0.0)
    interventions:  list[InterventionInput] = Field(default_factory=list)
    save_to_canon:  bool = Field(default=True)


class RecoverResponse(BaseModel):
    entity_name:       str
    first_run:         dict[str, Any]
    interventions:     list[str]
    restored_entity:   dict[str, Any]
    second_run:        dict[str, Any]
    recovered:         bool
    order_delta:       float
    narrative:         str
    run_at:            str


# ---------------------------------------------------------------------------
# Archetypes
# ---------------------------------------------------------------------------

class ArchetypeResponse(BaseModel):
    archetype:           str
    description:         str
    survived:            bool
    emergent_order:      float
    broken_faculties:    list[str]
    surviving_faculties: list[str]
    insights:            list[str]
    narrative:           str
    recovery_narrative:  str | None = None


# ---------------------------------------------------------------------------
# Canon
# ---------------------------------------------------------------------------

class CanonSummaryResponse(BaseModel):
    total:               int
    survived:            int
    collapsed:           int
    survival_rate:       float
    avg_emergent_order:  float
    top_insights:        list[str]
