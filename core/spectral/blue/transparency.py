"""
BLUE transparency layer — open-field signals.
Domain: truth expression, throat activation, perception clarity, fermentation.
"""

from .constants import (
    SENTINEL_LEVELS, UI_STATE, THROAT_ARCHETYPES,
    WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE
)


def detect_throat_state(signal: dict) -> dict:
    truth_index = signal.get("truth_index", 0.5)
    expression_rate = signal.get("expression_rate", 0.5)
    silence_score = signal.get("silence_score", 0.0)

    if truth_index >= 0.85 and expression_rate >= 0.8:
        phase = "sovereign_voice"
        archetype = "truth_speaker"
    elif silence_score >= 0.7:
        phase = "voice_suppressed"
        archetype = "silenced_one"
    elif truth_index >= 0.7 and expression_rate < 0.4:
        phase = "truth_withheld"
        archetype = "prophet"
    elif expression_rate >= 0.7:
        phase = "active_expression"
        archetype = "channel"
    else:
        phase = "fermentation_forming"
        archetype = "visionary"

    return {
        "color": "BLUE",
        "phase": phase,
        "archetype": archetype,
        "alchemical_stage": ALCHEMICAL_PHASE,
        "stage_index": STAGE,
        "truth_index": truth_index,
    }


def emit_throat_alert(level_key: str, context: dict = None) -> dict:
    level = SENTINEL_LEVELS.get(level_key, 1)
    return {
        "color": "BLUE",
        "alert": level_key,
        "severity": level,
        "context": context or {},
        "band": WAVELENGTH_RANGE,
        "interrupt_flag": False,
    }


def classify_expression_urgency(signal: dict) -> str:
    expression_rate = signal.get("expression_rate", 0.5)
    silence_score = signal.get("silence_score", 0.0)
    fracture_flag = signal.get("fracture_flag", False)

    if fracture_flag or silence_score >= 0.9:
        return "critical"
    if expression_rate < 0.2:
        return "high"
    if expression_rate < 0.5:
        return "moderate"
    return "low"


def get_ui_state(phase: str) -> str:
    return UI_STATE.get(phase, UI_STATE["idle"])


def is_fermentation_signal(signal: dict) -> bool:
    return signal.get("fermentation_flag", False) or signal.get("truth_index", 0.0) >= 0.8
