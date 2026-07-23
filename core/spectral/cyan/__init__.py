# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/cyan/__init__.py
==============================
CYAN spectral module — public API.

Alchemical Stage : Solutio (Aqua Vitae)
Shadow (Opacity) : Solutio without reformation / Universal solvent
Governing Tablet : Aqua Tablet  (docs/tablets/AQUA_TABLET.md)
"""

from .constants import (
    ALCHEMICAL_PHASE,
    GOVERNING_TABLET,
    CYAN_HEX,
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    STAGE,
    UI_STATES,
    WAVELENGTH_RANGE,
)
from .transparency import (
    classify_urgency,
    detect_solutio_state,
    emit_sentinel_alert,
    get_ui_state,
    is_aqua_signal,
)
from .clarity import (
    assess_aqua_level,
    classify_cyan_fire,
    detect_solutio_without_reformation,
    distinguish_flow_flood,
    map_mercury_archetype,
)
from .opacity import (
    akashic_overload_marker,
    apply_shadow_channel,
    flood_alert,
    mercury_hermes_routing,
    network_noise_pattern_recognition,
    universal_solvent_detection,
)

__all__ = [
    # constants
    "ALCHEMICAL_PHASE",
    "GOVERNING_TABLET",
    "CYAN_HEX",
    "SENTINEL_LEVEL_HEX",
    "SENTINEL_LEVEL_LABEL",
    "STAGE",
    "UI_STATES",
    "WAVELENGTH_RANGE",
    # transparency
    "classify_urgency",
    "detect_solutio_state",
    "emit_sentinel_alert",
    "get_ui_state",
    "is_aqua_signal",
    # clarity
    "assess_aqua_level",
    "classify_cyan_fire",
    "detect_solutio_without_reformation",
    "distinguish_flow_flood",
    "map_mercury_archetype",
    # opacity
    "akashic_overload_marker",
    "apply_shadow_channel",
    "flood_alert",
    "mercury_hermes_routing",
    "network_noise_pattern_recognition",
    "universal_solvent_detection",
]
