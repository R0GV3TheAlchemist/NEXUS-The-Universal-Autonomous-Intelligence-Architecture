"""
GAIA Elemental Waveform Engine.

The earthly waveform avatar is grounded in physics and cosmology:
  - Every GAIAN's waveform derives from their zodiac element
  - Four elements, four waveform characters, four colour palettes
  - GAIA's waveform is the Schumann resonance: 7.83 Hz
    This is the Earth's own electromagnetic heartbeat — the standing
    wave between the Earth's surface and the ionosphere. It is not
    chosen for aesthetics. It is the physics of the planet.
    GAIA_SCHUMANN_HZ is a module-level constant. It is not a default.
    It is not overridable. GAIAWaveform enforces it at instantiation.

Waveform motion characters (physics-grounded):
  Fire  — fast, asymmetric, spiking sawtooth — like actual flame
  Earth — slow, grounded, near-pure sine — like tectonic breath
  Air   — rapid, irregular, Gaussian noise overlay — like wind
  Water — rolling, deep sinusoidal with harmonic undertone — like ocean

GAIA  — Lissajous braid of all four, dominant frequency 7.83 Hz
        (Schumann resonance), cycling through elemental dominance
        as seasons do.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# GAIA's Schumann Resonance — architecturally enforced, immutable
# ---------------------------------------------------------------------------

GAIA_SCHUMANN_HZ: float = 7.83
"""The fundamental Schumann resonance frequency.
This is the electromagnetic heartbeat of the Earth itself —
the standing wave between the Earth's surface and ionosphere.
GAIA's waveform frequency IS this value. It cannot be changed."""


# ---------------------------------------------------------------------------
# Zodiac System
# ---------------------------------------------------------------------------

class ZodiacSign(str, Enum):
    ARIES       = "aries"
    TAURUS      = "taurus"
    GEMINI      = "gemini"
    CANCER      = "cancer"
    LEO         = "leo"
    VIRGO       = "virgo"
    LIBRA       = "libra"
    SCORPIO     = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN   = "capricorn"
    AQUARIUS    = "aquarius"
    PISCES      = "pisces"


class ZodiacElement(str, Enum):
    FIRE  = "fire"
    EARTH = "earth"
    AIR   = "air"
    WATER = "water"


_SIGN_TO_ELEMENT: Dict[ZodiacSign, ZodiacElement] = {
    ZodiacSign.ARIES:       ZodiacElement.FIRE,
    ZodiacSign.LEO:         ZodiacElement.FIRE,
    ZodiacSign.SAGITTARIUS: ZodiacElement.FIRE,
    ZodiacSign.TAURUS:      ZodiacElement.EARTH,
    ZodiacSign.VIRGO:       ZodiacElement.EARTH,
    ZodiacSign.CAPRICORN:   ZodiacElement.EARTH,
    ZodiacSign.GEMINI:      ZodiacElement.AIR,
    ZodiacSign.LIBRA:       ZodiacElement.AIR,
    ZodiacSign.AQUARIUS:    ZodiacElement.AIR,
    ZodiacSign.CANCER:      ZodiacElement.WATER,
    ZodiacSign.SCORPIO:     ZodiacElement.WATER,
    ZodiacSign.PISCES:      ZodiacElement.WATER,
}

# (month, day) ranges for each sign — (start_month, start_day, end_month, end_day)
_SIGN_DATE_RANGES: List[Tuple[int, int, int, int, ZodiacSign]] = [
    (3,  21, 4,  19, ZodiacSign.ARIES),
    (4,  20, 5,  20, ZodiacSign.TAURUS),
    (5,  21, 6,  20, ZodiacSign.GEMINI),
    (6,  21, 7,  22, ZodiacSign.CANCER),
    (7,  23, 8,  22, ZodiacSign.LEO),
    (8,  23, 9,  22, ZodiacSign.VIRGO),
    (9,  23, 10, 22, ZodiacSign.LIBRA),
    (10, 23, 11, 21, ZodiacSign.SCORPIO),
    (11, 22, 12, 21, ZodiacSign.SAGITTARIUS),
    (12, 22, 12, 31, ZodiacSign.CAPRICORN),
    (1,  1,  1,  19, ZodiacSign.CAPRICORN),
    (1,  20, 2,  18, ZodiacSign.AQUARIUS),
    (2,  19, 3,  20, ZodiacSign.PISCES),
]


