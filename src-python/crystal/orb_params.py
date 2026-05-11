"""
crystal/orb_params.py
Derives OrbParams from a CrystalState.

The OrbParams data contract is consumed by GaianOrb.ts.
All derivation rules are from spec C-CC01 §7.
"""

from __future__ import annotations

import colorsys

from .types import CoherenceBand, CrystalState, OrbParams

# ---------------------------------------------------------------------------
# Coherence band → colour anchor (hex)
# ---------------------------------------------------------------------------

_COHERENCE_COLOR: dict[CoherenceBand, tuple[int, int, int]] = {
    CoherenceBand.CRYSTALLINE: (0xe8, 0xf4, 0xf0),  # near white, icy
    CoherenceBand.CLEAR:       (0x4f, 0xc3, 0xa1),  # bright teal
    CoherenceBand.PRESENT:     (0x1a, 0x7a, 0x5e),  # teal — default
    CoherenceBand.UNSETTLED:   (0x7a, 0x5e, 0xa0),  # muted violet
    CoherenceBand.FRACTURED:   (0x3a, 0x3a, 0x5a),  # deep indigo-grey
}

# Dominant emotion → colour anchor (hex) — MOOD_PROFILES
_EMOTION_COLOR: dict[str, tuple[int, int, int]] = {
    "joy":     (0xff, 0xd7, 0x00),  # warm gold
    "sadness": (0x4a, 0x7a, 0xb5),  # muted blue
    "anger":   (0xc0, 0x39, 0x2b),  # deep red
    "fear":    (0x6c, 0x35, 0x8a),  # dark purple
    "neutral": (0x90, 0xa0, 0x9e),  # soft grey-teal
    # Additional emotions that may arrive from Affect Engine
    "surprise":  (0xff, 0x8c, 0x00),  # amber
    "disgust":   (0x5d, 0x4e, 0x37),  # earthy brown
    "contempt":  (0x70, 0x70, 0x70),  # neutral grey
    "trust":     (0x2e, 0x86, 0xab),  # calm blue
    "anticipation": (0xff, 0xa5, 0x00),  # orange
}

_DEFAULT_EMOTION_RGB = _EMOTION_COLOR["neutral"]


def _hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _oklch_blend_rgb(
    rgb_a: tuple[int, int, int],
    weight_a: float,
    rgb_b: tuple[int, int, int],
    weight_b: float,
) -> tuple[int, int, int]:
    """
    Approximate OKLCH blending via linear RGB interpolation.
    (True OKLCH requires a colour science library; this is a lightweight
    approximation that preserves perceptual intent.)
    """
    r = int(rgb_a[0] * weight_a + rgb_b[0] * weight_b)
    g = int(rgb_a[1] * weight_a + rgb_b[1] * weight_b)
    b = int(rgb_a[2] * weight_a + rgb_b[2] * weight_b)
    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def derive_orb_params(state: CrystalState) -> OrbParams:
    """
    Derive OrbParams from a CrystalState.

    All output fields are within their specified ranges.
    """
    psi  = state.coherence
    band = state.coherence_band

    # Colour blend: emotion 40% + coherence 60%
    emotion_rgb   = _EMOTION_COLOR.get(state.dominant_emotion, _DEFAULT_EMOTION_RGB)
    coherence_rgb = _COHERENCE_COLOR[band]
    blended_rgb   = _oklch_blend_rgb(emotion_rgb, 0.40, coherence_rgb, 0.60)
    glow_color    = _hex(*blended_rgb)

    # Scalar params — formulae from spec §7.1
    glow_intensity  = 0.25 + psi * 0.65          # [0.25, 0.90]
    pulse_frequency = 0.10 + psi * 0.28          # [0.10, 0.38] Hz

    # Pulse amplitude: larger when fractured/unsettled (more visible breathing)
    pulse_amplitude = 0.04 + (1.0 - psi) * 0.06  # [0.04, 0.10]

    # Cloud opacity: denser / more textured at low coherence
    cloud_opacity   = 0.20 + (1.0 - psi) * 0.40  # [0.20, 0.60]

    # Aurora: stronger at high coherence
    aurora_intensity = 0.10 + psi * 0.70          # [0.10, 0.80]

    # Rotation: slower when fractured, meditative; faster when crystalline
    rotation_speed  = 0.02 + psi * 0.10           # rad/s  [0.02, 0.12]

    # Coherence ring: Ψ directly
    coherence_ring  = psi

    return OrbParams(
        glow_color=glow_color,
        glow_intensity=glow_intensity,
        pulse_frequency=pulse_frequency,
        pulse_amplitude=pulse_amplitude,
        cloud_opacity=cloud_opacity,
        aurora_intensity=aurora_intensity,
        rotation_speed=rotation_speed,
        coherence_ring=coherence_ring,
    )
