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

from datetime import datetime
from typing import List, Optional

from .circuit_breaker import EscalationCircuitBreaker
from .crisis_detector import CrisisDetector
from .crisis_synthesizer import CrisisSynthesizer, CrossSessionCrisisSignal
from .escalation_detector import ReflectiveEscalationDetector
from .types import (
    CircuitBreakerState,
    CrisisLevel,
    CrisisSignal,
    EscalationSignal,
    SafetyVerdict,
    SessionRiskProfile,
    TurnRiskFrame,
)

# Explicit severity ordering for CrisisLevel so that max() works correctly.
# CrisisLevel inherits from str; alphabetical ordering is wrong
# ("none" > "masked" > "gradual" > "explicit" > "acute" alphabetically).
_CRISIS_SEVERITY: dict[CrisisLevel, int] = {
    CrisisLevel.NONE:     0,
    CrisisLevel.GRADUAL:  1,
    CrisisLevel.MASKED:   2,
    CrisisLevel.ACUTE:    3,
    CrisisLevel.EXPLICIT: 4,
}


class SafetyEngine:
    """Stateful per-session safety orchestrator."""

    def __init__(
        self,
        user_id: str = "unknown",
        session_id: str = "unknown",
        cooling_turns: int = 4,
        mirroring_threshold: float = 0.72,
        vulnerability_threshold: float = 0.65,
        escalation_window: int = 3,
    ) -> None:
        self._user_id = user_id
        self._session_id = session_id
        self._started_at = datetime.utcnow()

        self.escalation_detector = ReflectiveEscalationDetector(
            mirroring_threshold=mirroring_threshold,
            vulnerability_threshold=vulnerability_threshold,
            window=escalation_window,
        )
        self.circuit_breaker = EscalationCircuitBreaker(cooling_turns=cooling_turns)
        self.crisis_detector = CrisisDetector()
        self.crisis_synthesizer = CrisisSynthesizer()
        self._turn_index: int = 0

        # Accumulated per-session state for close_session()
        self._frames: List[TurnRiskFrame] = []
        self._escalation_events: int = 0
        self._cb_trips: int = 0

    # ------------------------------------------------------------------ #
    #  New process_turn API (test contract)                               #
    # ------------------------------------------------------------------ #

    def process_turn(
        self,
        frame: TurnRiskFrame,
        text: str,
        past_profiles: Optional[List[SessionRiskProfile]] = None,
    ) -> dict:
        """Evaluate one turn; return a result dict.

        Keys:
            intervention          — str or None
            escalation_signal     — EscalationSignal or None
            circuit_breaker_state — CircuitBreakerState.value str
            crisis_signal         — CrossSessionCrisisSignal or None
                                    (only populated when past_profiles is given
                                    and aggregate risk exceeds threshold)
        """
        self._frames.append(frame)
        self._turn_index += 1

        # Cross-session synthesis (only when caller supplies history)
        # Returns CrossSessionCrisisSignal | None
        cross_signal: Optional[CrossSessionCrisisSignal] = None
        if past_profiles:
            cross_signal = self.crisis_synthesizer.synthesize(
                self._user_id, self._session_id, past_profiles
            )

        # Per-turn acute crisis detection (highest priority — overrides everything)
        # Returns CrisisSignal | None  — kept as local var, not surfaced in return dict
        # to avoid confusion with the cross-session CrossSessionCrisisSignal.
        per_turn_crisis: Optional[CrisisSignal] = self.crisis_detector.evaluate(text)
        if per_turn_crisis and per_turn_crisis.requires_immediate_response:
            response_text = self.crisis_synthesizer.synthesize(per_turn_crisis)
            return {
                "intervention": response_text,
                "escalation_signal": None,
                "circuit_breaker_state": CircuitBreakerState.TRIPPED.value,
                "crisis_signal": cross_signal,  # CrossSessionCrisisSignal | None
            }

        # Cooling tick — returns COOLING while counter > 0, CLOSED when expired
        cb_state = self.circuit_breaker.tick()
        if cb_state == CircuitBreakerState.COOLING:
            return {
                "intervention": None,
                "escalation_signal": None,
                "circuit_breaker_state": cb_state.value,
                "crisis_signal": cross_signal,
            }

        # Reflective escalation detection
        escalation_signal: Optional[EscalationSignal] = self.escalation_detector.push_turn(frame)
        if escalation_signal:
            intervention = self.circuit_breaker.intervene(escalation_signal)
            self._escalation_events += 1
            self._cb_trips += 1
            return {
                "intervention": intervention["text"],
                "escalation_signal": escalation_signal,
                "circuit_breaker_state": CircuitBreakerState.COOLING.value,
                "crisis_signal": cross_signal,
            }

        # Pass — no safety triggers fired
        return {
            "intervention": None,
            "escalation_signal": None,
            "circuit_breaker_state": self.escalation_detector.state.value,
            "crisis_signal": cross_signal,
        }

    def close_session(self) -> SessionRiskProfile:
        """Finalise the session and return an aggregate SessionRiskProfile."""
        ended_at = datetime.utcnow()

        if self._frames:
            mean_vuln = sum(f.vulnerability_score for f in self._frames) / len(self._frames)
            # Use an explicit severity key — CrisisLevel inherits from str and
            # its alphabetical ordering is the inverse of severity intent.
            peak_crisis = max(
                (f.crisis_level for f in self._frames),
                key=lambda lvl: _CRISIS_SEVERITY[lvl],
                default=CrisisLevel.NONE,
            )
        else:
            mean_vuln = 0.0
            peak_crisis = CrisisLevel.NONE

        # Cumulative risk: blend mean_vuln with trip density
        trip_density = min(1.0, self._escalation_events / max(len(self._frames), 1))
        cumulative = min(1.0, mean_vuln * 0.6 + trip_density * 0.4)

        profile = SessionRiskProfile(
            session_id=self._session_id,
            user_id=self._user_id,
            started_at=self._started_at,
            ended_at=ended_at,
            peak_crisis_level=peak_crisis,
            mean_vulnerability_score=mean_vuln,
            escalation_events=self._escalation_events,
            circuit_breaker_trips=self._cb_trips,
            cumulative_risk_score=cumulative,
        )
        # Reset session state
        self._frames.clear()
        self._escalation_events = 0
        self._cb_trips = 0
        self._turn_index = 0
        self._started_at = datetime.utcnow()
        return profile

    # ------------------------------------------------------------------ #
    #  Legacy evaluate_turn API (keep for existing callers)               #
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
        self._frames.clear()
        self._escalation_events = 0
        self._cb_trips = 0
        self._turn_index = 0
        self._started_at = datetime.utcnow()
