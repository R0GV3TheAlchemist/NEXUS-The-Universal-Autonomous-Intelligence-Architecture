"""
ORANGE transparency layer — open-field, publicly readable signals.
Domain: creative vitality, sacral energy, boundary awareness.
"""

from .constants import (
    SENTINEL_LEVELS, UI_STATE, SACRAL_ARCHETYPES,
    WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE
)


def detect_sacral_state(signal: dict) -> dict:
    """
    Detect the active sacral/creative energetic state from a signal dict.
    Returns a state descriptor with phase, intensity, and archetype hint.
    """
    intensity = signal.get("intensity", 0.0)
    creativity_index = signal.get("creativity_index", 0.0)
    boundary_score = signal.get("boundary_score", 1.0)

    if intensity >= 0.9 and creativity_index >= 0.8:
        phase = "peak_creative_flow"
        archetype = "creator"
    elif boundary_score < 0.3:
        phase = "boundary_dissolution"
        archetype = "martyr"
    elif intensity < 0.2:
        phase = "creative_block"
        archetype = "wounded_child"
    elif intensity >= 0.6:
        phase = "active_creation"
        archetype = "sovereign_of_pleasure"
    else:
        phase = "latent_creative"
        archetype = "lover"

    return {
        "color": "ORANGE",
        "phase": phase,
        "archetype": archetype,
        "alchemical_stage": ALCHEMICAL_PHASE,
        "stage_index": STAGE,
        "intensity": intensity,
    }


def emit_sacral_alert(level_key: str, context: dict = None) -> dict:
    """
    Emit a structured sentinel alert for the ORANGE band.
    level_key must be a key in SENTINEL_LEVELS.
    """
    level = SENTINEL_LEVELS.get(level_key, 1)
    return {
        "color": "ORANGE",
        "alert": level_key,
        "severity": level,
        "context": context or {},
        "band": WAVELENGTH_RANGE,
        "interrupt_flag": False,
    }


def classify_creative_urgency(signal: dict) -> str:
    """
    Returns urgency string: 'low' | 'moderate' | 'high' | 'critical'
    based on combined creative and boundary signals.
    """
    intensity = signal.get("intensity", 0.0)
    boundary_score = signal.get("boundary_score", 1.0)
    block_flag = signal.get("block_flag", False)

    if block_flag or boundary_score < 0.2:
        return "critical"
    if intensity >= 0.8:
        return "high"
    if intensity >= 0.5:
        return "moderate"
    return "low"


def get_ui_state(phase: str) -> str:
    """
    Returns the hex color for a given UI phase key.
    Defaults to 'idle' if phase not found.
    """
    return UI_STATE.get(phase, UI_STATE["idle"])


def is_dissolution_signal(signal: dict) -> bool:
    """
    Returns True if the signal carries dissolution characteristics.
    """
    return signal.get("boundary_score", 1.0) < 0.35 or signal.get("dissolution_flag", False)