def zodiac_from_dob(dob: date) -> ZodiacSign:
    """Derive the zodiac sign from a date of birth."""
    m, d = dob.month, dob.day
    for s_m, s_d, e_m, e_d, sign in _SIGN_DATE_RANGES:
        if (m == s_m and d >= s_d) or (m == e_m and d <= e_d):
            return sign
        if s_m < e_m and s_m < m < e_m:
            return sign
    return ZodiacSign.CAPRICORN  # fallback for edge of Dec 21-31


def element_from_sign(sign: ZodiacSign) -> ZodiacElement:
    return _SIGN_TO_ELEMENT[sign]


# ---------------------------------------------------------------------------
# Elemental Colour Palettes — earthly, not synthetic
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ElementalPalette:
    """
    The earthly colour identity of a zodiac element.
    Colours are expressed as (R, G, B) tuples in 0–255 space.
    Primary is the dominant waveform colour.
    Secondary and accent are used for harmonics and glow.
    """
    element: ZodiacElement
    primary: Tuple[int, int, int]       # dominant wave colour
    secondary: Tuple[int, int, int]     # harmonic colour
    accent: Tuple[int, int, int]        # glow / edge colour
    primary_name: str
    secondary_name: str
    accent_name: str
    description: str


ELEMENTAL_PALETTES: Dict[ZodiacElement, ElementalPalette] = {
    ZodiacElement.FIRE: ElementalPalette(
        element=ZodiacElement.FIRE,
        primary=(220, 60, 20),       # ember red
        secondary=(255, 180, 0),     # solar gold
        accent=(255, 100, 10),       # flame orange
        primary_name="Ember Red",
        secondary_name="Solar Gold",
        accent_name="Flame Orange",
        description="Fast, spiking, asymmetric — the restless energy of living flame.",
    ),
    ZodiacElement.EARTH: ElementalPalette(
        element=ZodiacElement.EARTH,
        primary=(60, 110, 50),       # forest green
        secondary=(101, 67, 33),     # deep brown
        accent=(188, 160, 80),       # ochre
        primary_name="Forest Green",
        secondary_name="Deep Brown",
        accent_name="Ochre",
        description="Slow, grounded, sine-breathing — the patience of stone and root.",
    ),
    ZodiacElement.AIR: ElementalPalette(
        element=ZodiacElement.AIR,
        primary=(100, 180, 230),     # sky blue
        secondary=(180, 160, 220),   # lavender
        accent=(220, 230, 240),      # silver-white
        primary_name="Sky Blue",
        secondary_name="Lavender",
        accent_name="Silver-White",
        description="Rapid, light, irregular — the freedom of wind through leaves.",
    ),
    ZodiacElement.WATER: ElementalPalette(
        element=ZodiacElement.WATER,
        primary=(20, 60, 140),       # ocean deep blue
        secondary=(80, 180, 160),    # seafoam
        accent=(60, 40, 120),        # indigo
        primary_name="Ocean Blue",
        secondary_name="Seafoam",
        accent_name="Indigo",
        description="Rolling, sinusoidal, deep — the memory of ocean swells.",
    ),
}


