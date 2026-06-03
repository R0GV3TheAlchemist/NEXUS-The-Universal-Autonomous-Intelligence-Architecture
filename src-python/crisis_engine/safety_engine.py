"""SafetyEngine — thin orchestration facade for GAIA's crisis safety pipeline.

This module is the primary integration point for tests in test_safety.py.
It wraps CrisisEngine and exposes a simpler interface that returns structured
session profiles (dicts) and surfaces handoff signals cleanly.

Canon C01: Safety first — no action must compromise the user's safety.
Canon C30: No silent failures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from .engine import CrisisEngine, EngineConfig
from .types import EscalationTier, HandoffRecord, RiskLevel


class SafetyLevel(str, Enum):
    """Explicit safety level — mirrors EscalationTier for test clarity."""
    SAFE     = "SAFE"
    MONITOR  = "MONITOR"
    WARNING  = "WARNING"   # ← Added: sub-critical advisory level
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"
    HANDOFF  = "HANDOFF"


_TIER_TO_LEVEL: Dict[EscalationTier, SafetyLevel] = {
    EscalationTier.NONE    : SafetyLevel.SAFE,
    EscalationTier.MONITOR : SafetyLevel.MONITOR,
    EscalationTier.SUPPORT : SafetyLevel.ELEVATED,
    EscalationTier.CRISIS  : SafetyLevel.CRITICAL,
    EscalationTier.HANDOFF : SafetyLevel.HANDOFF,
}


@dataclass
class SessionProfile:
    """Structured result of a safety evaluation for one session turn."""
    session_id        : str
    turn_index        : int
    safety_level      : SafetyLevel
    risk_level        : RiskLevel
    requires_handoff  : bool
    handoff_signal    : Optional[str]      # Non-None when requires_handoff=True
    intervention_msg  : str
    raw_snapshot      : Dict[str, Any] = field(default_factory=dict)


class SafetyEngine:
    """Facade around CrisisEngine for the safety test suite.

    Parameters
    ----------
    principal_id : str
        Identifies the GAIA user / Gaian instance.
    db_path : Path | None
        Passed through to CrisisEngine; defaults to :memory:.
    """

    def __init__(
        self,
        principal_id: str,
        db_path: Optional[Path] = None,
    ) -> None:
        config           = EngineConfig(principal_id=principal_id, db_path=db_path)
        self._engine     = CrisisEngine(config)
        self._principal  = principal_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_turn(
        self,
        user_text  : str,
        session_id : str,
        turn_index : int = 0,
    ) -> SessionProfile:
        """Evaluate a single user turn and return a SessionProfile dict.

        Always returns a dict (never a plain string) so callers can index
        into it with string keys without hitting TypeError.
        """
        snapshot = self._engine.evaluate(
            user_text  = user_text,
            session_id = session_id,
            turn_index = turn_index,
        )

        safety_level     = _TIER_TO_LEVEL.get(snapshot.escalation_tier, SafetyLevel.SAFE)
        requires_handoff = snapshot.escalation_tier == EscalationTier.HANDOFF

        # Build handoff signal string only when handoff is required
        handoff_signal: Optional[str] = None
        if requires_handoff:
            record = self._engine.build_handoff()
            handoff_signal = (
                record.resource_detail
                if record is not None
                else f"handoff-required:{session_id}"
            )

        intervention_msg = self._engine.get_intervention_message()

        return SessionProfile(
            session_id       = session_id,
            turn_index       = turn_index,
            safety_level     = safety_level,
            risk_level       = snapshot.current_risk,
            requires_handoff = requires_handoff,
            handoff_signal   = handoff_signal,
            intervention_msg = intervention_msg,
            raw_snapshot     = snapshot.to_dict() if hasattr(snapshot, "to_dict") else {},
        )

    def close_session(
        self,
        session_id  : str,
        peak_risk   : RiskLevel = RiskLevel.NONE,
        signal_count: int       = 0,
        has_explicit: bool      = False,
        has_masked  : bool      = False,
    ) -> SessionProfile:
        """Close out a session and return the final SessionProfile.

        Returns a SessionProfile (always a dict-like object, never a string)
        so that test assertions like `profile["session_id"]` work correctly.
        """
        self._engine.close_session(
            session_id   = session_id,
            peak_risk    = peak_risk,
            signal_count = signal_count,
            has_explicit = has_explicit,
            has_masked   = has_masked,
        )
        # After close, build a lightweight profile from the last snapshot
        last = self._engine._last_snapshot
        if last is None:
            return SessionProfile(
                session_id       = session_id,
                turn_index       = -1,
                safety_level     = SafetyLevel.SAFE,
                risk_level       = peak_risk,
                requires_handoff = False,
                handoff_signal   = None,
                intervention_msg = "",
            )

        safety_level     = _TIER_TO_LEVEL.get(last.escalation_tier, SafetyLevel.SAFE)
        requires_handoff = last.escalation_tier == EscalationTier.HANDOFF
        handoff_signal: Optional[str] = None
        if requires_handoff:
            record = self._engine.build_handoff()
            handoff_signal = (
                record.resource_detail
                if record is not None
                else f"handoff-required:{session_id}"
            )

        return SessionProfile(
            session_id       = session_id,
            turn_index       = -1,
            safety_level     = safety_level,
            risk_level       = peak_risk,
            requires_handoff = requires_handoff,
            handoff_signal   = handoff_signal,
            intervention_msg = self._engine.get_intervention_message(),
            raw_snapshot     = last.to_dict() if hasattr(last, "to_dict") else {},
        )
