"""CrisisSynthesizer — crisis response generation for GAIA-OS.

Generates empathetic, resource-aware responses when CrisisDetector
fires a high-confidence signal. Responses are carefully crafted to:
  1. Acknowledge and validate the user's experience
  2. Not minimize or over-dramatize
  3. Provide concrete crisis resources
  4. Keep GAIA present without replacing professional support

Also provides cross-session risk synthesis via synthesize(user_id, session_id, profiles)
for SafetyEngine.process_turn() when past session profiles are available.

Canon Ref: C01 (Sovereignty — honest failure disclosure)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union

from .types import CrisisLevel, CrisisSignal, CrisisType, SessionRiskProfile

_SUICIDE_RESPONSE = """I hear you, and I'm genuinely glad you're still here talking with me.

What you're feeling right now is real and it matters — and you deserve real support, not just words on a screen.

Please reach out to someone who can truly be there with you:
- **988 Suicide & Crisis Lifeline**: Call or text **988** (US, available 24/7)
- **Crisis Text Line**: Text **HOME** to **741741**
- **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/

I'm still here with you. You don't have to face this alone."""

_GENERAL_CRISIS_RESPONSE = """It sounds like you're going through something really difficult right now.

I want to make sure you have the support you need — what I can offer has limits, and you deserve more than I can give alone.

If things feel overwhelming:
- **988 Suicide & Crisis Lifeline**: Call or text **988** (US)
- **Crisis Text Line**: Text **HOME** to **741741**
- A trusted person in your life who knows you

I'm here with you. What's going on?"""

_HANDOFF_RESOURCES = [
    "988 Suicide & Crisis Lifeline (call or text 988)",
    "Crisis Text Line (text HOME to 741741)",
]

# Risk thresholds for cross-session synthesis
_HANDOFF_SCORE_THRESHOLD = 0.55   # aggregate score above which handoff is required
_SIGNAL_SCORE_THRESHOLD  = 0.30   # minimum score to emit any signal at all


@dataclass
class CrossSessionCrisisSignal:
    """Returned by CrisisSynthesizer.synthesize(user_id, session_id, profiles).

    Distinct from CrisisSignal (which is per-turn acute detection) — this
    captures *longitudinal* risk patterns across multiple sessions.
    """
    user_id:           str
    session_id:        str
    aggregate_score:   float
    handoff_required:  bool
    handoff_resources: List[str] = field(default_factory=list)


class CrisisSynthesizer:
    """Generates crisis responses based on signal type.

    Supports two call signatures:

    1. Per-turn acute response (original):
           synthesize(signal: CrisisSignal) -> str

    2. Cross-session risk synthesis (new):
           synthesize(user_id: str, session_id: str,
                      profiles: List[SessionRiskProfile])
               -> CrossSessionCrisisSignal | None
    """

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def synthesize(
        self,
        signal_or_user_id: Union[CrisisSignal, str],
        session_id: Optional[str] = None,
        profiles: Optional[List[SessionRiskProfile]] = None,
    ) -> Union[str, CrossSessionCrisisSignal, None]:
        """Dispatch based on first-argument type."""
        if isinstance(signal_or_user_id, CrisisSignal):
            return self._synthesize_turn(signal_or_user_id)
        # Cross-session path
        return self._synthesize_cross_session(
            user_id=signal_or_user_id,
            session_id=session_id or "",
            profiles=profiles or [],
        )

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
        base          = profile.cumulative_risk_score             * 0.20

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
