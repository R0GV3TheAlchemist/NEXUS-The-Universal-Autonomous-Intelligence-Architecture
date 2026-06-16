"""GoldenCompassService — REST API surface for the moral engine.

This is the module that the API layer (FastAPI/Flask router) wires to.
It provides the four REST endpoints specified in #438:

  GET  /moral/compass        — current session moral reading
  POST /moral/evaluate       — evaluate a proposed action
  GET  /moral/love-mode      — current active love mode
  GET  /moral/entropy-state  — chaos/order balance

All calls are stateless except for the session context cache.
"""

from __future__ import annotations

from typing import Optional

from .types import ActionContext, ProposedAction
from .chaos_order import ChaosOrderEngine, EntropyAssessment
from .love import LoveAssessment, LoveDoctrineEngine
from .compass import GoldenCompassEngine, MoralCompassReading


class GoldenCompassService:
    """Service layer for the GoldenCompassEngine.

    Maintains a session context cache so that repeated evaluations
    within a session accumulate context (LCI, harm history, etc.).

    Usage:
        service = GoldenCompassService()
        reading = service.evaluate(
            description="Build the GAIA OS session bootstrap",
            session_id="abc123",
        )
        print(reading.recommended_action)
    """

    def __init__(self) -> None:
        self._compass = GoldenCompassEngine()
        self._love_engine = LoveDoctrineEngine()
        self._chaos_engine = ChaosOrderEngine()
        self._session_contexts: dict[str, ActionContext] = {}
        self._last_readings: dict[str, MoralCompassReading] = {}

    # ------------------------------------------------------------------
    # POST /moral/evaluate
    # ------------------------------------------------------------------

    def evaluate(
        self,
        description: str,
        session_id: Optional[str] = None,
        content: Optional[str] = None,
        action_type: str = "RESPONSE",
        target: Optional[str] = None,
    ) -> MoralCompassReading:
        """Evaluate a proposed action. Returns a full MoralCompassReading."""
        action = ProposedAction(
            description=description,
            content=content,
            action_type=action_type,
            target=target,
        )
        ctx = self._get_context(session_id)
        reading = self._compass.evaluate_action(action, ctx)

        if session_id:
            self._last_readings[session_id] = reading
            self._update_context(session_id, reading)

        return reading

    # ------------------------------------------------------------------
    # GET /moral/compass
    # ------------------------------------------------------------------

    def get_current_reading(self, session_id: str) -> Optional[MoralCompassReading]:
        """Return the most recent compass reading for this session."""
        return self._last_readings.get(session_id)

    # ------------------------------------------------------------------
    # GET /moral/love-mode
    # ------------------------------------------------------------------

    def get_love_mode(
        self,
        description: str,
        session_id: Optional[str] = None,
    ) -> LoveAssessment:
        """Identify the active love mode for a given description."""
        action = ProposedAction(description=description)
        ctx = self._get_context(session_id)
        return self._love_engine.assess_love(action, ctx)

    # ------------------------------------------------------------------
    # GET /moral/entropy-state
    # ------------------------------------------------------------------

    def get_entropy_state(
        self,
        description: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> EntropyAssessment:
        """Get the current chaos/order entropy state."""
        action = ProposedAction(description=description or "") if description else None
        ctx = self._get_context(session_id)
        return self._chaos_engine.get_entropy_state(action, ctx)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_context(self, session_id: Optional[str]) -> Optional[ActionContext]:
        if not session_id:
            return None
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = ActionContext(session_id=session_id)
        return self._session_contexts[session_id]

    def _update_context(
        self, session_id: str, reading: MoralCompassReading
    ) -> None:
        """Propagate reading results back into the session context."""
        ctx = self._session_contexts.get(session_id)
        if not ctx or not reading.love:
            return
        ctx.love_coherence_index = reading.love.love_coherence_index
        if reading.harm and reading.harm.risk_level.value in ("HIGH", "CRITICAL"):
            ctx.prior_harm_events += 1
        ctx.interaction_count += 1
