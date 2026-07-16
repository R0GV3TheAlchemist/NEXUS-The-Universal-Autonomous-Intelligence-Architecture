"""
INDIGO transparency layer — open-field signals.
Domain: intuition, third eye activation, deep field perception, distillation.
"""

from .constants import (
    SENTINEL_LEVELS, UI_STATE, INTUITION_ARCHETYPES,
    WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE
)


def detect_third_eye_state(signal: dict) -> dict:
    intuition_index = signal.get("intuition_index", 0.5)
    field_perception = signal.get("field_perception", 0.5)
    rational_override = signal.get("rational_override", 0.0)

    if intuition_index >= 0.85 and field_perception >= 0.8:
        phase = "oracle_activation"
        archetype = "oracle"
    elif rational_override >= 0.8:
        phase = "third_eye_blocked"
        archetype = "blind_mystic"
    elif intuition_index >= 0.7:
        phase = "active_perception"
        archetype = "seer"
    elif field_perception >= 0.6:
        phase = "field_reading"
        archetype = "distiller"
    else:
        phase = "latent_intuition"
        archetype = "psychic_warrior"

    return {
        "color": "INDIGO",
        "phase": phase,
        "archetype": archetype,
        "alchemical_stage": ALCHEMICAL_PHASE,
        "stage_index": STAGE,
        "intuition_index": intuition_index,
    }


def emit_indigo_alert(level_key: str, context: dict = None) -> dict:
    level = SENTINEL_LEVELS.get(level_key, 1)
    return {
        "color": "INDIGO",
        "alert": level_key,
        "severity": level,
        "context": context or {},
        "band": WAVELENGTH_RANGE,
        "interrupt_flag": False,
    }


def classify_intuition_urgency(signal: dict) -> str:
    intuition_index = signal.get("intuition_index", 0.5)
    rational_override = signal.get("rational_override", 0.0)
    fracture_flag = signal.get("fracture_flag", False)

    if fracture_flag or rational_override >= 0.9:
        return "critical"
    if intuition_index < 0.2:
        return "high"
    if intuition_index < 0.5:
        return "moderate"
    return "low"


def get_ui_state(phase: str) -> str:
    return UI_STATE.get(phase, UI_STATE["idle"])


def is_distillation_signal(signal: dict) -> bool:
    return signal.get("distillation_flag", False) or signal.get("intuition_index", 0.0) >= 0.8