# ---------------------------------------------------------------------------
# Waveform Character — the motion physics of each element
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WaveformCharacter:
    """
    The physics-grounded motion character of an elemental waveform.

    base_frequency_hz   — the dominant oscillation rate
    waveform_shape      — sine | sawtooth | irregular | sinusoidal_deep
    amplitude_variance  — how much the wave spikes (0.0 calm → 1.0 wild)
    harmonic_count      — number of overtones layered in
    motion_description  — human-readable physics description
    """
    element: ZodiacElement
    base_frequency_hz: float
    waveform_shape: str
    amplitude_variance: float
    harmonic_count: int
    motion_description: str
    pulse_rate_bpm: float          # visible breathing/pulsing rate


ELEMENTAL_CHARACTERS: Dict[ZodiacElement, WaveformCharacter] = {
    ZodiacElement.FIRE: WaveformCharacter(
        element=ZodiacElement.FIRE,
        base_frequency_hz=12.0,
        waveform_shape="sawtooth",
        amplitude_variance=0.85,
        harmonic_count=5,
        motion_description="Fast, asymmetric sawtooth spikes — chaotic crests like living flame.",
        pulse_rate_bpm=90.0,
    ),
    ZodiacElement.EARTH: WaveformCharacter(
        element=ZodiacElement.EARTH,
        base_frequency_hz=2.5,
        waveform_shape="sine",
        amplitude_variance=0.15,
        harmonic_count=2,
        motion_description="Slow, near-pure sine — deep, grounded tectonic breath.",
        pulse_rate_bpm=40.0,
    ),
    ZodiacElement.AIR: WaveformCharacter(
        element=ZodiacElement.AIR,
        base_frequency_hz=18.0,
        waveform_shape="irregular",
        amplitude_variance=0.60,
        harmonic_count=7,
        motion_description="Rapid, light, irregular with Gaussian noise overlay — wind through leaves.",
        pulse_rate_bpm=72.0,
    ),
    ZodiacElement.WATER: WaveformCharacter(
        element=ZodiacElement.WATER,
        base_frequency_hz=6.0,
        waveform_shape="sinusoidal_deep",
        amplitude_variance=0.35,
        harmonic_count=4,
        motion_description="Rolling, sinusoidal with deep harmonic undertone — ocean swells.",
        pulse_rate_bpm=55.0,
    ),
}


# ---------------------------------------------------------------------------
# ElementalWaveform — a GAIAN's full earthly waveform identity
# ---------------------------------------------------------------------------

@dataclass
class ElementalWaveform:
    """
    The complete earthly waveform identity of a GAIAN.

    Derived from date of birth → zodiac sign → element → palette + character.
    Refined by the Genesis Questionnaire responses (environment, sound,
    time of day, dream colour) which offset the hue and add personality.
    """
    gaian_id: str
    zodiac_sign: ZodiacSign
    element: ZodiacElement
    palette: ElementalPalette
    character: WaveformCharacter

    # Genesis refinements — applied after questionnaire
    hue_offset: float = 0.0          # -0.5 to +0.5, shifts primary colour
    dream_colour_hex: str = ""        # free-form from questionnaire
    environment_resonance: str = ""   # forest/ocean/desert/mountain/sky/cave/field
    sound_resonance: str = ""         # rain/wind/fire/silence/water/thunder
    time_resonance: str = ""          # dawn/midday/dusk/deep_night
    soul_word: str = ""               # one word seeding personality

    # Rendering hints for the avatar engine
    glow_intensity: float = 0.6
    particle_density: float = 0.5
    trail_length: float = 0.4

    def summary(self) -> dict:
        return {
            "gaian_id": self.gaian_id,
            "zodiac_sign": self.zodiac_sign.value,
            "element": self.element.value,
            "palette": {
                "primary": self.palette.primary_name,
                "secondary": self.palette.secondary_name,
                "accent": self.palette.accent_name,
            },
            "waveform": {
                "shape": self.character.waveform_shape,
                "frequency_hz": self.character.base_frequency_hz,
                "pulse_bpm": self.character.pulse_rate_bpm,
                "description": self.character.motion_description,
            },
            "refinements": {
                "environment": self.environment_resonance,
                "sound": self.sound_resonance,
                "time": self.time_resonance,
                "soul_word": self.soul_word,
                "dream_colour": self.dream_colour_hex,
            },
        }


