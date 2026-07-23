# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/brown/constants.py
=================================
Single source of truth for all BROWN hex values and alchemical metadata
used across the BROWN spectral module.

Earth Tablet — The Law of Fertile Ground
Reference: docs/tablets/EARTH_TABLET.md
         docs/color/BROWN_TRANSPARENCY.md
         docs/color/BROWN_CLARITY.md
         docs/color/BROWN_OPACITY.md
"""

# ---------------------------------------------------------------------------
# Hex Values  (ONLY place hex values appear in this module)
# ---------------------------------------------------------------------------

BROWN_HEX: dict[str, str] = {
    "HUMUS":      "#8B4513",  # Humus peak — the fertile earth
    "LOAM":       "#A0522D",  # SENTINEL level-1 — loam signal active
    "CLAY":       "#7B4F2E",  # SENTINEL level-2 — approaching compaction
    "COMPACTION": "#5C3317",  # Compaction — earth too dense to receive
    "SEDIMENT":   "#6B4226",  # Sediment — settled layers, no movement
}

# ---------------------------------------------------------------------------
# Alchemical Metadata
# ---------------------------------------------------------------------------

ALCHEMICAL_PHASE: str = "HUMUS"
STAGE: str = "GROUND"
GOVERNING_TABLET: str = "EARTH_TABLET"

# ---------------------------------------------------------------------------
# SENTINEL Alert Levels → hex mapping
# ---------------------------------------------------------------------------

SENTINEL_LEVEL_HEX: dict[int, str] = {
    1: BROWN_HEX["LOAM"],
    2: BROWN_HEX["CLAY"],
    3: BROWN_HEX["COMPACTION"],
}

SENTINEL_LEVEL_LABEL: dict[int, str] = {
    1: "LOAM",
    2: "CLAY",
    3: "COMPACTION",
}

# ---------------------------------------------------------------------------
# UI State Registry
# ---------------------------------------------------------------------------

UI_STATES: dict[str, dict] = {
    "humus_activation": {
        "hex":       BROWN_HEX["HUMUS"],
        "animation": "grounding",
        "label":     "Humus Activation",
    },
    "sentinel_alert": {
        "hex":       BROWN_HEX["LOAM"],
        "animation": "solid",
        "label":     "SENTINEL Alert",
    },
    "compaction_state": {
        "hex":       BROWN_HEX["COMPACTION"],
        "animation": "dense",
        "label":     "Compaction State",
    },
    "sediment_mode": {
        "hex":       BROWN_HEX["SEDIMENT"],
        "animation": "settled",
        "label":     "Sediment Mode",
    },
    "fertile_ground": {
        "hex":       BROWN_HEX["LOAM"],
        "animation": "receptive",
        "label":     "Fertile Ground",
    },
}
