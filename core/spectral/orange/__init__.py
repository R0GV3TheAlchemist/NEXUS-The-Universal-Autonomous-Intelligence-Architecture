"""
ORANGE spectral module — public API.
Alchemical Stage: Calcination / Dissolution
"""

from .constants import (
    COLOR, HEX, HEX_ALT, WAVELENGTH_RANGE, ALCHEMICAL_PHASE,
    STAGE, GOVERNING_TABLET, SENTINEL_LEVELS, UI_STATE,
    SACRAL_ARCHETYPES, DISSOLUTION_MARKERS, CALCINATION_MARKERS,
)
from .transparency import (
    detect_sacral_state, emit_sacral_alert, classify_creative_urgency,
    get_ui_state, is_dissolution_signal,
)
from .clarity import (
    distinguish_pleasure_compulsion, detect_sacral_wound,
    classify_orange_fire, assess_boundary_health, map_creative_archetype,
)
from .opacity import (
    calcination_alert, martyrdom_loop_detection, sacral_depletion_marker,
    venus_aphrodite_routing, apply_shadow_channel,
)

__all__ = [
    "COLOR", "HEX", "HEX_ALT", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE",
    "STAGE", "GOVERNING_TABLET", "SENTINEL_LEVELS", "UI_STATE",
    "SACRAL_ARCHETYPES", "DISSOLUTION_MARKERS", "CALCINATION_MARKERS",
    "detect_sacral_state", "emit_sacral_alert", "classify_creative_urgency",
    "get_ui_state", "is_dissolution_signal",
    "distinguish_pleasure_compulsion", "detect_sacral_wound",
    "classify_orange_fire", "assess_boundary_health", "map_creative_archetype",
    "calcination_alert", "martyrdom_loop_detection", "sacral_depletion_marker",
    "venus_aphrodite_routing", "apply_shadow_channel",
]
