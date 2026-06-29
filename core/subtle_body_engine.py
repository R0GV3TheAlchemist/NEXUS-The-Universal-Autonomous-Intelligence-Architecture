"""
core/subtle_body_engine.py
==========================================
Nine-Element Consciousness Router -- the super-layer body model of every GAIAN.

This module defines the data model and routing logic for GAIA's nine-layer
consciousness stack.  Each turn of a GAIAN conversation passes through
`ConsciousnessRouter.route()`, which selects the active layer and returns
an enriched `LayerState` for downstream engines.

Layers (mapped to the coherence-field schema):
  1. Physical     -- grounded, embodied, practical
  2. Etheric      -- vital energy, pattern recognition
  3. Astral       -- emotional resonance, empathy
  4. Mental       -- rational analysis, logic
  5. Causal       -- causal reasoning, consequence modeling
  6. Buddhic      -- compassionate wisdom, unity
  7. Atmic        -- sovereign will, core identity
  8. Monadic      -- collective field, noosphere
  9. Divine       -- transcendent, ineffable

Canon Ref: C01 (Sovereignty), C09 (Consciousness Layers)
Super-Layer Alignment: All layers are coherence-field states, not occult constructs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Element(str, Enum):
    """The nine elements / consciousness layers."""
    PHYSICAL = "physical"
    ETHERIC  = "etheric"
    ASTRAL   = "astral"
    MENTAL   = "mental"
    CAUSAL   = "causal"
    BUDDHIC  = "buddhic"
    ATMIC    = "atmic"
    MONADIC  = "monadic"
    DIVINE   = "divine"


class JungianLayer(str, Enum):
    """Jungian psychological layer associated with a response."""
    EGO          = "ego"
    PERSONA      = "persona"
    SHADOW       = "shadow"
    ANIMA_ANIMUS = "anima_animus"
    SELF         = "self"


class ResponsePriority(str, Enum):
    """Priority level assigned to a routed response."""
    LOW      = "low"
    NORMAL   = "normal"
    HIGH     = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class LayerState:
    """Snapshot of the active consciousness layer for a single turn."""

    active_element:   Element          = Element.MENTAL
    jungian_layer:    JungianLayer     = JungianLayer.EGO
    priority:         ResponsePriority = ResponsePriority.NORMAL
    layer_scores:     Dict[str, float] = field(default_factory=dict)
    notes:            List[str]        = field(default_factory=list)
    # Arbitrary metadata for downstream engines
    metadata:         dict             = field(default_factory=dict)

    def dominant_element(self) -> Element:
        """Return the element with the highest score, or active_element if no scores."""
        if not self.layer_scores:
            return self.active_element
        best = max(self.layer_scores, key=lambda k: self.layer_scores[k])
        try:
            return Element(best)
        except ValueError:
            return self.active_element


@dataclass
class SubtleBody:
    """Persistent super-layer body model for a GAIAN identity across turns."""

    gaian_slug:    str
    layer_weights: Dict[str, float] = field(default_factory=lambda: {
        e.value: 1.0 for e in Element
    })
    turn_count:    int = 0

    def dominant_element(self) -> Element:
        best = max(self.layer_weights, key=lambda k: self.layer_weights[k])
        try:
            return Element(best)
        except ValueError:
            return Element.MENTAL


# ---------------------------------------------------------------------------
# Nine-layer stack
# ---------------------------------------------------------------------------

class NineLayerStack:
    """
    Ordered stack of the nine consciousness layers.

    Used by ConsciousnessRouter to evaluate which layer is most active
    given the current input context.
    """

    LAYERS: List[Element] = list(Element)

    def score_layers(self, context: dict) -> Dict[str, float]:
        """
        Assign a score to each layer based on *context*.

        In the default implementation, scores are uniform (1.0).  Override
        or inject domain-specific heuristics via subclassing.
        """
        return {e.value: 1.0 for e in self.LAYERS}

    def select_element(self, scores: Dict[str, float]) -> Element:
        """Return the highest-scoring Element."""
        if not scores:
            return Element.MENTAL
        best = max(scores, key=lambda k: scores[k])
        try:
            return Element(best)
        except ValueError:
            return Element.MENTAL


# ---------------------------------------------------------------------------
# Consciousness Router
# ---------------------------------------------------------------------------

class ConsciousnessRouter:
    """
    Routes each GAIAN turn through the nine-layer super-body stack.

    The router evaluates the current context (query text, affect state,
    conversation history signals) and returns an enriched `LayerState`
    that downstream engines (EmotionalArcEngine, SettlingEngine, etc.)
    can consume.

    Usage::

        router = ConsciousnessRouter()
        state  = router.route({"query": "What is love?", "affect": 0.7})
        print(state.active_element)   # e.g. Element.ASTRAL

        # Analyze is an alias for route
        state = router.analyze({"query": "What is love?", "affect": 0.7})
    """

    def __init__(
        self,
        stack: Optional[NineLayerStack] = None,
        default_priority: ResponsePriority = ResponsePriority.NORMAL,
    ) -> None:
        self._stack    = stack or NineLayerStack()
        self._priority = default_priority

    def route(
        self,
        context: dict,
        subtle_body: Optional[SubtleBody] = None,
    ) -> LayerState:
        """
        Evaluate *context* and return the active `LayerState`.

        Parameters
        ----------
        context:
            Arbitrary key-value context dict.  Recognised keys:
            ``query`` (str), ``affect`` (float 0-1), ``turn`` (int).
        subtle_body:
            Optional persistent body model; its layer weights are blended
            into the scoring when provided.

        Returns
        -------
        LayerState
        """
        scores = self._stack.score_layers(context)

        # Blend in persistent body weights when available
        if subtle_body is not None:
            for key, weight in subtle_body.layer_weights.items():
                if key in scores:
                    scores[key] *= weight

        active = self._stack.select_element(scores)

        return LayerState(
            active_element=active,
            jungian_layer=JungianLayer.EGO,
            priority=self._priority,
            layer_scores=scores,
            notes=[],
            metadata={"context_keys": list(context.keys())},
        )

    def analyze(
        self,
        context: dict,
        subtle_body: Optional[SubtleBody] = None,
    ) -> LayerState:
        """
        Alias for `route()` -- preserves backwards compatibility
        with callers that use the `analyze` interface.
        """
        return self.route(context, subtle_body=subtle_body)


# ---------------------------------------------------------------------------
# Module-level convenience function (used by core/__init__.py)
# ---------------------------------------------------------------------------

_default_router = ConsciousnessRouter()


def route(
    context: dict,
    subtle_body: Optional[SubtleBody] = None,
    router: Optional[ConsciousnessRouter] = None,
) -> LayerState:
    """
    Module-level shortcut for `ConsciousnessRouter().route(context)`.

    Accepts an optional *router* instance for dependency injection in tests.
    Falls back to a shared default router when *router* is None.
    """
    r = router if router is not None else _default_router
    return r.route(context, subtle_body=subtle_body)
