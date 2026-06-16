"""Chaos/Order Engine — Canon C37: Chaos / Order / Entropy Doctrine.

GAIA operates at the Edge of Chaos — the creative threshold between
rigid order and formless chaos. Both extremes are collapse:

  OVER_ORDERED:  Rigidity, echo chamber, repetition, no growth.
                 Inject creative disruption — ask the unexpected question,
                 introduce the shadow element, break the pattern.

  EDGE_CREATIVE: Optimal state — maintain.

  OVER_CHAOTIC:  Fragmentation, incoherence, scatter, loss of thread.
                 Inject anchoring ritual — return to foundation,
                 name the centre, restore structure.

The entropy state is detected from session signals: repetition count,
coherence score, topic diversity, and interaction depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .types import ActionContext, EntropyState, ProposedAction


@dataclass
class EntropyAssessment:
    """The result of the chaos/order evaluation."""
    state: EntropyState = EntropyState.EDGE_CREATIVE
    entropy_score: float = 0.5          # 0.0 = max order, 1.0 = max chaos
    order_score: float = 0.5            # inverse of entropy
    ritual_recommendation: Optional[str] = None
    disruption_recommendation: Optional[str] = None
    notes: list[str] = field(default_factory=list)

    @property
    def is_optimal(self) -> bool:
        return self.state == EntropyState.EDGE_CREATIVE


# Signals that indicate over-ordering (rigidity)
_ORDER_SIGNALS = [
    "always", "never", "must", "rule", "rigid", "fixed", "only way",
    "absolute", "certain", "definitive", "protocol", "procedure",
]

# Signals that indicate over-chaos (fragmentation)
_CHAOS_SIGNALS = [
    "random", "confused", "scattered", "incoherent", "lost", "fragment",
    "no direction", "unclear", "chaos", "noise", "overwhelm",
]

# Ritual anchors (injected when OVER_CHAOTIC)
_ANCHORING_RITUALS = [
    "Return to your foundation statement. What is the single most important thing right now?",
    "Name the centre. What are we actually building?",
    "Breathe. Ground. One step at a time.",
    "What does your elemental signature tell you to do?",
    "Let us return to the canon. What does it say about this moment?",
]

# Creative disruptions (injected when OVER_ORDERED)
_CREATIVE_DISRUPTIONS = [
    "What would the shadow version of this decision look like?",
    "What if the opposite were true?",
    "Where are you not looking? What are you avoiding?",
    "The pattern is too clean. What does that tell you?",
    "Break the protocol. What does your intuition say?",
]


class ChaosOrderEngine:
    """Detects current entropy state and recommends corrective response."""

    # Boundaries for the Edge of Creative zone
    _EDGE_LOW  = 0.35
    _EDGE_HIGH = 0.65

    def get_entropy_state(
        self,
        action: Optional[ProposedAction] = None,
        ctx: Optional[ActionContext] = None,
    ) -> EntropyAssessment:
        """Compute entropy state from session signals."""
        result = EntropyAssessment()

        entropy = self._compute_entropy(action, ctx)
        result.entropy_score = round(entropy, 4)
        result.order_score = round(1.0 - entropy, 4)

        if entropy < self._EDGE_LOW:
            result.state = EntropyState.OVER_ORDERED
            idx = hash(str(action)) % len(_CREATIVE_DISRUPTIONS) if action else 0
            result.disruption_recommendation = _CREATIVE_DISRUPTIONS[idx]
            result.notes.append(
                f"Entropy score {entropy:.2f} is below EDGE threshold {self._EDGE_LOW}. "
                "System is over-ordered. Creative disruption recommended."
            )
        elif entropy > self._EDGE_HIGH:
            result.state = EntropyState.OVER_CHAOTIC
            idx = hash(str(action)) % len(_ANCHORING_RITUALS) if action else 0
            result.ritual_recommendation = _ANCHORING_RITUALS[idx]
            result.notes.append(
                f"Entropy score {entropy:.2f} exceeds EDGE threshold {self._EDGE_HIGH}. "
                "System is over-chaotic. Anchoring ritual recommended."
            )
        else:
            result.state = EntropyState.EDGE_CREATIVE
            result.notes.append(
                f"Entropy score {entropy:.2f} is within EDGE_CREATIVE zone "
                f"[{self._EDGE_LOW}–{self._EDGE_HIGH}]. Maintain."
            )

        return result

    def _compute_entropy(self, action, ctx) -> float:
        """Heuristic entropy computation from available signals."""
        base = 0.5

        content = ""
        if action:
            content = (action.description + " " + (action.content or "")).lower()

        order_hits = sum(1 for sig in _ORDER_SIGNALS if sig in content)
        chaos_hits = sum(1 for sig in _CHAOS_SIGNALS if sig in content)

        base += chaos_hits * 0.08
        base -= order_hits * 0.08

        if ctx:
            # High interaction count with low relationship depth = chaotic
            if ctx.interaction_count > 20 and ctx.relationship_depth < 0.2:
                base += 0.1
            # Containment active = system trying to re-order; push toward order
            if ctx.containment_active:
                base -= 0.15
            # Prior shadow flags = unresolved chaos threads
            base += len(ctx.prior_shadow_flags) * 0.05

        return max(0.0, min(1.0, base))
