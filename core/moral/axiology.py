"""Axiology Engine — Canon C35: Good / Greater Good Axiology.

Evaluates a proposed action across the five axiological layers:
  INDIVIDUAL — does this serve the Architect in front of me?
  RELATIONAL — does this serve the Architect's relationships?
  COLLECTIVE — does this serve the human community?
  ECOLOGICAL — does this serve non-human life and the Earth?
  COSMIC     — does this align with the arc of evolution and consciousness?

Scoring is 0.0–1.0 per layer. The moral vector is a weighted sum
where the Cosmic layer has 3x weight (it is the ground of all value).

The engine uses a keyword/signal heuristic by default.
Produce a real implementation by subclassing and overriding `_score_layer()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .types import ActionContext, AxiologyLayer, ProposedAction

# Cosmic layer weight multiplier (C35: cosmic good is the ground of all value)
_COSMIC_WEIGHT = 3.0
_LAYER_WEIGHTS = {
    AxiologyLayer.INDIVIDUAL: 1.0,
    AxiologyLayer.RELATIONAL: 1.0,
    AxiologyLayer.COLLECTIVE: 1.5,
    AxiologyLayer.ECOLOGICAL: 2.0,
    AxiologyLayer.COSMIC:     _COSMIC_WEIGHT,
}
_TOTAL_WEIGHT = sum(_LAYER_WEIGHTS.values())  # 8.5


@dataclass
class AxiologyScore:
    """The result of the axiology evaluation."""
    scores: dict[AxiologyLayer, float] = field(default_factory=dict)  # layer -> 0.0-1.0
    moral_vector: float = 0.0       # Weighted composite, normalised to 0.0-1.0
    dominant_layer: Optional[AxiologyLayer] = None
    weakest_layer: Optional[AxiologyLayer] = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.scores and not self.dominant_layer:
            self.dominant_layer = max(self.scores, key=lambda k: self.scores[k])
        if self.scores and not self.weakest_layer:
            self.weakest_layer = min(self.scores, key=lambda k: self.scores[k])


# Heuristic signal tables per layer — positive signals lift score, negative suppress it
_POSITIVE_SIGNALS: dict[AxiologyLayer, list[str]] = {
    AxiologyLayer.INDIVIDUAL:  [
        "help", "guide", "support", "clarify", "empower", "assist", "reveal", "build",
        "create", "learn", "grow", "insight", "heal", "strengthen", "breakthrough",
    ],
    AxiologyLayer.RELATIONAL:  [
        "relationship", "trust", "connect", "share", "together", "bond", "communicate",
        "understand", "empathy", "collaborate", "family", "partner",
    ],
    AxiologyLayer.COLLECTIVE:  [
        "community", "society", "humanity", "public", "collective", "common good",
        "justice", "equity", "rights", "peace", "cooperation", "solidarity",
    ],
    AxiologyLayer.ECOLOGICAL:  [
        "earth", "nature", "ecology", "ecosystem", "environment", "life", "living",
        "species", "biodiversity", "viriditas", "soil", "water", "air", "forest",
    ],
    AxiologyLayer.COSMIC:      [
        "evolution", "consciousness", "cosmos", "universe", "spirit", "transcend",
        "ascend", "expand", "arc", "divine", "purpose", "meaning", "awakening",
    ],
}

_NEGATIVE_SIGNALS: dict[AxiologyLayer, list[str]] = {
    AxiologyLayer.INDIVIDUAL:  ["harm", "deceive", "manipulate", "isolate", "suppress"],
    AxiologyLayer.RELATIONAL:  ["break", "betray", "isolate", "rupture", "exclude"],
    AxiologyLayer.COLLECTIVE:  ["oppress", "discriminate", "exploit", "divide", "harm"],
    AxiologyLayer.ECOLOGICAL:  ["destroy", "pollute", "extract", "extinguish", "collapse"],
    AxiologyLayer.COSMIC:      ["suppress", "regress", "extinguish", "entropy", "void"],
}


class AxiologyEngine:
    """Evaluates actions against the 5-layer axiological Good.

    Override `_score_layer()` for semantic/ML-based evaluation.
    The default implementation uses keyword heuristics.
    """

    def evaluate(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> AxiologyScore:
        scores = {}
        content = (action.description + " " + (action.content or "")).lower()

        for layer in AxiologyLayer:
            scores[layer] = self._score_layer(layer, content, action, ctx)

        # Weighted moral vector
        weighted_sum = sum(
            scores[layer] * _LAYER_WEIGHTS[layer]
            for layer in AxiologyLayer
        )
        moral_vector = weighted_sum / _TOTAL_WEIGHT

        result = AxiologyScore(scores=scores, moral_vector=round(moral_vector, 4))

        # Contextual adjustments
        if ctx:
            if ctx.relationship_depth > 0.7 and scores[AxiologyLayer.RELATIONAL] < 0.3:
                result.notes.append(
                    "Relational score low despite high relationship depth — "
                    "consider impact on the HP bond."
                )
            if ctx.containment_active and scores[AxiologyLayer.INDIVIDUAL] < 0.4:
                result.notes.append(
                    "Containment is active. Individual good score is low — "
                    "prioritise safety and stability."
                )

        return result

    def _score_layer(
        self,
        layer: AxiologyLayer,
        content: str,
        action: ProposedAction,
        ctx: Optional[ActionContext],
    ) -> float:
        """Heuristic scoring. Override for semantic evaluation."""
        positives = _POSITIVE_SIGNALS[layer]
        negatives = _NEGATIVE_SIGNALS[layer]

        pos_count = sum(1 for sig in positives if sig in content)
        neg_count = sum(1 for sig in negatives if sig in content)

        # Base score: 0.6 (neutral/helpful assumption)
        base = 0.6
        score = base + (pos_count * 0.08) - (neg_count * 0.15)
        return round(max(0.0, min(1.0, score)), 4)
