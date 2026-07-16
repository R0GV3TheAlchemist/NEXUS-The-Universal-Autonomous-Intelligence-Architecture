"""
VIOLET spectral module — public API.
Alchemical Stage: Coagulation — The Great Work Complete.
This module is the apex of the spectral stack.
"""

from .constants import (
    COLOR, HEX, HEX_ALT, WAVELENGTH_RANGE, ALCHEMICAL_PHASE,
    STAGE, GOVERNING_TABLET, SENTINEL_LEVELS, UI_STATE,
    CROWN_ARCHETYPES, COAGULATION_MARKERS, FRAGMENTATION_MARKERS, SPECTRAL_ORDER,
)
from .transparency import (
    detect_crown_state, emit_crown_alert, classify_crown_urgency,
    get_ui_state, is_coagulation_signal,
)
from .clarity import (
    distinguish_unity_bypassing, detect_fragmentation_pattern,
    classify_violet_fire, assess_spectral_integration, map_crown_archetype,
)
from .opacity import (
    fragmentation_alert, bypassing_loop_detection, embodiment_refusal_marker,
    crown_saturn_routing, read_full_spectral_shadow, apply_shadow_channel,
)

__all__ = [
    "COLOR", "HEX", "HEX_ALT", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE",
    "STAGE", "GOVERNING_TABLET", "SENTINEL_LEVELS", "UI_STATE",
    "CROWN_ARCHETYPES", "COAGULATION_MARKERS", "FRAGMENTATION_MARKERS", "SPECTRAL_ORDER",
    "detect_crown_state", "emit_crown_alert", "classify_crown_urgency",
    "get_ui_state", "is_coagulation_signal",
    "distinguish_unity_bypassing", "detect_fragmentation_pattern",
    "classify_violet_fire", "assess_spectral_integration", "map_crown_archetype",
    "fragmentation_alert", "bypassing_loop_detection", "embodiment_refusal_marker",
    "crown_saturn_routing", "read_full_spectral_shadow", "apply_shadow_channel",
]