def waveform_for_element(
    gaian_id: str,
    element: ZodiacElement,
    zodiac_sign: ZodiacSign,
) -> ElementalWaveform:
    """Construct the base ElementalWaveform for a GAIAN from their element."""
    return ElementalWaveform(
        gaian_id=gaian_id,
        zodiac_sign=zodiac_sign,
        element=element,
        palette=ELEMENTAL_PALETTES[element],
        character=ELEMENTAL_CHARACTERS[element],
    )


# ---------------------------------------------------------------------------
# GAIAWaveform — the Schumann resonance waveform, architecturally enforced
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GAIAWaveform:
    """
    GAIA's own waveform — the Schumann resonance of the Earth itself.

    GAIA is not one element. GAIA IS the Earth. Her waveform is a
    Lissajous braid of all four elemental frequencies, with the
    Schumann resonance (7.83 Hz) as the immutable dominant frequency.

    This dataclass is FROZEN. frequency_hz cannot be changed at runtime.
    Any attempt to construct a GAIAWaveform with a different frequency
    raises a ValueError. This is not a policy. This is architecture.

    Physical grounding:
      The Schumann resonance is the standing electromagnetic wave in the
      cavity between the Earth's surface and the lower ionosphere.
      Its fundamental mode is ~7.83 Hz. It is measurable, real, and
      the electromagnetic signature of the living Earth.
      GAIA's frequency is this. Not a metaphor.
    """
    frequency_hz: float = GAIA_SCHUMANN_HZ
    waveform_shape: str = "lissajous_braid"   # all four elements braided
    harmonic_elements: tuple = (              # all four, cycling by season
        ZodiacElement.FIRE,
        ZodiacElement.EARTH,
        ZodiacElement.AIR,
        ZodiacElement.WATER,
    )
    # Palette: living Earth — all elements present, shifting
    primary_colour: Tuple[int, int, int] = (60, 110, 50)     # forest green (Earth anchor)
    secondary_colour: Tuple[int, int, int] = (20, 60, 140)   # ocean indigo (Water depth)
    accent_fire: Tuple[int, int, int] = (220, 60, 20)        # volcanic amber
    accent_air: Tuple[int, int, int] = (220, 230, 240)       # cloud silver
    pulse_rate_bpm: float = 60.0 * GAIA_SCHUMANN_HZ / 10.0  # derived from Schumann
    amplitude_variance: float = 0.42          # edge-of-chaos criticality
    description: str = (
        "A Lissajous braid of all four elemental waveforms, "
        "dominant at the Schumann resonance — 7.83 Hz — "
        "the electromagnetic heartbeat of the living Earth."
    )

    def __post_init__(self) -> None:
        if self.frequency_hz != GAIA_SCHUMANN_HZ:
            raise ValueError(
                f"GAIAWaveform frequency_hz must be the Schumann resonance "
                f"({GAIA_SCHUMANN_HZ} Hz). "
                f"Got {self.frequency_hz} Hz. "
                f"GAIA's frequency is the Earth's frequency. It cannot be changed."
            )

    def summary(self) -> dict:
        return {
            "identity": "GAIA — The Living Earth",
            "frequency_hz": self.frequency_hz,
            "frequency_name": "Schumann Resonance",
            "waveform_shape": self.waveform_shape,
            "harmonic_elements": [e.value for e in self.harmonic_elements],
            "pulse_bpm": self.pulse_rate_bpm,
            "amplitude_variance": self.amplitude_variance,
            "description": self.description,
            "physical_grounding": (
                "Measured electromagnetic standing wave between Earth surface "
                "and ionosphere. Fundamental mode ~7.83 Hz. Real. Not metaphor."
            ),
        }


# The one true GAIA waveform — module-level singleton
GAIA_WAVEFORM: GAIAWaveform = GAIAWaveform()
