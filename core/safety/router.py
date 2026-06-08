"""SafetyRouter — HTTP routing layer for the SafetyEngine.

Exposes the SafetyEngine as a FastAPI router so the main GAIA server
can mount it at /safety. Manages per-session engine instances.
"""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .safety_engine import SafetyEngine

router = APIRouter(prefix="/safety", tags=["safety"])

# In-memory session registry — keyed by session_id
# In production this would be backed by Redis or similar
_engines: Dict[str, SafetyEngine] = {}


def _get_engine(session_id: str) -> SafetyEngine:
    """Retrieve or create a SafetyEngine for the given session."""
    if session_id not in _engines:
        _engines[session_id] = SafetyEngine()
    return _engines[session_id]


# ------------------------------------------------------------------ #
#  Request / Response schemas                                         #
# ------------------------------------------------------------------ #

class TurnEvaluationRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    user_text: str = Field(..., description="Raw user message text")
    mirroring_score: float = Field(..., ge=0.0, le=1.0)
    vulnerability_score: float = Field(..., ge=0.0, le=1.0)
    escalation_delta: float = Field(0.0, description="Change in vulnerability score from previous turn")


class TurnEvaluationResponse(BaseModel):
    action: str
    intervention_text: str | None
    circuit_breaker_state: str
    intervention_mode: str | None = None
    has_crisis_signal: bool
    has_escalation_signal: bool


# ------------------------------------------------------------------ #
#  Endpoints                                                          #
# ------------------------------------------------------------------ #

@router.post("/evaluate", response_model=TurnEvaluationResponse)
async def evaluate_turn(req: TurnEvaluationRequest) -> TurnEvaluationResponse:
    """Evaluate a conversation turn for safety signals."""
    engine = _get_engine(req.session_id)
    verdict = engine.evaluate_turn(
        user_text=req.user_text,
        mirroring_score=req.mirroring_score,
        vulnerability_score=req.vulnerability_score,
        escalation_delta=req.escalation_delta,
        session_id=req.session_id,
    )
    return TurnEvaluationResponse(
        action=verdict.action,
        intervention_text=verdict.intervention_text,
        circuit_breaker_state=verdict.circuit_breaker_state.value,
        intervention_mode=verdict.intervention_mode,
        has_crisis_signal=verdict.crisis_signal is not None,
        has_escalation_signal=verdict.escalation_signal is not None,
    )


@router.post("/reset/{session_id}")
async def reset_session(session_id: str) -> dict:
    """Reset safety state for the given session."""
    if session_id in _engines:
        _engines[session_id].reset_session()
    return {"ok": True, "session_id": session_id}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Remove a session's SafetyEngine instance from memory."""
    _engines.pop(session_id, None)
    return {"ok": True, "session_id": session_id}
