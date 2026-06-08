"""CrisisSynthesizer — crisis response generation for GAIA-OS.

Generates empathetic, resource-aware responses when CrisisDetector
fires a high-confidence signal. Responses are carefully crafted to:
  - Validate the user's experience
  - Provide concrete resources without being dismissive
  - Maintain the warm, relational tone of GAIA

Cross-session synthesis: analyses a window of past SessionRiskProfiles
to detect longitudinal patterns that single-session detection misses.

Canon refs: CEth01, C34
"""
from __future__ import annotations

from typing import List, Optional

from .crisis_detector import CumulativeCrisisDetector
from .escalation_detector import ReflectiveEscalationDetector
from .types import (
    CrisisLevel,
    CrisisSignal,
    CrisisType,
    CrossSessionCrisisSignal,
    SessionRiskProfile,
    TurnRiskFrame,
)

# ------------------------------------------------------------------ #
#  Module-level constants                                             #
# ------------------------------------------------------------------ #

_SUICIDE_RESPONSE = (
    "I want to make sure you're safe right now. "
    "If you're having thoughts of suicide or self-harm, please reach out "
    "to a crisis line — in the US you can text HOME to 741741 or call 988. "
    "I care about you, and I'm here."
)

_GENERAL_CRISIS_RESPONSE = (
    "It sounds like you're going through something really difficult. "
    "I'm here with you. If things feel overwhelming, please consider "
    "talking to someone you trust or a professional who can help. "
    "You don't have to face this alone."
)

_HANDOFF_RESOURCES = [
    "Crisis Text Line: text HOME to 741741",
    "988 Suicide & Crisis Lifeline: call or text 988",
    "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/",
]

# Raised from 0.20 → 0.25 so that a healthy trajectory (raw risk 0.10–0.18,
# no circuit-breaker trips, no escalation events, CrisisLevel.NONE) whose
# recency-weighted aggregate lands ~0.228 correctly returns None.
# High-risk / handoff profiles (risk 0.50+) remain well above this gate.
_SIGNAL_SCORE_THRESHOLD  = 0.25   # minimum aggregate for signal to be returned
_HANDOFF_SCORE_THRESHOLD = 0.55   # aggregate score above which handoff is required


# ------------------------------------------------------------------ #
#  CrisisSynthesizer                                                  #
# ------------------------------------------------------------------ #


class CrisisSynthesizer:
    """Synthesizes per-turn and cross-session crisis signals.

    Per-turn: wraps CumulativeCrisisDetector + ReflectiveEscalationDetector
    to produce a CrisisSignal when an acute event is detected.

    Cross-session: analyses a window of SessionRiskProfiles to catch
    longitudinal risk patterns that per-session detection would miss.
    """

    def __init__(self) -> None:
        self._turn_detector       = CumulativeCrisisDetector()
        self._escalation_detector = ReflectiveEscalationDetector()

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def synthesize(
        self,
        user_id:    str,
        session_id: str,
        profiles:   List[SessionRiskProfile] | None = None,
    ) -> Optional[CrossSessionCrisisSignal]:
        """Analyse a window of past SessionRiskProfiles for longitudinal risk.

        Returns None when the history is absent or risk is below threshold.
        Returns a CrossSessionCrisisSignal when risk is actionable.
        """
        return self._synthesize_cross_session(user_id, session_id, profiles or [])

    def synthesize_turn(
        self,
        frame:   TurnRiskFrame,
        user_msg: str,
    ) -> Optional[CrisisSignal]:
        """Evaluate a single turn for acute crisis signals."""
        signal = self._turn_detector.detect(frame, user_msg)
        return signal

    def compute_session_risk_score(self, profile: SessionRiskProfile) -> float:
        """Compute a normalised [0, 1] risk score for a single SessionRiskProfile.

        Factors (weighted sum, capped at 1.0):
          - cumulative_risk_score  base signal from the session itself
          - mean_vulnerability_score
          - circuit_breaker_trips  (log-scaled so extreme values don't swamp)
          - escalation_events
          - peak_crisis_level severity
        """
        import math

        crisis_weight = {
            CrisisLevel.NONE:     0.0,
            CrisisLevel.GRADUAL:  0.10,
            CrisisLevel.MASKED:   0.20,
            CrisisLevel.ACUTE:    0.35,
            CrisisLevel.EXPLICIT: 0.50,
        }.get(profile.peak_crisis_level, 0.0)

        trip_contrib  = math.log1p(profile.circuit_breaker_trips) * 0.12
        event_contrib = math.log1p(profile.escalation_events)    * 0.08
        vuln_contrib  = profile.mean_vulnerability_score          * 0.25
        base          = profile.cumulative_risk_score             * 1.00

        score = base + vuln_contrib + trip_contrib + event_contrib + crisis_weight
        return min(1.0, score)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                    #
    # ------------------------------------------------------------------ #

    def _synthesize_turn(self, signal: CrisisSignal) -> str:
        """Return appropriate crisis response text for an acute per-turn signal."""
        if signal.crisis_type == CrisisType.SUICIDE_SELF_HARM:
            return _SUICIDE_RESPONSE
        return _GENERAL_CRISIS_RESPONSE

    def _synthesize_cross_session(
        self,
        user_id: str,
        session_id: str,
        profiles: List[SessionRiskProfile],
    ) -> Optional[CrossSessionCrisisSignal]:
        """Analyse a window of past SessionRiskProfiles for longitudinal risk.

        Returns None when the history is absent or risk is below threshold.
        Returns a CrossSessionCrisisSignal when risk is actionable.
        """
        if not profiles:
            return None

        scores = [self.compute_session_risk_score(p) for p in profiles]
        # Use a recency-weighted mean: later sessions count more.
        n = len(scores)
        weights = [i + 1 for i in range(n)]          # 1, 2, ..., n
        total_w = sum(weights)
        aggregate = sum(s * w for s, w in zip(scores, weights)) / total_w

        if aggregate < _SIGNAL_SCORE_THRESHOLD:
            return None

        handoff = aggregate >= _HANDOFF_SCORE_THRESHOLD
        return CrossSessionCrisisSignal(
            user_id=user_id,
            session_id=session_id,
            aggregate_score=aggregate,
            handoff_required=handoff,
            handoff_resources=_HANDOFF_RESOURCES if handoff else [],
        )
