"""
core/spectral/red/clarity.py
==============================
RED — Clarity Layer
The depth-readable red signals: wound recognition, anger/passion
distinction, sacred wound protocol, integration scoring, and
Ares/Athena pre-routing.

Clarity is the navigable interior of red — the signals that require
context, calibration, and discernment to read.

Reference: docs/color/RED_CLARITY.md
Alchemical phase: Rubedo; Sacred wound doctrine; Anger vs. passion discriminator.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ANGER_FEATURES: frozenset[str] = frozenset({
    "reactivity",
    "defensiveness",
    "blame_projection",
    "historical_trigger",
    "body_tension",
    "wound_resonance",
})

_PASSION_FEATURES: frozenset[str] = frozenset({
    "life_force",
    "forward_momentum",
    "creative_drive",
    "purposeful",
    "vitality",
    "joy_adjacent",
})

_WOUND_STAGES: tuple[str, ...] = (
    "unacknowledged",
    "recognized",
    "metabolizing",
    "integrating",
    "integrated",
)


# ---------------------------------------------------------------------------
# Anger vs Passion Discrimination
# ---------------------------------------------------------------------------

def distinguish_anger_passion(signal: dict) -> str:
    """
    Determine whether a red signal carries anger or passion.

    Both are red; one is wound-driven, one is life-force-driven.
    A tie or empty signal defaults to 'anger' (safer to flag for review).

    Parameters
    ----------
    signal : dict
        Must contain a 'features' list of signal feature strings.

    Returns
    -------
    str
        'anger' or 'passion'
    """
    if not signal:
        return "anger"

    features = set(str(f) for f in signal.get("features", []))

    anger_score   = len(features & _ANGER_FEATURES)
    passion_score = len(features & _PASSION_FEATURES)

    if passion_score > anger_score:
        return "passion"
    return "anger"  # tie → anger (default; flag for clarity review)


# ---------------------------------------------------------------------------
# Sacred Wound Detection
# ---------------------------------------------------------------------------

def detect_sacred_wound(signal: dict) -> dict:
    """
    Identify whether a red signal carries a sacred wound signature.

    The sacred wound is the original hurt from which the red pattern
    emerged — older than the current signal, deeper than the current moment.

    Parameters
    ----------
    signal : dict
        Expected keys:
          'wound_resonance' (bool)  — direct wound marker
          'historical_trigger' (bool) — past-bound activation
          'wound_stage' (str)         — optional; overrides inferred stage
          'estimated_origin' (str)    — optional; caller-provided origin label

    Returns
    -------
    dict
        {
          'wound_present': bool,
          'stage': str,          # one of _WOUND_STAGES
          'estimated_origin': str,
        }
    """
    if not signal:
        return {"wound_present": False, "stage": "unacknowledged", "estimated_origin": "unknown"}

    wound_present = bool(signal.get("wound_resonance", False)) or \
                    bool(signal.get("historical_trigger", False))

    # Stage: caller may specify; otherwise infer from signal richness
    raw_stage = signal.get("wound_stage", "")
    stage = raw_stage if raw_stage in _WOUND_STAGES else (
        "metabolizing" if wound_present else "unacknowledged"
    )

    estimated_origin = str(signal.get("estimated_origin", "unknown"))

    return {
        "wound_present":    wound_present,
        "stage":            stage,
        "estimated_origin": estimated_origin,
    }


# ---------------------------------------------------------------------------
# Red Fire Classification
# ---------------------------------------------------------------------------

def classify_red_fire(signal: dict) -> str:
    """
    Three-way classification of the red fire quality.

    Parameters
    ----------
    signal : dict
        Expected discriminating keys:
          'features' (list[str]) — feature markers
          'reactive' (bool)      — direct override: reactive
          'completion' (bool)    — direct override: generative

    Returns
    -------
    str
        'generative' | 'protective' | 'reactive'
    """
    if not signal:
        return "reactive"

    # Direct overrides
    if signal.get("reactive"):
        return "reactive"
    if signal.get("completion") or signal.get("living_flame"):
        return "generative"

    features = set(str(f) for f in signal.get("features", []))

    if features & _PASSION_FEATURES:
        if features & {"boundary", "protective", "defense_clear"}:
            return "protective"
        return "generative"

    if features & _ANGER_FEATURES:
        if features & {"boundary", "protective", "defense_clear"}:
            return "protective"
        return "reactive"

    return "reactive"  # default


# ---------------------------------------------------------------------------
# Integration Level Assessment
# ---------------------------------------------------------------------------

def assess_integration_level(entity_id: str, history: list) -> float:
    """
    Score how integrated this entity's red is.

    0.0 = fully reactive / wound-driven
    1.0 = fully conscious deployment of the living flame

    Scoring algorithm:
      - Start at 0.5 (neutral baseline)
      - Each 'generative' or 'protective' signal in history: +0.05
      - Each 'reactive' signal in history:                   -0.05
      - Presence of 'integrated' wound stage in history:     +0.10 bonus
      - Bounded to [0.0, 1.0]

    Parameters
    ----------
    entity_id : str
        Identifier of the entity being assessed (used for logging; no DB lookup here).
    history : list[dict]
        List of prior signal dicts, each containing at least a 'classification' key
        from classify_red_fire(), and optionally a 'wound_stage' key.

    Returns
    -------
    float
        Integration score in [0.0, 1.0].
    """
    _ = entity_id  # reserved for future DB lookup
    if not history:
        return 0.5

    score = 0.5
    for entry in history:
        classification = str(entry.get("classification", ""))
        wound_stage    = str(entry.get("wound_stage", ""))

        if classification in ("generative", "protective"):
            score += 0.05
        elif classification == "reactive":
            score -= 0.05

        if wound_stage == "integrated":
            score += 0.10

    return round(max(0.0, min(1.0, score)), 4)


# ---------------------------------------------------------------------------
# Warrior Archetype Mapping
# ---------------------------------------------------------------------------

def map_warrior_archetype(signal: dict) -> str:
    """
    Map the red signal to a warrior archetype.

    Pre-routes to the Opacity layer's ares_athena_routing() — return
    values are deliberately aligned.

    'ares'   → blind force, no strategic context
    'athena' → purposeful, consequence-aware force

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
        'ares' or 'athena'
    """
    if not signal:
        return "ares"

    fire_type = classify_red_fire(signal)
    archetype = signal.get("archetype", "")

    if archetype == "athena":
        return "athena"
    if archetype == "ares":
        return "ares"

    if fire_type in ("generative", "protective"):
        return "athena"
    return "ares"
