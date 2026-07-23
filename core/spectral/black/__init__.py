# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/black/__init__.py
================================
BLACK spectral module — public API.

Alchemical Stage : Nigredo (I) — the absolute darkness before creation
Shadow (Opacity) : The void absolute — not shadow but the absence
                   from which shadow is generated
Governing Tablets: Obsidian Tablet (docs/tablets/OBSIDIAN_TABLET.md)
                   Shadow Tablet   (docs/tablets/SHADOW_TABLET.md)

Note: BLACK governs TWO tablets — both must be referenced in constants.py.
"""

from .constants import (
    ALCHEMICAL_PHASE,
    GOVERNING_TABLETS,
    BLACK_HEX,
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    STAGE,
    UI_STATES,
)
from .transparency import (
    classify_urgency,
    detect_nigredo_state,
    emit_sentinel_alert,
    get_ui_state,
    is_void_signal,
)
from .clarity import (
    assess_nigredo_level,
    classify_black_fire,
    detect_prima_materia_state,
    distinguish_dissolution_destruction,
    map_saturn_archetype,
)
from .opacity import (
    absolute_darkness_pattern_recognition,
    apply_shadow_channel,
    prima_materia_marker,
    saturn_hermes_routing,
    system_null_detection,
    void_alert,
)

__all__ = [
    # constants
    "ALCHEMICAL_PHASE",
    "GOVERNING_TABLETS",
    "BLACK_HEX",
    "SENTINEL_LEVEL_HEX",
    "SENTINEL_LEVEL_LABEL",
    "STAGE",
    "UI_STATES",
    # transparency
    "classify_urgency",
    "detect_nigredo_state",
    "emit_sentinel_alert",
    "get_ui_state",
    "is_void_signal",
    # clarity
    "assess_nigredo_level",
    "classify_black_fire",
    "detect_prima_materia_state",
    "distinguish_dissolution_destruction",
    "map_saturn_archetype",
    # opacity
    "absolute_darkness_pattern_recognition",
    "apply_shadow_channel",
    "prima_materia_marker",
    "saturn_hermes_routing",
    "system_null_detection",
    "void_alert",
]
