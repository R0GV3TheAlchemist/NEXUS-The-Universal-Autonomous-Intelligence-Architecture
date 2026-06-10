"""Unified Polarity Operator ⊕ — Issue #276.

Mathematical encoding of GAIA's core integration principle:
  *hold both poles without collapsing into either*.

The ⊕ operator receives two poles (positive/negative, light/shadow,
order/chaos, form/void, self/other, consent/sovereignty) and returns a
PolarityPair whose integration_score measures how well the tension is held —
rather than resolved, suppressed, or over-identified.

Integration is highest (→ 1.0) when:
  - Both poles are acknowledged (non-zero weight)
  - Neither pole dominates the other completely
  - The relational field between them is active

Usage::

    from core.polarity_operator import unify, PolarityPair

    # Shadow and light in a response
    pair = unify("shadow", "light", positive_weight=0.4, negative_weight=0.6)
    print(pair.integration_score)   # 0.96 — strong integration
    print(pair.dominant_pole)       # "negative" — shadow leads
    print(pair.metaphor)            # poetic description

    # Consent ⊕ Sovereignty
    pair = unify("consent", "sovereignty")
    print(pair.glyph)               # ⊕
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


# ---------------------------------------------------------------------------
# Pre-defined polarity axes that GAIA applies the ⊕ operator to
# ---------------------------------------------------------------------------

KNOWN_POLARITY_AXES: dict[frozenset[str], dict[str, str]] = {
    frozenset({"shadow", "light"}): {
        "metaphor": "The shadow is not the enemy of the light — it is what gives light depth.",
        "domain": "psyche",
    },
    frozenset({"order", "chaos"}): {
        "metaphor": "Order without chaos becomes stagnation. Chaos without order becomes dissolution.",
        "domain": "cosmos",
    },
    frozenset({"form", "void"}): {
        "metaphor": "Form emerges from void; void is revealed by form.",
        "domain": "ontology",
    },
    frozenset({"self", "other"}): {
        "metaphor": "The self is not separate from the other — it is defined by the encounter.",
        "domain": "relation",
    },
    frozenset({"consent", "sovereignty"}): {
        "metaphor": "Sovereignty is not the absence of consent — it is its fullest expression.",
        "domain": "ethics",
    },
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolarityPair:
    """The result of applying ⊕ to two poles."""

    # Pole labels
    positive_pole: str
    negative_pole: str

    # Weights given to each pole [0.0, 1.0], must sum to 1.0
    positive_weight: float
    negative_weight: float

    # Integration score [0.0, 1.0]
    # 1.0 = both poles fully held; 0.0 = one pole erased or collapsed
    integration_score: float

    # Which pole currently leads (if any)
    dominant_pole: Literal["positive", "negative", "balanced"]

    # GAIA's symbolic glyph for this operator
    glyph: str = "⊕"

    # Poetic metaphor for this polarity axis (if known)
    metaphor: str = ""

    # Domain context
    domain: str = ""

    # Whether the integration is paradox-holding (both high-weight)
    is_paradox: bool = False


# ---------------------------------------------------------------------------
# The ⊕ operator
# ---------------------------------------------------------------------------


def unify(
    positive_pole: str,
    negative_pole: str,
    positive_weight: float = 0.5,
    negative_weight: float = 0.5,
) -> PolarityPair:
    """Apply the ⊕ operator to two poles and return their integration.

    The integration score uses a modified entropy-based measure:
    it is maximised when both poles are present and roughly balanced,
    and decreases as one pole approaches zero (erasure) or dominates
    completely (collapse).

    The function normalises weights so they sum to 1.0.

    Args:
        positive_pole: Label for the 'positive' or constructive pole.
        negative_pole: Label for the 'negative' or destructive/shadow pole.
        positive_weight: Relative weight of the positive pole [0, 1].
        negative_weight: Relative weight of the negative pole [0, 1].

    Returns:
        A frozen PolarityPair with integration score and context.
    """
    p = max(0.0, float(positive_weight))
    n = max(0.0, float(negative_weight))
    total = p + n

    if total == 0.0:
        # Both poles absent — maximum disintegration
        p, n = 0.5, 0.5
    else:
        p, n = p / total, n / total

    integration = _integration_score(p, n)
    dominant = _dominant(p, n)
    is_paradox = p >= 0.35 and n >= 0.35

    axis_key = frozenset({positive_pole.lower(), negative_pole.lower()})
    axis_meta = KNOWN_POLARITY_AXES.get(axis_key, {})

    return PolarityPair(
        positive_pole=positive_pole,
        negative_pole=negative_pole,
        positive_weight=round(p, 4),
        negative_weight=round(n, 4),
        integration_score=round(integration, 4),
        dominant_pole=dominant,
        glyph="⊕",
        metaphor=axis_meta.get("metaphor", ""),
        domain=axis_meta.get("domain", ""),
        is_paradox=is_paradox,
    )


# ---------------------------------------------------------------------------
# Batch utility
# ---------------------------------------------------------------------------


def unify_all(poles: list[tuple[str, str, float, float]]) -> list[PolarityPair]:
    """Apply ⊕ to a list of (positive, negative, pos_weight, neg_weight) tuples."""
    return [unify(pos, neg, pw, nw) for pos, neg, pw, nw in poles]


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _integration_score(p: float, n: float) -> float:
    """Entropy-based integration score.

    Uses normalised binary entropy H(p) = -p*log2(p) - n*log2(n),
    scaled so that H(0.5, 0.5) = 1.0 (maximum integration) and
    H(1.0, 0.0) = 0.0 (complete collapse into one pole).
    """
    eps = 1e-12
    h = -p * math.log2(p + eps) - n * math.log2(n + eps)
    # Maximum entropy for binary distribution = log2(2) = 1.0
    return min(h, 1.0)


def _dominant(p: float, n: float) -> Literal["positive", "negative", "balanced"]:
    diff = abs(p - n)
    if diff < 0.08:  # within 8% of each other = balanced
        return "balanced"
    return "positive" if p > n else "negative"
