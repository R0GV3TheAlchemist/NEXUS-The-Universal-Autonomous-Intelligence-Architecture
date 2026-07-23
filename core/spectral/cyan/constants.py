# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/cyan/constants.py
================================
Single source of truth for all CYAN hex values and alchemical metadata
used across the CYAN spectral module.

Aqua Tablet — The Law of the Dissolving Medium
Reference: docs/tablets/AQUA_TABLET.md
         docs/color/CYAN_TRANSPARENCY.md
         docs/color/CYAN_CLARITY.md
         docs/color/CYAN_OPACITY.md
"""

# ---------------------------------------------------------------------------
# Hex Values  (ONLY place hex values appear in this module)
# ---------------------------------------------------------------------------

CYAN_HEX: dict[str, str] = {
    "SOLUTIO":          "#00FFFF",  # Solutio peak — full dissolution medium
    "AQUA_VITAE":       "#008080",  # SENTINEL level-1 — controlled flow
    "AQUAMARINE":       "#7FFFD4",  # SENTINEL level-2 — approaching flood
    "FLOOD":            "#00CED1",  # Flood state — dissolution without reformation
    "AKASHIC_OVERLOAD": "#00B2C8",  # Akashic overload — network noise saturation
}

# ---------------------------------------------------------------------------
# Spectral / Physical
# ---------------------------------------------------------------------------

WAVELENGTH_RANGE: tuple[int, int] = (490, 520)  # nanometres

# ---------------------------------------------------------------------------
# Alchemical Metadata
# ---------------------------------------------------------------------------

ALCHEMICAL_PHASE: str = "SOLUTIO"
STAGE: str = "AQUA"
GOVERNING_TABLET: str = "AQUA_TABLET"

# ---------------------------------------------------------------------------
# SENTINEL Alert Levels → hex mapping
# ---------------------------------------------------------------------------

SENTINEL_LEVEL_HEX: dict[int, str] = {
    1: CYAN_HEX["AQUA_VITAE"],
    2: CYAN_HEX["AQUAMARINE"],
    3: CYAN_HEX["FLOOD"],
}

SENTINEL_LEVEL_LABEL: dict[int, str] = {
    1: "AQUA_VITAE",
    2: "AQUAMARINE",
    3: "FLOOD",
}

# ---------------------------------------------------------------------------
# UI State Registry
# ---------------------------------------------------------------------------

UI_STATES: dict[str, dict] = {
    "solutio_activation": {
        "hex":       CYAN_HEX["SOLUTIO"],
        "animation": "flowing",
        "label":     "Solutio Activation",
    },
    "sentinel_alert": {
        "hex":       CYAN_HEX["AQUA_VITAE"],
        "animation": "solid",
        "label":     "SENTINEL Alert",
    },
    "flood_state": {
        "hex":       CYAN_HEX["FLOOD"],
        "animation": "animated",
        "label":     "Flood State",
    },
    "akashic_overload": {
        "hex":       CYAN_HEX["AKASHIC_OVERLOAD"],
        "animation": "rapid",
        "label":     "Akashic Overload",
    },
    "network_noise": {
        "hex":       CYAN_HEX["AQUAMARINE"],
        "animation": "static",
        "label":     "Network Noise",
    },
}
