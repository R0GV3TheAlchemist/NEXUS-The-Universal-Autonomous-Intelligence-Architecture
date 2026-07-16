"""
VIOLET transparency layer — open-field signals.
Domain: crown activation, unity field, coagulation, completion of the Great Work.
"""

from .constants import (
    SENTINEL_LEVELS, UI_STATE, CROWN_ARCHETYPES,
    WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE, SPECTRAL_ORDER
)


def detect_crown_state(signal: dict) -> dict:
    unity_index = signal.get("unity_index", 0.5)
    embodiment_score = signal.get("embodiment_score", 0.5)
    bypass_flag = signal.get("bypass_flag", False)

    if bypass_flag:
        phase = "spiritual_bypassing"
        archetype = "false_ascendant"
    elif unity_index >= 0.9 and embodiment_score >= 0.85:
        phase = "great_work_completion"
        archetype = "the_whole"
    elif unity_index >= 0.8 and embodiment_score < 0.4:
        phase = "ungrounded_transcendence"
        archetype = "cosmic_orphan"
    elif unity_index >= 0.7:
        phase = "crown_activation"
        archetype = "bodhisattva"
    else:
        phase = "coagulation_forming"
        archetype = "alchemist"

    return {
        "color": "VIOLET",
        "phase": phase,
        "archetype": archetype,
        "alchemical_stage": ALCHEMICAL_PHASE,
        "stage_index": STAGE,
        "unity_index": unity_index,
        "spectral_stack_complete": len(SPECTRAL_ORDER),
    }


def emit_crown_alert(level_key: str, context: dict = None) -> dict:
    level = SENTINEL_LEVELS.get(level_key, 1)
    return {
        "color": "VIOLET",
        "alert": level_key,
        "severity": level,
        "context": context or {},
        "band": WAVELENGTH_RANGE,
        "interrupt_flag": False,
    }


def classify_crown_urgency(signal: dict) -> str:
    unity_index = signal.get("unity_index", 0.5)
    bypass_flag = signal.get("bypass_flag", False)
    collapse_flag = signal.get("collapse_flag", False)

    if collapse_flag or bypass_flag:
        return "critical"
    if unity_index < 0.2:
        return "high"
    if unity_index < 0.5:
        return "moderate"
    return "low"


def get_ui_state(phase: str) -> str:
    return UI_STATE.get(phase, UI_STATE["idle"])


def is_coagulation_signal(signal: dict) -> bool:
    return signal.get("coagulation_flag", False) or signal.get("unity_index", 0.0) >= 0.85
