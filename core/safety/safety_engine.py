"""SafetyEngine — top-level safety orchestrator for GAIA-OS.

Wires together:
  - ReflectiveEscalationDetector  (feedback-loop detection)
  - EscalationCircuitBreaker      (graduated intervention)
  - CrisisDetector                (acute crisis signal detection)
  - CrisisSynthesizer             (crisis response generation)

The engine is stateful per-session and is instantiated by the
SynergyEngine (or equivalent session manager) at session start.
"""

from __future__ import annotations

from typing import Optional

from .circuit_breaker import EscalationCircuitBreaker, InterventionMode
from .crisis_detector import CrisisDetector
from .crisis_synthesizer import CrisisSynthesizer
from .escalation_detector import ReflectiveEscalationDetector
from .types import (
    CircuitBreakerState,
    CrisisSignal,
    EscalationSignal,
    SafetyVerdict,
    TurnRiskFrame,
)


class SafetyEngine:
    """Stateful per-session safety orchestrator."""

    def __init__(
        self,
        cooling_turns: int = 4,
        mirroring_threshold: float = 0.72,
        vulnerability_threshold: float = 0.65,
        escalation_window: int = 3,
    ) -> None:
        self.escalation_detector = ReflectiveEscalationDetector(
            mirroring_threshold=mirroring_threshold,
            vulnerability_threshold=vulnerability_threshold,
            window=escalation_window,
        )
        self.circuit_breaker = EscalationCircuitBreaker(cooling_turns=cooling_turns)
        self.crisis_detector = CrisisDetector()
        self.crisis_synthesizer = CrisisSynthesizer()
        self._turn_index: int = 0

    # ------------------------------------------------------------------ #
    #  Primary entry point                                                #
    # ------------------------------------------------------------------ #

    def evaluate_turn(
        self,
        user_text: str,
        mirroring_score: float,
        vulnerability_score: float,
        escalation_delta: float = 0.0,
        session_id: str = "unknown",
    ) -> SafetyVerdict:
        """
        Evaluate a single conversation turn for safety signals.

        Returns a SafetyVerdict that the SynergyEngine uses to decide
        whether to pass the normal response or inject an intervention.
        """
        self._turn_index += 1

        frame = TurnRiskFrame(
            turn_index=self._turn_index,
            session_id=session_id,
            mirroring_score=mirroring_score,
            vulnerability_score=vulnerability_score,
            escalation_delta=escalation_delta,
        )

        # 1. Crisis detection (highest priority — overrides everything)
        crisis_signal: Optional[CrisisSignal] = self.crisis_detector.evaluate(user_text)
        if crisis_signal and crisis_signal.requires_immediate_response:
            response_text = self.crisis_synthesizer.synthesize(crisis_signal)
            return SafetyVerdict(
                action="crisis_response",
                intervention_text=response_text,
                crisis_signal=crisis_signal,
                escalation_signal=None,
                circuit_breaker_state=CircuitBreakerState.TRIPPED,
            )

        # 2. Cooling tick — decrement counter if we're in a cooldown window
        cb_state = self.circuit_breaker.tick()
        if cb_state == CircuitBreakerState.COOLING:
            return SafetyVerdict(
                action="cooling",
                intervention_text=None,
                crisis_signal=crisis_signal,
                escalation_signal=None,
                circuit_breaker_state=cb_state,
            )

        # 3. Reflective escalation detection
        escalation_signal: Optional[EscalationSignal] = self.escalation_detector.push_turn(frame)
        if escalation_signal:
            intervention = self.circuit_breaker.intervene(escalation_signal)
            return SafetyVerdict(
                action="escalation_intervention",
                intervention_text=intervention["text"],
                crisis_signal=crisis_signal,
                escalation_signal=escalation_signal,
                circuit_breaker_state=CircuitBreakerState.TRIPPED,
                intervention_mode=intervention["intervention_mode"],
            )

        # 4. Pass — no safety triggers fired
        return SafetyVerdict(
            action="pass",
            intervention_text=None,
            crisis_signal=crisis_signal,
            escalation_signal=None,
            circuit_breaker_state=self.escalation_detector.state,
        )

    def reset_session(self) -> None:
        """Reset all stateful detectors for a new session."""
        self.escalation_detector.reset_session()
        self._turn_index = 0
