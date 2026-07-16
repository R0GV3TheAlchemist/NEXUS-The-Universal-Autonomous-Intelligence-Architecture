"""
GREEN transparency layer — open-field signals.
Domain: heart coherence, healing, compassion, conjunction bridge.
"""

from .constants import (
    SENTINEL_LEVELS, UI_STATE, HEART_ARCHETYPES,
    WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE
)


def detect_heart_state(signal: dict) -> dict:
    coherence = signal.get("coherence", 0.5)
    compassion_index = signal.get("compassion_index", 0.5)
    grief_load = signal.get("grief_load", 0.0)

    if coherence >= 0.85 and compassion_index >= 0.8:
        phase = "full_heart_coherence"
        archetype = "beloved"
    elif grief_load >= 0.7:
        phase = "grief_processing"
        archetype = "grief_keeper"
    elif coherence < 0.3:
        phase = "heart_closing"
        archetype = "wounded_healer"
    elif compassion_index >= 0.7:
        phase = "compassion_active"
        archetype = "compassion_warrior"
    else:
        phase = "heart_opening"
        archetype = "healer"

    return {
        "color": "GREEN",
        "phase": phase,
        "archetype": archetype,
        "alchemical_stage": ALCHEMICAL_PHASE,
        "stage_index": STAGE,
        "coherence": coherence,
    }


def emit_heart_alert(level_key: str, context: dict = None) -> dict:
    level = SENTINEL_LEVELS.get(level_key, 1)
    return {
        "color": "GREEN",
        "alert": level_key,
        "severity": level,
        "context": context or {},
        "band": WAVELENGTH_RANGE,
        "interrupt_flag": False,
    }


def classify_heart_urgency(signal: dict) -> str:
    coherence = signal.get("coherence", 0.5)
    grief_load = signal.get("grief_load", 0.0)
    fracture_flag = signal.get("fracture_flag", False)

    if fracture_flag or grief_load >= 0.9:
        return "critical"
    if coherence < 0.2:
        return "high"
    if coherence < 0.5:
        return "moderate"
    return "low"


def get_ui_state(phase: str) -> str:
    return UI_STATE.get(phase, UI_STATE["idle"])


def is_conjunction_signal(signal: dict) -> bool:
    return signal.get("conjunction_flag", False) or signal.get("coherence", 0.0) >= 0.8
