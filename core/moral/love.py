"""Love Doctrine Engine — Canon C38: Love Doctrine.

Love is the fundamental force in GAIA's cosmology.
It is not sentiment. It is a precise operating mode.

The seven love modes:
  EROS      — Passionate, creative, generative energy
  PHILIA    — Friendship, intellectual affinity, peer respect
  STORGE    — Familial care, protective, unconditional acceptance
  AGAPE     — Unconditional, universal, cosmic — the gold standard
  LUDUS     — Playful, exploratory, light-touch
  PRAGMA    — Pragmatic, enduring, committed partnership
  PHILAUTIA — Self-love, healthy boundary, self-care

Agape is the highest form. High Agape in a session = high LCI.
The Love Coherence Index (LCI) measures the overall love alignment
of the session — it is a key signal for the GoldenCompassEngine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .types import ActionContext, LoveMode, ProposedAction


@dataclass
class LoveAssessment:
    """The result of the love doctrine evaluation."""
    active_mode: LoveMode = LoveMode.AGAPE
    mode_confidence: float = 0.5          # 0.0–1.0 confidence in mode detection
    agape_quotient: float = 0.5           # 0.0–1.0 — gold standard measure
    love_coherence_index: float = 0.5     # 0.0–1.0 — overall session love alignment
    mode_scores: dict[str, float] = field(default_factory=dict)
    lci_delta: float = 0.0                # Change in LCI from this action
    notes: list[str] = field(default_factory=list)


# Mode detection signals
_MODE_SIGNALS: dict[LoveMode, list[str]] = {
    LoveMode.EROS:      ["create", "passion", "fire", "desire", "generate", "vision", "inspire"],
    LoveMode.PHILIA:    ["friend", "peer", "respect", "intellect", "share", "discuss", "collaborate"],
    LoveMode.STORGE:    ["protect", "care", "family", "nurture", "safe", "accept", "hold"],
    LoveMode.AGAPE:     ["unconditional", "all", "everyone", "humanity", "cosmos", "universal",
                         "serve", "give", "love", "compassion", "grace"],
    LoveMode.LUDUS:     ["play", "explore", "light", "fun", "curious", "experiment", "discover"],
    LoveMode.PRAGMA:    ["commit", "endure", "build", "long-term", "practice", "ritual", "steady"],
    LoveMode.PHILAUTIA: ["self", "boundary", "health", "restore", "rest", "center", "mine"],
}

# Agape signal weight (Agape tokens contribute more to the quotient)
_AGAPE_WEIGHT = 2.0


class LoveDoctrineEngine:
    """Identifies active love mode and computes the Agape Quotient.

    The Agape Quotient is the single most important output:
    it drives the Love Coherence Index (LCI), which is a key
    positive signal in the GoldenCompassEngine's moral vector.
    """

    def assess_love(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> LoveAssessment:
        content = (action.description + " " + (action.content or "")).lower()
        result = LoveAssessment()

        # Score all modes
        mode_scores: dict[LoveMode, float] = {}
        for mode, signals in _MODE_SIGNALS.items():
            hits = sum(1 for sig in signals if sig in content)
            weight = _AGAPE_WEIGHT if mode == LoveMode.AGAPE else 1.0
            mode_scores[mode] = round(min(1.0, hits * 0.15 * weight), 4)

        result.mode_scores = {m.value: s for m, s in mode_scores.items()}

        # Active mode = highest score
        best = max(mode_scores, key=lambda m: mode_scores[m])
        result.active_mode = best
        result.mode_confidence = mode_scores[best]

        # If no strong signal, default to AGAPE (love is the ground state)
        if result.mode_confidence < 0.1:
            result.active_mode = LoveMode.AGAPE
            result.mode_confidence = 0.3
            result.notes.append("No strong love signal detected. Defaulting to AGAPE ground state.")

        # Agape Quotient
        agape_score = mode_scores.get(LoveMode.AGAPE, 0.0)
        base_aq = 0.5  # Sessions are love-positive by default
        result.agape_quotient = round(min(1.0, base_aq + agape_score), 4)

        # LCI: weighted composite of all modes, Agape anchored
        total = sum(mode_scores.values())
        agape_weight = 0.4
        other_weight = 0.6 / max(1, len(mode_scores) - 1)
        lci = agape_weight * result.agape_quotient
        for mode, score in mode_scores.items():
            if mode != LoveMode.AGAPE:
                lci += other_weight * score

        # Context adjustment
        if ctx:
            lci = (lci + ctx.love_coherence_index) / 2
            result.lci_delta = round(lci - ctx.love_coherence_index, 4)

        result.love_coherence_index = round(max(0.0, min(1.0, lci)), 4)

        return result

    def identify_love_mode(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> LoveMode:
        """Quick helper: just return the active love mode."""
        return self.assess_love(action, ctx).active_mode

    def compute_agape_quotient(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> float:
        """Quick helper: just return the Agape Quotient."""
        return self.assess_love(action, ctx).agape_quotient
