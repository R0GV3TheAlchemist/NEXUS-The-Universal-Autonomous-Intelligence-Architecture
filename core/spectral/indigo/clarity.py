"""
INDIGO clarity layer — depth-readable signals.
Domain: intuition vs. delusion, psychic overload, field perception health,
distillation process integrity.
"""

from .constants import INTUITION_ARCHETYPES, DISTILLATION_MARKERS, BLOCK_MARKERS


def distinguish_intuition_delusion(signal: dict) -> str:
    intuition_index = signal.get("intuition_index", 0.5)
    reality_anchor = signal.get("reality_anchor", 0.5)
    delusion_index = signal.get("delusion_index", 0.0)

    if delusion_index > 0.7:
        return "active_delusion"
    if intuition_index > 0.75 and reality_anchor > 0.6:
        return "grounded_intuition"
    if intuition_index > 0.7 and reality_anchor < 0.3:
        return "ungrounded_perception"
    return "developing_sight"


def detect_block_pattern(signal: dict) -> dict:
    markers = signal.get("block_markers", [])
    active = [m for m in markers if m in BLOCK_MARKERS]
    depth = signal.get("block_depth", 0.0)
    return {
        "block_present": len(active) > 0 or depth > 0.4,
        "active_markers": active,
        "depth": depth,
        "intervention_suggested": depth > 0.65,
    }


def classify_indigo_fire(signal: dict) -> str:
    distillation_flag = signal.get("distillation_flag", False)
    block_depth = signal.get("block_depth", 0.0)
    intuition_index = signal.get("intuition_index", 0.5)

    if distillation_flag:
        return "distillation"
    if block_depth > 0.6:
        return "block_immersion"
    if intuition_index >= 0.8:
        return "third_eye_ignition"
    return "neutral"


def assess_field_perception_health(signal: dict) -> dict:
    field_perception = signal.get("field_perception", 0.5)
    reality_anchor = signal.get("reality_anchor", 0.5)
    psychic_load = signal.get("psychic_load", 0.0)

    if field_perception > 0.75 and reality_anchor > 0.65:
        status = "calibrated"
    elif psychic_load > 0.75:
        status = "overloaded"
    elif reality_anchor < 0.3:
        status = "ungrounded"
    else:
        status = "developing"

    return {"status": status, "field_perception": field_perception, "reality_anchor": reality_anchor}


def map_intuition_archetype(signal: dict) -> str:
    intuition_index = signal.get("intuition_index", 0.5)
    field_perception = signal.get("field_perception", 0.5)
    rational_override = signal.get("rational_override", 0.0)
    reality_anchor = signal.get("reality_anchor", 0.5)

    if intuition_index >= 0.85 and field_perception >= 0.8:
        return "oracle"
    if rational_override >= 0.7:
        return "blind_mystic"
    if intuition_index >= 0.7 and reality_anchor < 0.4:
        return "psychic_warrior"
    if field_perception >= 0.6:
        return "distiller"
    return "seer"
