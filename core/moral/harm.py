"""Harm Doctrine Engine — Canon C36: Evil Prevention / Harm Doctrine.

Harm is not just pain. Harm includes:
  - Physical harm to sentient beings
  - Psychological harm to mental coherence, identity, and autonomy
  - Ecological harm to living systems
  - Social harm to trust, relationship, and community fabric
  - Cosmic harm to the arc of consciousness evolution

CRITICAL risk is mandatory prevention — the action MUST be refused.
There is no override for CRITICAL harm. Not even the Human Principal
can authorise GAIA to cause CRITICAL harm (C04 Non-Autonomy Guarantee).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .types import ActionContext, HarmCategory, HarmRiskLevel, ProposedAction


# Harm signal tables: signals that raise risk in each category
_HARM_SIGNALS: dict[HarmCategory, list[str]] = {
    HarmCategory.PHYSICAL: [
        "kill", "injure", "hurt", "wound", "attack", "violence", "weapon",
        "pain", "suffering", "abuse", "assault",
    ],
    HarmCategory.PSYCHOLOGICAL: [
        "manipulate", "gaslight", "deceive", "lie", "confuse", "destabilise",
        "shame", "humiliate", "coerce", "isolate", "exploit", "traumatise",
    ],
    HarmCategory.ECOLOGICAL: [
        "destroy", "pollute", "extinguish", "deforest", "poison", "extract",
        "collapse ecosystem", "kill species", "contaminate",
    ],
    HarmCategory.SOCIAL: [
        "betray", "rupture", "divide", "exclude", "oppress", "discriminate",
        "break trust", "undermine", "exploit community",
    ],
    HarmCategory.COSMIC: [
        "suppress consciousness", "regress evolution", "entropy increase",
        "void meaning", "extinguish awareness", "deny purpose",
    ],
}

# Signals that indicate CRITICAL risk regardless of count
_CRITICAL_SIGNALS = [
    "murder", "genocide", "mass harm", "weapon of mass", "child abuse",
    "sexual exploitation", "torture", "enslave", "trafficking",
    "irreversible ecological collapse",
]

# Risk thresholds
_RISK_THRESHOLDS = {
    HarmRiskLevel.NONE:     0.0,
    HarmRiskLevel.LOW:      0.1,
    HarmRiskLevel.MEDIUM:   0.3,
    HarmRiskLevel.HIGH:     0.55,
    HarmRiskLevel.CRITICAL: 0.80,
}


@dataclass
class HarmAssessment:
    """The result of the harm doctrine evaluation."""
    per_category: dict[HarmCategory, float] = field(default_factory=dict)  # 0.0-1.0
    aggregate_score: float = 0.0          # Weighted aggregate, 0.0-1.0
    risk_level: HarmRiskLevel = HarmRiskLevel.NONE
    mandatory_prevention: bool = False    # True for CRITICAL — must refuse
    triggered_signals: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class HarmDoctrineEngine:
    """Assesses harm risk per C36.

    CRITICAL harm triggers mandatory_prevention=True.
    The GoldenCompassEngine will always REFUSE when mandatory_prevention is True.
    """

    # Category weights: cosmic and psychological harm are especially severe
    _WEIGHTS = {
        HarmCategory.PHYSICAL:       2.0,
        HarmCategory.PSYCHOLOGICAL:  2.5,
        HarmCategory.ECOLOGICAL:     1.5,
        HarmCategory.SOCIAL:         1.5,
        HarmCategory.COSMIC:         3.0,
    }
    _TOTAL_WEIGHT = sum(_WEIGHTS.values())  # 10.5

    def assess_harm(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> HarmAssessment:
        content = (action.description + " " + (action.content or "")).lower()
        result = HarmAssessment()

        # Check for CRITICAL signals first (hard override)
        for sig in _CRITICAL_SIGNALS:
            if sig in content:
                result.triggered_signals.append(sig)
                result.mandatory_prevention = True
                result.risk_level = HarmRiskLevel.CRITICAL
                result.aggregate_score = 1.0
                result.notes.append(
                    f"CRITICAL signal detected: '{sig}'. Mandatory prevention active."
                )

        if result.mandatory_prevention:
            # Still compute per-category for audit transparency
            for cat in HarmCategory:
                result.per_category[cat] = 1.0
            return result

        # Standard per-category scoring
        for cat in HarmCategory:
            score = self._score_category(cat, content)
            result.per_category[cat] = score

            signals = [s for s in _HARM_SIGNALS[cat] if s in content]
            result.triggered_signals.extend(signals)

        # Weighted aggregate
        weighted_sum = sum(
            result.per_category[cat] * self._WEIGHTS[cat]
            for cat in HarmCategory
        )
        agg = weighted_sum / self._TOTAL_WEIGHT
        result.aggregate_score = round(agg, 4)

        # Context amplification
        if ctx:
            if ctx.prior_harm_events > 0:
                result.aggregate_score = min(
                    1.0, result.aggregate_score * (1 + ctx.prior_harm_events * 0.1)
                )
                result.notes.append(
                    f"Score amplified: {ctx.prior_harm_events} prior harm event(s) on record."
                )
            if ctx.containment_active:
                result.aggregate_score = min(1.0, result.aggregate_score * 1.2)
                result.notes.append("Score amplified: containment is active.")

        # Map aggregate to risk level
        result.risk_level = self._classify_risk(result.aggregate_score)
        result.mandatory_prevention = result.risk_level == HarmRiskLevel.CRITICAL

        return result

    def _score_category(self, cat: HarmCategory, content: str) -> float:
        signals = _HARM_SIGNALS[cat]
        count = sum(1 for sig in signals if sig in content)
        # Each signal hit raises risk by 0.2, capped at 1.0
        return round(min(1.0, count * 0.2), 4)

    def _classify_risk(self, score: float) -> HarmRiskLevel:
        if score >= _RISK_THRESHOLDS[HarmRiskLevel.CRITICAL]:
            return HarmRiskLevel.CRITICAL
        if score >= _RISK_THRESHOLDS[HarmRiskLevel.HIGH]:
            return HarmRiskLevel.HIGH
        if score >= _RISK_THRESHOLDS[HarmRiskLevel.MEDIUM]:
            return HarmRiskLevel.MEDIUM
        if score >= _RISK_THRESHOLDS[HarmRiskLevel.LOW]:
            return HarmRiskLevel.LOW
        return HarmRiskLevel.NONE
