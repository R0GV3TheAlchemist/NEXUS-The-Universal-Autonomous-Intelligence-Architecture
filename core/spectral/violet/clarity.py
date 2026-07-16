"""
VIOLET clarity layer — depth-readable signals.
Domain: distinguishing genuine unity from spiritual bypassing,
embodied transcendence vs. dissociation, crown integration across full spectral stack.
"""

from .constants import CROWN_ARCHETYPES, COAGULATION_MARKERS, FRAGMENTATION_MARKERS, SPECTRAL_ORDER


def distinguish_unity_bypassing(signal: dict) -> str:
    unity_index = signal.get("unity_index", 0.5)
    embodiment_score = signal.get("embodiment_score", 0.5)
    bypass_flag = signal.get("bypass_flag", False)

    if bypass_flag or (unity_index > 0.8 and embodiment_score < 0.3):
        return "spiritual_bypassing"
    if unity_index > 0.8 and embodiment_score > 0.7:
        return "embodied_unity"
    if unity_index > 0.6 and embodiment_score > 0.5:
        return "integrating"
    return "approaching_unity"


def detect_fragmentation_pattern(signal: dict) -> dict:
    markers = signal.get("fragmentation_markers", [])
    active = [m for m in markers if m in FRAGMENTATION_MARKERS]
    depth = signal.get("fragmentation_depth", 0.0)
    return {
        "fragmentation_present": len(active) > 0 or depth > 0.4,
        "active_markers": active,
        "depth": depth,
        "intervention_suggested": depth > 0.65,
    }


def classify_violet_fire(signal: dict) -> str:
    coagulation_flag = signal.get("coagulation_flag", False)
    bypass_flag = signal.get("bypass_flag", False)
    unity_index = signal.get("unity_index", 0.5)

    if bypass_flag:
        return "bypassing"
    if coagulation_flag:
        return "coagulation"
    if unity_index >= 0.85:
        return "great_work_ignition"
    return "neutral"


def assess_spectral_integration(signal: dict) -> dict:
    """
    Assesses how fully the entity has integrated all 7 spectral stages.
    VIOLET is the only module that assesses the full stack.
    """
    stage_scores = signal.get("stage_scores", {})
    completed = [s for s in SPECTRAL_ORDER if stage_scores.get(s, 0.0) >= 0.7]
    integration_ratio = len(completed) / len(SPECTRAL_ORDER)

    return {
        "completed_stages": completed,
        "total_stages": len(SPECTRAL_ORDER),
        "integration_ratio": round(integration_ratio, 3),
        "great_work_ready": integration_ratio >= 1.0,
    }


def map_crown_archetype(signal: dict) -> str:
    unity_index = signal.get("unity_index", 0.5)
    embodiment_score = signal.get("embodiment_score", 0.5)
    bypass_flag = signal.get("bypass_flag", False)

    if bypass_flag:
        return "false_ascendant"
    if unity_index >= 0.9 and embodiment_score >= 0.85:
        return "the_whole"
    if unity_index >= 0.8 and embodiment_score < 0.4:
        return "cosmic_orphan"
    if unity_index >= 0.7:
        return "bodhisattva"
    return "alchemist"
