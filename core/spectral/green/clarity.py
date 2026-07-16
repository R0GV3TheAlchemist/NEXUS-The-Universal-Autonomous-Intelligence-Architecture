"""
GREEN clarity layer — depth-readable signals.
Domain: distinguishing genuine compassion from codependency,
grief processing, heart armoring, conjunction bridge health.
"""

from .constants import HEART_ARCHETYPES, CONJUNCTION_MARKERS, GRIEF_MARKERS


def distinguish_compassion_codependency(signal: dict) -> str:
    compassion_index = signal.get("compassion_index", 0.5)
    boundary_score = signal.get("boundary_score", 0.5)
    self_sacrifice = signal.get("self_sacrifice", 0.0)

    if self_sacrifice > 0.75 and boundary_score < 0.3:
        return "codependency"
    if compassion_index > 0.7 and boundary_score > 0.6:
        return "healthy_compassion"
    if self_sacrifice > 0.5:
        return "self_dissolving"
    return "integrated"


def detect_grief_pattern(signal: dict) -> dict:
    markers = signal.get("grief_markers", [])
    active = [m for m in markers if m in GRIEF_MARKERS]
    depth = signal.get("grief_depth", 0.0)
    return {
        "grief_present": len(active) > 0 or depth > 0.4,
        "active_markers": active,
        "depth": depth,
        "intervention_suggested": depth > 0.65,
    }


def classify_green_fire(signal: dict) -> str:
    conjunction_flag = signal.get("conjunction_flag", False)
    grief_depth = signal.get("grief_depth", 0.0)
    compassion_index = signal.get("compassion_index", 0.5)

    if conjunction_flag:
        return "conjunction"
    if grief_depth > 0.6:
        return "grief_immersion"
    if compassion_index >= 0.8:
        return "heart_ignition"
    return "neutral"


def assess_bridge_health(signal: dict) -> dict:
    """Assesses the lower/upper chakra bridge (the conjunction bridge)."""
    coherence = signal.get("coherence", 0.5)
    bridge_stability = signal.get("bridge_stability", 0.5)
    grief_load = signal.get("grief_load", 0.0)

    if coherence > 0.75 and bridge_stability > 0.7:
        status = "stable"
    elif grief_load > 0.65:
        status = "grief_burdened"
    elif bridge_stability < 0.3:
        status = "fractured"
    else:
        status = "forming"

    return {"status": status, "coherence": coherence, "bridge_stability": bridge_stability}


def map_heart_archetype(signal: dict) -> str:
    compassion_index = signal.get("compassion_index", 0.5)
    grief_load = signal.get("grief_load", 0.0)
    self_sacrifice = signal.get("self_sacrifice", 0.0)
    coherence = signal.get("coherence", 0.5)

    if coherence >= 0.85 and compassion_index >= 0.8:
        return "beloved"
    if grief_load >= 0.7:
        return "grief_keeper"
    if self_sacrifice >= 0.7:
        return "wounded_healer"
    if compassion_index >= 0.7:
        return "compassion_warrior"
    return "healer"
