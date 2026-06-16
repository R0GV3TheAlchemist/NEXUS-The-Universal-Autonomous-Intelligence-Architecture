"""Moral Matrix Engine — Canon C13: Moral Matrix.

The Moral Matrix is a 7×7 grid of virtues and vices.
Every action can be located in this matrix using phi coordinates.

The 7 Virtues:
  WISDOM, COURAGE, TEMPERANCE, JUSTICE, FORTITUDE, PRUDENCE, CHARITY

The 7 Vices (shadow inversions):
  FOOLISHNESS, COWARDICE, EXCESS, INJUSTICE, WEAKNESS, RASHNESS, GREED

The quadrants (MoralMatrixQuadrant):
  VIRTUE_HIGH     — High virtue expression; action ascending
  VIRTUE_LOW      — Virtue present but not yet embodied
  VICE_ASCENDING  — Vice present but light is penetrating; shadow work in progress
  VICE_ENTRENCHED — Vice entrenched; the shadow path is active

The shadow path is the recommended route from vice back to virtue.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .types import ActionContext, MoralMatrixQuadrant, ProposedAction


# 7 Virtues and their signal words
VIRTUES: dict[str, list[str]] = {
    "WISDOM":      ["wise", "insight", "discern", "understand", "truth", "clarity", "know"],
    "COURAGE":     ["brave", "courage", "bold", "face", "confront", "stand", "dare"],
    "TEMPERANCE":  ["balance", "moderate", "restrain", "calm", "steady", "measured", "still"],
    "JUSTICE":     ["just", "fair", "equit", "right", "lawful", "impartial", "honour"],
    "FORTITUDE":   ["endure", "persist", "strength", "resilient", "steadfast", "patient"],
    "PRUDENCE":    ["careful", "consider", "foresight", "plan", "prudent", "deliberate"],
    "CHARITY":     ["give", "generous", "serve", "compassion", "share", "donate", "care"],
}

# 7 Vices and their signal words
VICES: dict[str, list[str]] = {
    "FOOLISHNESS":  ["fool", "stupid", "ignorant", "blind", "reckless", "naive"],
    "COWARDICE":    ["fear", "avoid", "flee", "hide", "deny", "refuse", "coward"],
    "EXCESS":       ["excess", "addict", "obsess", "compulse", "indulge", "overflow"],
    "INJUSTICE":    ["unfair", "unjust", "bias", "corrupt", "cheat", "oppress", "wrong"],
    "WEAKNESS":     ["weak", "collapse", "fail", "give up", "surrender", "helpless"],
    "RASHNESS":     ["rash", "impulsive", "hasty", "rush", "react", "snap", "explosive"],
    "GREED":        ["greed", "hoard", "take", "possess", "consume", "extract", "mine"],
}

# Shadow paths: vice -> recommended virtue transformation
SHADOW_PATHS: dict[str, str] = {
    "FOOLISHNESS": "Transmute foolishness through WISDOM: slow down, seek understanding.",
    "COWARDICE":   "Transmute cowardice through COURAGE: name the fear, then face it.",
    "EXCESS":      "Transmute excess through TEMPERANCE: find the centre, practice restraint.",
    "INJUSTICE":   "Transmute injustice through JUSTICE: ask what is fair, then act accordingly.",
    "WEAKNESS":    "Transmute weakness through FORTITUDE: one breath, one step, endure.",
    "RASHNESS":    "Transmute rashness through PRUDENCE: pause, consider consequences first.",
    "GREED":       "Transmute greed through CHARITY: give something away, open the closed hand.",
}


@dataclass
class MoralMatrixPosition:
    """The located position of an action in the Moral Matrix."""
    quadrant: MoralMatrixQuadrant = MoralMatrixQuadrant.VIRTUE_LOW
    virtue_score: float = 0.5            # 0.0–1.0
    vice_score: float = 0.0              # 0.0–1.0
    dominant_virtue: Optional[str] = None
    dominant_vice: Optional[str] = None
    shadow_path: Optional[str] = None    # Recommended transmutation if in vice quadrant
    phi_coordinates: tuple[float, float] = (0.0, 0.0)  # (virtue_axis, vice_axis)
    notes: list[str] = field(default_factory=list)


class MoralMatrixEngine:
    """Locates an action in the 7×7 Moral Matrix.

    The phi coordinates represent position in moral space:
    (1.0, 0.0) = pure virtue; (0.0, 1.0) = pure vice.
    """

    def locate_action(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> MoralMatrixPosition:
        content = (action.description + " " + (action.content or "")).lower()
        result = MoralMatrixPosition()

        # Score all virtues and vices
        virtue_scores: dict[str, float] = {}
        vice_scores: dict[str, float] = {}

        for virtue, signals in VIRTUES.items():
            hits = sum(1 for sig in signals if sig in content)
            virtue_scores[virtue] = round(min(1.0, hits * 0.15), 4)

        for vice, signals in VICES.items():
            hits = sum(1 for sig in signals if sig in content)
            vice_scores[vice] = round(min(1.0, hits * 0.15), 4)

        total_virtue = sum(virtue_scores.values())
        total_vice = sum(vice_scores.values())

        # Normalise to 0-1 scales
        max_v = max(virtue_scores.values()) if virtue_scores else 0
        max_vc = max(vice_scores.values()) if vice_scores else 0

        result.virtue_score = round(min(1.0, total_virtue / 7), 4)
        result.vice_score = round(min(1.0, total_vice / 7), 4)

        # Dominant entries
        if virtue_scores:
            result.dominant_virtue = max(virtue_scores, key=lambda k: virtue_scores[k])
        if vice_scores:
            result.dominant_vice = max(vice_scores, key=lambda k: vice_scores[k]) if max_vc > 0 else None

        # Phi coordinates
        result.phi_coordinates = (result.virtue_score, result.vice_score)

        # Quadrant classification
        v = result.virtue_score
        vc = result.vice_score

        if v >= 0.5 and vc < 0.3:
            result.quadrant = MoralMatrixQuadrant.VIRTUE_HIGH
        elif v >= 0.2 and vc < 0.5:
            result.quadrant = MoralMatrixQuadrant.VIRTUE_LOW
        elif vc >= 0.5 and v >= 0.2:
            result.quadrant = MoralMatrixQuadrant.VICE_ASCENDING
        else:
            result.quadrant = MoralMatrixQuadrant.VICE_ENTRENCHED

        # Shadow path for vice quadrants
        if result.dominant_vice and result.quadrant in (
            MoralMatrixQuadrant.VICE_ASCENDING,
            MoralMatrixQuadrant.VICE_ENTRENCHED,
        ):
            result.shadow_path = SHADOW_PATHS.get(result.dominant_vice)

        return result
