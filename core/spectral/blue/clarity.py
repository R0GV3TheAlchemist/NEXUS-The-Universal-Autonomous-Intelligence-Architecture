"""
BLUE clarity layer — depth-readable signals.
Domain: truth vs. deception, expression blocks, perception upgrades,
fermentation process health.
"""

from .constants import THROAT_ARCHETYPES, FERMENTATION_MARKERS, SILENCE_MARKERS


def distinguish_truth_deception(signal: dict) -> str:
    truth_index = signal.get("truth_index", 0.5)
    distortion_index = signal.get("distortion_index", 0.0)
    self_deception = signal.get("self_deception", 0.0)

    if self_deception > 0.7:
        return "self_deception"
    if distortion_index > 0.65:
        return "active_distortion"
    if truth_index > 0.75 and distortion_index < 0.2:
        return "clear_truth"
    return "partial_clarity"


def detect_silence_pattern(signal: dict) -> dict:
    markers = signal.get("silence_markers", [])
    active = [m for m in markers if m in SILENCE_MARKERS]
    depth = signal.get("silence_depth", 0.0)
    return {
        "silence_present": len(active) > 0 or depth > 0.4,
        "active_markers": active,
        "depth": depth,
        "intervention_suggested": depth > 0.65,
    }


def classify_blue_fire(signal: dict) -> str:
    fermentation_flag = signal.get("fermentation_flag", False)
    silence_depth = signal.get("silence_depth", 0.0)
    truth_index = signal.get("truth_index", 0.5)

    if fermentation_flag:
        return "fermentation"
    if silence_depth > 0.6:
        return "silence_immersion"
    if truth_index >= 0.8:
        return "truth_ignition"
    return "neutral"


def assess_perception_health(signal: dict) -> dict:
    clarity_score = signal.get("clarity_score", 0.5)
    distortion_index = signal.get("distortion_index", 0.0)
    perception_fog = signal.get("perception_fog", 0.0)

    if clarity_score > 0.75 and distortion_index < 0.3:
        status = "clear"
    elif perception_fog > 0.65:
        status = "fogged"
    elif distortion_index > 0.65:
        status = "distorted"
    else:
        status = "clearing"

    return {"status": status, "clarity_score": clarity_score, "distortion_index": distortion_index}


def map_throat_archetype(signal: dict) -> str:
    truth_index = signal.get("truth_index", 0.5)
    expression_rate = signal.get("expression_rate", 0.5)
    silence_score = signal.get("silence_score", 0.0)

    if truth_index >= 0.85 and expression_rate >= 0.8:
        return "truth_speaker"
    if silence_score >= 0.7:
        return "silenced_one"
    if truth_index >= 0.7:
        return "prophet"
    if expression_rate >= 0.7:
        return "channel"
    return "visionary"
