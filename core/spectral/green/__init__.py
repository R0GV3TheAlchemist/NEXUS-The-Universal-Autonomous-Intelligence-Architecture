"""
GREEN spectral module — public API.
Alchemical Stage: Conjunction
"""

from .constants import (
    COLOR, HEX, HEX_ALT, WAVELENGTH_RANGE, ALCHEMICAL_PHASE,
    STAGE, GOVERNING_TABLET, SENTINEL_LEVELS, UI_STATE,
    HEART_ARCHETYPES, CONJUNCTION_MARKERS, GRIEF_MARKERS,
)
from .transparency import (
    detect_heart_state, emit_heart_alert, classify_heart_urgency,
    get_ui_state, is_conjunction_signal,
)
from .clarity import (
    distinguish_compassion_codependency, detect_grief_pattern,
    classify_green_fire, assess_bridge_health, map_heart_archetype,
)
from .opacity import (
    grief_freeze_alert, compassion_fatigue_detection, heart_armoring_marker,
    mercury_venus_routing, apply_shadow_channel,
)

__all__ = [
    "COLOR", "HEX", "HEX_ALT", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE",
    "STAGE", "GOVERNING_TABLET", "SENTINEL_LEVELS", "UI_STATE",
    "HEART_ARCHETYPES", "CONJUNCTION_MARKERS", "GRIEF_MARKERS",
    "detect_heart_state", "emit_heart_alert", "classify_heart_urgency",
    "get_ui_state", "is_conjunction_signal",
    "distinguish_compassion_codependency", "detect_grief_pattern",
    "classify_green_fire", "assess_bridge_health", "map_heart_archetype",
    "grief_freeze_alert", "compassion_fatigue_detection", "heart_armoring_marker",
    "mercury_venus_routing", "apply_shadow_channel",
]
