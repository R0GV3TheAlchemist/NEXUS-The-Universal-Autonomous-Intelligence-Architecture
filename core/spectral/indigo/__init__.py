"""
INDIGO spectral module — public API.
Alchemical Stage: Distillation
"""

from .constants import (
    COLOR, HEX, HEX_ALT, WAVELENGTH_RANGE, ALCHEMICAL_PHASE,
    STAGE, GOVERNING_TABLET, SENTINEL_LEVELS, UI_STATE,
    INTUITION_ARCHETYPES, DISTILLATION_MARKERS, BLOCK_MARKERS,
)
from .transparency import (
    detect_third_eye_state, emit_indigo_alert, classify_intuition_urgency,
    get_ui_state, is_distillation_signal,
)
from .clarity import (
    distinguish_intuition_delusion, detect_block_pattern,
    classify_indigo_fire, assess_field_perception_health, map_intuition_archetype,
)
from .opacity import (
    block_alert, psychic_overload_detection, vision_fog_marker,
    saturn_jupiter_routing, apply_shadow_channel,
)

__all__ = [
    "COLOR", "HEX", "HEX_ALT", "WAVELENGTH_RANGE", "ALCHEMICAL_PHASE",
    "STAGE", "GOVERNING_TABLET", "SENTINEL_LEVELS", "UI_STATE",
    "INTUITION_ARCHETYPES", "DISTILLATION_MARKERS", "BLOCK_MARKERS",
    "detect_third_eye_state", "emit_indigo_alert", "classify_intuition_urgency",
    "get_ui_state", "is_distillation_signal",
    "distinguish_intuition_delusion", "detect_block_pattern",
    "classify_indigo_fire", "assess_field_perception_health", "map_intuition_archetype",
    "block_alert", "psychic_overload_detection", "vision_fog_marker",
    "saturn_jupiter_routing", "apply_shadow_channel",
]
