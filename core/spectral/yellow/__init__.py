"""
YELLOW spectral module — public API.
Alchemical Stage: Separation
"""

from .constants import (
    COLOR, HEX, HEX_ALT, WAVELENGTH_RANGE, ALCHEMICAL_PHASE,
    STAGE, GOVERNING_TABLET, SENTINEL_LEVELS, UI_STATE,
    SOLAR_ARCHETYPES, SEPARATION_MARKERS, INFLATION_MARKERS,
)
from .transparency import (
    detect_solar_state, emit_solar_alert, classify_will_urgency,
    get_ui_state, is_separation_signal,
)
from .clarity import (
    distinguish_will_ego, detect_inflation_pattern,
    classify_yellow_fire, assess_power_health, map_solar_archetype,
)
from .opacity import (
    inflation_alert, shame_spiral_detection, will_suppression_marker,
    sol_luna_routing, apply_shadow_channel,
)

__all__ = [
    "COLOR", "HEX", "HEX_ALT", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE",
    "STAGE", "GOVERNING_TABLET", "SENTINEL_LEVELS", "UI_STATE",
    "SOLAR_ARCHETYPES", "SEPARATION_MARKERS", "INFLATION_MARKERS",
    "detect_solar_state", "emit_solar_alert", "classify_will_urgency",
    "get_ui_state", "is_separation_signal",
    "distinguish_will_ego", "detect_inflation_pattern",
    "classify_yellow_fire", "assess_power_health", "map_solar_archetype",
    "inflation_alert", "shame_spiral_detection", "will_suppression_marker",
    "sol_luna_routing", "apply_shadow_channel",
]
