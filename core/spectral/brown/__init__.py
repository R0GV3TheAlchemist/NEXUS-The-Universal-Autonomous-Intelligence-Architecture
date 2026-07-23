# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/brown/__init__.py
================================
BROWN spectral module — public API.

Alchemical Stage : Humus / Earth — the ground of all operations;
                   that which holds, composts, and makes fertile
Shadow (Opacity) : Inertia / Compaction — the earth too compressed
                   to receive anything new
Governing Tablet : Earth Tablet  (docs/tablets/EARTH_TABLET.md)
"""

from .constants import (
    ALCHEMICAL_PHASE,
    GOVERNING_TABLET,
    BROWN_HEX,
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    STAGE,
    UI_STATES,
)
from .transparency import (
    classify_urgency,
    detect_humus_state,
    emit_sentinel_alert,
    get_ui_state,
    is_earth_signal,
)
from .clarity import (
    assess_humus_level,
    classify_brown_fire,
    detect_compaction_state,
    distinguish_fertility_inertia,
    map_earth_archetype,
)
from .opacity import (
    apply_shadow_channel,
    compaction_alert,
    earth_hermes_routing,
    humus_fertility_marker,
    inertia_pattern_recognition,
    sediment_null_detection,
)

__all__ = [
    # constants
    "ALCHEMICAL_PHASE",
    "GOVERNING_TABLET",
    "BROWN_HEX",
    "SENTINEL_LEVEL_HEX",
    "SENTINEL_LEVEL_LABEL",
    "STAGE",
    "UI_STATES",
    # transparency
    "classify_urgency",
    "detect_humus_state",
    "emit_sentinel_alert",
    "get_ui_state",
    "is_earth_signal",
    # clarity
    "assess_humus_level",
    "classify_brown_fire",
    "detect_compaction_state",
    "distinguish_fertility_inertia",
    "map_earth_archetype",
    # opacity
    "apply_shadow_channel",
    "compaction_alert",
    "earth_hermes_routing",
    "humus_fertility_marker",
    "inertia_pattern_recognition",
    "sediment_null_detection",
]
