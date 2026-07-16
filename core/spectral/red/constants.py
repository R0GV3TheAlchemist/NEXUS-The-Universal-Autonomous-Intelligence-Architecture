"""
core/spectral/red/constants.py
==============================
Single source of truth for all RED hex values, wavelength bounds,
and alchemical metadata used across the RED spectral module.

Ruby Tablet — Law of the Living Flame
"""

# ---------------------------------------------------------------------------
# Hex Values
# ---------------------------------------------------------------------------

RED_HEX: dict[str, str] = {
    "RUBEDO":       "#CC2200",  # Rubedo activation — deep living flame
    "ALERT":        "#DC2626",  # SENTINEL level-1 alert
    "DANGER":       "#DC2626",  # SENTINEL level-2 (same base, higher context)
    "CRIMSON":      "#DC143C",  # Completion signal — Rubedo completion marker
    "SCARLET":      "#FF3333",  # Error state — unbound fire
    "DEEP_CARMINE": "#FF2400",  # Living Flame mode — animated, fully alive
}

# ---------------------------------------------------------------------------
# Spectral / Physical
# ---------------------------------------------------------------------------

WAVELENGTH_RANGE: tuple[int, int] = (620, 750)  # nanometres

# ---------------------------------------------------------------------------
# Alchemical Metadata
# ---------------------------------------------------------------------------

ALCHEMICAL_PHASE: str = "Rubedo"
STAGE: int = 4
GOVERNING_TABLET: str = "Ruby Tablet"

# ---------------------------------------------------------------------------
# SENTINEL Alert Levels → hex mapping
# ---------------------------------------------------------------------------

SENTINEL_LEVEL_HEX: dict[int, str] = {
    1: RED_HEX["ALERT"],
    2: RED_HEX["DANGER"],
    3: RED_HEX["SCARLET"],
}

SENTINEL_LEVEL_LABEL: dict[int, str] = {
    1: "ALERT",
    2: "DANGER",
    3: "SCARLET",
}

# ---------------------------------------------------------------------------
# UI State Registry
# ---------------------------------------------------------------------------

UI_STATES: dict[str, dict] = {
    "rubedo_activation": {
        "hex":       RED_HEX["RUBEDO"],
        "animation": "pulsing",
        "label":     "Rubedo Activation",
    },
    "sentinel_alert": {
        "hex":       RED_HEX["ALERT"],
        "animation": "solid",
        "label":     "SENTINEL Alert",
    },
    "completion_signal": {
        "hex":       RED_HEX["CRIMSON"],
        "animation": "static",
        "label":     "Completion Signal",
    },
    "error_state": {
        "hex":       RED_HEX["SCARLET"],
        "animation": "solid",
        "label":     "Error State",
    },
    "living_flame_mode": {
        "hex":       RED_HEX["DEEP_CARMINE"],
        "animation": "animated",
        "label":     "Living Flame Mode",
    },
}
