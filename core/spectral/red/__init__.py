"""
core/spectral/red
=================
RED — Rubedo (Stage IV of the Magnum Opus)
Governing Tablet: Ruby Tablet
Wavelength: 620–750 nm
Shadow Doctrine: The wound beneath the warrior; the fire that knows why it burns.

Three-layer architecture:
  transparency  → the open-field red signals
  clarity       → the depth-readable red signals
  opacity       → the shadow-channel red signals (passive, appended, never blocking)
"""

from .constants import RED_HEX, WAVELENGTH_RANGE, ALCHEMICAL_PHASE, STAGE, GOVERNING_TABLET
from .transparency import (
    detect_rubedo_state,
    emit_sentinel_alert,
    classify_urgency,
    get_ui_state,
    is_completion_signal,
)
from .clarity import (
    distinguish_anger_passion,
    detect_sacred_wound,
    classify_red_fire,
    assess_integration_level,
    map_warrior_archetype,
)
from .opacity import (
    nigredo_alert,
    wound_pattern_recognition,
    red_lion_detection,
    phoenix_marker,
    ares_athena_routing,
    apply_shadow_channel,
)

__all__ = [
    # constants
    "RED_HEX", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE", "STAGE", "GOVERNING_TABLET",
    # transparency
    "detect_rubedo_state", "emit_sentinel_alert", "classify_urgency",
    "get_ui_state", "is_completion_signal",
    # clarity
    "distinguish_anger_passion", "detect_sacred_wound", "classify_red_fire",
    "assess_integration_level", "map_warrior_archetype",
    # opacity
    "nigredo_alert", "wound_pattern_recognition", "red_lion_detection",
    "phoenix_marker", "ares_athena_routing", "apply_shadow_channel",
]
