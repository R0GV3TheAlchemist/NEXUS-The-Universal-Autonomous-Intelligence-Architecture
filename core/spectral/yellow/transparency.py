"""
YELLOW transparency layer — open-field signals.
Domain: will, solar plexus activation, ego boundary, personal power.
"""

from .constants import (
    SENTINEL_LEVELS, UI_STATE, SOLAR_ARCHETYPES,
    WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE
)


def detect_solar_state(signal: dict) -> dict:
    will_strength = signal.get("will_strength", 0.5)
    ego_clarity = signal.get("ego_clarity", 0.5)
    shame_index = signal.get("shame_index", 0.0)

    if will_strength >= 0.85 and ego_clarity >= 0.8:
        phase = "sovereign_activation"
        archetype = "sovereign"
    elif shame_index >= 0.7:
        phase = "shame_collapse"
        archetype = "doormat"
    elif will_strength >= 0.8 and ego_clarity < 0.4:
        phase = "ego_inflation"
        archetype = "tyrant"
    elif will_strength >= 0.6:
        phase = "will_assertion"
        archetype = "warrior_of_will"
    else:
        phase = "latent_solar"
        archetype = "radiant_self"

    return {
        "color": "YELLOW",
        "phase": phase,
        "archetype": archetype,
        "alchemical_stage": ALCHEMICAL_PHASE,
        "stage_index": STAGE,
        "will_strength": will_strength,
    }


def emit_solar_alert(level_key: str, context: dict = None) -> dict:
    level = SENTINEL_LEVELS.get(level_key, 1)
    return {
        "color": "YELLOW",
        "alert": level_key,
        "severity": level,
        "context": context or {},
        "band": WAVELENGTH_RANGE,
        "interrupt_flag": False,
    }


def classify_will_urgency(signal: dict) -> str:
    will_strength = signal.get("will_strength", 0.5)
    shame_index = signal.get("shame_index", 0.0)
    collapse_flag = signal.get("collapse_flag", False)

    if collapse_flag or shame_index >= 0.85:
        return "critical"
    if will_strength < 0.2:
        return "high"
    if will_strength < 0.5:
        return "moderate"
    return "low"


def get_ui_state(phase: str) -> str:
    return UI_STATE.get(phase, UI_STATE["idle"])


def is_separation_signal(signal: dict) -> bool:
    return signal.get("separation_flag", False) or signal.get("ego_clarity", 0.5) >= 0.75
