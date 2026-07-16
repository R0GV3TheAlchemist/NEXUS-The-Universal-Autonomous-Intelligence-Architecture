"""
ORANGE clarity layer — depth-readable signals.
Domain: distinguishing healthy creativity from compulsion,
sacral wounding, pleasure/guilt splits.
"""

from .constants import SACRAL_ARCHETYPES, CALCINATION_MARKERS, DISSOLUTION_MARKERS


def distinguish_pleasure_compulsion(signal: dict) -> str:
    """
    Distinguishes healthy pleasure-seeking from compulsive patterns.
    Returns: 'healthy_pleasure' | 'compulsive_seeking' | 'guilt_suppression' | 'integrated'
    """
    pleasure_score = signal.get("pleasure_score", 0.5)
    guilt_index = signal.get("guilt_index", 0.0)
    repetition_rate = signal.get("repetition_rate", 0.0)

    if guilt_index > 0.7 and pleasure_score < 0.4:
        return "guilt_suppression"
    if repetition_rate > 0.8 and guilt_index > 0.5:
        return "compulsive_seeking"
    if pleasure_score > 0.7 and guilt_index < 0.3:
        return "healthy_pleasure"
    return "integrated"


def detect_sacral_wound(signal: dict) -> dict:
    """
    Detects presence and depth of sacral wound patterns.
    Returns wound descriptor dict.
    """
    wound_markers = signal.get("wound_markers", [])
    depth = signal.get("wound_depth", 0.0)

    active_dissolution = [m for m in wound_markers if m in DISSOLUTION_MARKERS]
    wound_present = len(active_dissolution) > 0 or depth > 0.4

    return {
        "wound_present": wound_present,
        "active_markers": active_dissolution,
        "depth": depth,
        "intervention_suggested": depth > 0.65,
    }


def classify_orange_fire(signal: dict) -> str:
    """
    Classifies the nature of the orange fire signal.
    Returns: 'calcination' | 'dissolution' | 'creative_ignition' | 'neutral'
    """
    calcination_flag = signal.get("calcination_flag", False)
    dissolution_flag = signal.get("dissolution_flag", False)
    creativity_index = signal.get("creativity_index", 0.0)

    if calcination_flag:
        return "calcination"
    if dissolution_flag:
        return "dissolution"
    if creativity_index >= 0.7:
        return "creative_ignition"
    return "neutral"


def assess_boundary_health(signal: dict) -> dict:
    """
    Assesses the health of personal boundaries.
    Returns structured boundary health report.
    """
    boundary_score = signal.get("boundary_score", 0.5)
    permeability = signal.get("permeability", 0.5)
    enforcement_rate = signal.get("enforcement_rate", 0.5)

    if boundary_score > 0.75 and enforcement_rate > 0.7:
        status = "healthy"
    elif boundary_score < 0.3 or permeability > 0.8:
        status = "compromised"
    elif enforcement_rate < 0.3:
        status = "inconsistent"
    else:
        status = "developing"

    return {
        "status": status,
        "boundary_score": boundary_score,
        "permeability": permeability,
        "enforcement_rate": enforcement_rate,
    }


def map_creative_archetype(signal: dict) -> str:
    """
    Maps signal to a ORANGE sacral archetype.
    Returns one of SACRAL_ARCHETYPES.
    """
    intensity = signal.get("intensity", 0.0)
    guilt_index = signal.get("guilt_index", 0.0)
    creativity_index = signal.get("creativity_index", 0.0)

    if creativity_index >= 0.8 and guilt_index < 0.2:
        return "creator"
    if guilt_index >= 0.7:
        return "martyr"
    if intensity >= 0.7 and creativity_index >= 0.6:
        return "sovereign_of_pleasure"
    if intensity < 0.3:
        return "wounded_child"
    return "lover"
