"""
BLUE spectral module — public API.
Alchemical Stage: Fermentation
"""

from .constants import (
    COLOR, HEX, HEX_ALT, WAVELENGTH_RANGE, ALCHEMICAL_PHASE,
    STAGE, GOVERNING_TABLET, SENTINEL_LEVELS, UI_STATE,
    THROAT_ARCHETYPES, FERMENTATION_MARKERS, SILENCE_MARKERS,
)
from .transparency import (
    detect_throat_state, emit_throat_alert, classify_expression_urgency,
    get_ui_state, is_fermentation_signal,
)
from .clarity import (
    distinguish_truth_deception, detect_silence_pattern,
    classify_blue_fire, assess_perception_health, map_throat_archetype,
)
from .opacity import (
    silence_alert, distortion_loop_detection, perception_fog_marker,
    jupiter_mercury_routing, apply_shadow_channel,
)

__all__ = [
    "COLOR", "HEX", "HEX_ALT", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE",
    "STAGE", "GOVERNING_TABLET", "SENTINEL_LEVELS", "UI_STATE",
    "THROAT_ARCHETYPES", "FERMENTATION_MARKERS", "SILENCE_MARKERS",
    "detect_throat_state", "emit_throat_alert", "classify_expression_urgency",
    "get_ui_state", "is_fermentation_signal",
    "distinguish_truth_deception", "detect_silence_pattern",
    "classify_blue_fire", "assess_perception_health", "map_throat_archetype",
    "silence_alert", "distortion_loop_detection", "perception_fog_marker",
    "jupiter_mercury_routing", "apply_shadow_channel",
]
