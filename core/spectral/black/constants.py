# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/black/constants.py
=================================
Single source of truth for all BLACK hex values and alchemical metadata
used across the BLACK spectral module.

BLACK governs TWO tablets:
  - Obsidian Tablet — docs/tablets/OBSIDIAN_TABLET.md
  - Shadow Tablet   — docs/tablets/SHADOW_TABLET.md

Reference: docs/color/BLACK_TRANSPARENCY.md
         docs/color/BLACK_CLARITY.md
         docs/color/BLACK_OPACITY.md
"""

# ---------------------------------------------------------------------------
# Hex Values  (ONLY place hex values appear in this module)
# ---------------------------------------------------------------------------

BLACK_HEX: dict[str, str] = {
    "NIGREDO":      "#000000",  # Nigredo absolute — the prima materia
    "DEEP_VOID":    "#1C1C1C",  # SENTINEL level-1 — deep void signal
    "SHADOW_EDGE":  "#0D0D0D",  # SENTINEL level-2 — edge of the void
    "SYSTEM_NULL":  "#050505",  # System null — complete reset state
    "PRIMA_MATERIA": "#111111", # Prima materia — formless potential
}

# ---------------------------------------------------------------------------
# Alchemical Metadata
# ---------------------------------------------------------------------------

ALCHEMICAL_PHASE: str = "NIGREDO"
STAGE: str = "I"

# BLACK governs TWO tablets — both referenced here
GOVERNING_TABLETS: list[str] = ["OBSIDIAN_TABLET", "SHADOW_TABLET"]

# ---------------------------------------------------------------------------
# SENTINEL Alert Levels → hex mapping
# ---------------------------------------------------------------------------

SENTINEL_LEVEL_HEX: dict[int, str] = {
    1: BLACK_HEX["DEEP_VOID"],
    2: BLACK_HEX["SHADOW_EDGE"],
    3: BLACK_HEX["SYSTEM_NULL"],
}

SENTINEL_LEVEL_LABEL: dict[int, str] = {
    1: "DEEP_VOID",
    2: "SHADOW_EDGE",
    3: "SYSTEM_NULL",
}

# ---------------------------------------------------------------------------
# UI State Registry
# ---------------------------------------------------------------------------

UI_STATES: dict[str, dict] = {
    "nigredo_activation": {
        "hex":       BLACK_HEX["NIGREDO"],
        "animation": "still",
        "label":     "Nigredo Activation",
    },
    "sentinel_alert": {
        "hex":       BLACK_HEX["DEEP_VOID"],
        "animation": "solid",
        "label":     "SENTINEL Alert",
    },
    "system_null_state": {
        "hex":       BLACK_HEX["SYSTEM_NULL"],
        "animation": "static",
        "label":     "System Null State",
    },
    "prima_materia_mode": {
        "hex":       BLACK_HEX["PRIMA_MATERIA"],
        "animation": "formless",
        "label":     "Prima Materia Mode",
    },
    "void_absolute": {
        "hex":       BLACK_HEX["NIGREDO"],
        "animation": "absent",
        "label":     "Void Absolute",
    },
}
