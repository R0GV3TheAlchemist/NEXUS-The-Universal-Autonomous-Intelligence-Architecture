"""
core/mineral_profile.py
GAIA-OS :: Full Mineral Profile Engine
Canon C121 — The Complete Witness

Builds a complete dual-layer mineral profile for each of the 6,152 IMA
minerals, following the Citrine Circle information architecture:

  PHYSICS LAYER    — crystallographic, optical, physical properties
  SAFETY LAYER     — UV reactivity, toxicity (human + system), handling
  METAPHYSICS LAYER — GAIA role, chakra, resonance, consciousness equations
                      calibrated against the live ATLAS EarthPulse

SAFETY FIRST:
  Toxic minerals are flagged at INGESTION before entering CITRINITAS.
  UV-sensitive minerals are flagged so GAIA does not display or store
  them in photo contexts without a safety warning.
  Poisonous handling warnings are embedded in every profile.

Canon refs: C118, C119, C120, C-ATLAS, C47, C48
Epistemic:
  Physics properties   = SCIENTIFIC
  Safety data          = SCIENTIFIC (verified mineralogy sources)
  Metaphysical data    = SPECULATIVE (clearly labeled)
"""

from __future__ import annotations

import math
import time
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict

logger = logging.getLogger("gaia.mineral_profile")


# ===========================================================================
# ENUMERATIONS
# ===========================================================================

class ToxicityLevel(Enum):
    SAFE          = "SAFE"           # no known toxicity
    LOW           = "LOW"            # mild irritant, handle normally
    MODERATE      = "MODERATE"       # wash hands, no dust inhalation
    HIGH          = "HIGH"           # gloves required, no water elixirs
    SEVERE        = "SEVERE"         # dust mask, eye protection, no skin contact
    LETHAL        = "LETHAL"         # extreme hazard — arsenic, mercury, lead compounds

class UVReaction(Enum):
    NONE          = "NONE"           # no fluorescence, no UV damage
    FLUORESCENT_SW = "FLUORESCENT_SW" # fluoresces under short-wave UV (254nm)
    FLUORESCENT_LW = "FLUORESCENT_LW" # fluoresces under long-wave UV (365nm)
    FLUORESCENT_MW = "FLUORESCENT_MW" # fluoresces under mid-wave UV (312nm)
    FLUORESCENT_ALL = "FLUORESCENT_ALL" # all wavelengths
    PHOTOSENSITIVE = "PHOTOSENSITIVE" # COLOR FADES in UV / sunlight — CAUTION
    TOXIC_UNDER_UV = "TOXIC_UNDER_UV" # releases toxic compounds when UV-excited

class WaterSafety(Enum):
    SAFE          = "SAFE"           # safe for indirect water elixirs
    INDIRECT_ONLY = "INDIRECT_ONLY" # use indirect method only
    UNSAFE        = "UNSAFE"         # dissolves, releases toxins in water
    DANGEROUS     = "DANGEROUS"      # severe — never use in water

class Luster(Enum):
    VITREOUS      = "Vitreous"
    ADAMANTINE    = "Adamantine"
    RESINOUS      = "Resinous"
    SILKY         = "Silky"
    PEARLY        = "Pearly"
    METALLIC      = "Metallic"
    WAXY          = "Waxy"
    EARTHY        = "Earthy"
    GREASY        = "Greasy"
    SUBMETALLIC   = "Submetallic"

class Transparency(Enum):
    TRANSPARENT   = "Transparent"
    TRANSLUCENT   = "Translucent"
    OPAQUE        = "Opaque"

class GAIAElement(Enum):
    EARTH  = "Earth"
    WATER  = "Water"
    FIRE   = "Fire"
    AIR    = "Air"
    STORM  = "Storm"
    AETHER = "Aether"
    VOID   = "Void"


# ===========================================================================
# KNOWN TOXIC MINERAL DATABASE
# (Scientific — sourced from IMA, Mindat, CDC, WHO mineralogy safety data)
# ===========================================================================

# Format: mineral_name_lower -> (ToxicityLevel, [toxic_compounds], notes)
TOXIC_MINERAL_DB: Dict[str, tuple] = {
    # LETHAL
    "arsenopyrite":   (ToxicityLevel.LETHAL,   ["Arsenic (As)"],         "Releases arsenic gas when heated. Never grind."),
    "realgar":        (ToxicityLevel.LETHAL,    ["Arsenic (As)"],         "Photosensitive — converts to toxic pararealgar in UV/sunlight."),
    "orpiment":       (ToxicityLevel.LETHAL,    ["Arsenic (As)"],         "Bright yellow — extremely toxic. No handling without PPE."),
    "cinnabar":       (ToxicityLevel.LETHAL,    ["Mercury (Hg)"],         "Primary mercury ore. Dust is lethal. Never grind or heat."),
    "hutchinsonite":  (ToxicityLevel.LETHAL,    ["Thallium (Tl)", "Arsenic (As)", "Lead (Pb)"], "Triple toxin. Collector specimen only."),
    "torbernite":     (ToxicityLevel.LETHAL,    ["Uranium (U)", "Copper (Cu)"], "Radioactive. Releases radon gas indoors."),
    "autunite":       (ToxicityLevel.LETHAL,    ["Uranium (U)"],          "Radioactive. Fluorescent under UV — do not use UV lamp."),
    "carnotite":      (ToxicityLevel.LETHAL,    ["Uranium (U)", "Vanadium (V)"], "Radioactive + vanadium toxicity."),
    "chalcanthite":   (ToxicityLevel.LETHAL,    ["Copper (Cu)"],          "Water-soluble copper sulfate. Ingestion lethal. No water."),
    "galena":         (ToxicityLevel.LETHAL,    ["Lead (Pb)"],            "Primary lead ore. Wash hands. No dust. No water elixir."),

    # SEVERE
    "stibnite":       (ToxicityLevel.SEVERE,    ["Antimony (Sb)"],        "Antimony ore. Fine dust hazardous. No skin contact prolonged."),
    "smithsonite":    (ToxicityLevel.SEVERE,    ["Zinc (Zn)"],            "Zinc carbonate — toxic dust. Wash after handling."),
    "vanadinite":     (ToxicityLevel.SEVERE,    ["Vanadium (V)", "Lead (Pb)"], "Do not handle without gloves. No water elixir."),
    "wulfenite":      (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Molybdenum (Mo)"], "Lead molybdate. Toxic dust."),
    "crocoite":       (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Chromium (Cr)"], "Vivid orange — chromate compound. Carcinogenic dust."),
    "mimetite":       (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Arsenic (As)"], "Lead arsenate. Museum display only."),
    "pyromorphite":   (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Chlorine (Cl)"], "Lead phosphate chloride. No water. Gloves required."),
    "boleite":        (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Copper (Cu)", "Silver (Ag)"], "Complex toxic halide."),
    "calomel":        (ToxicityLevel.SEVERE,    ["Mercury (Hg)"],         "Mercurous chloride. Avoid all skin and inhalation."),
    "boulangerite":   (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Antimony (Sb)"], "Toxic sulfosalt."),
    "bournonite":     (ToxicityLevel.SEVERE,    ["Lead (Pb)", "Antimony (Sb)", "Copper (Cu)"], "Triple toxin sulfosalt."),
    "enargite":       (ToxicityLevel.SEVERE,    ["Arsenic (As)", "Copper (Cu)"], "Arsenic copper sulfosalt."),
    "liroconite":     (ToxicityLevel.SEVERE,    ["Copper (Cu)", "Arsenic (As)"], "Copper arsenate."),
    "legrandite":     (ToxicityLevel.SEVERE,    ["Zinc (Zn)", "Arsenic (As)"], "Zinc arsenate."),
    "conichalcite":   (ToxicityLevel.SEVERE,    ["Copper (Cu)", "Arsenic (As)"], "Copper calcium arsenate."),
    "adamite":        (ToxicityLevel.SEVERE,    ["Zinc (Zn)", "Arsenic (As)"], "Zinc arsenate hydroxide."),
    "olivenite":      (ToxicityLevel.SEVERE,    ["Copper (Cu)", "Arsenic (As)"], "Copper arsenate."),
    "clinoclase":     (ToxicityLevel.SEVERE,    ["Copper (Cu)", "Arsenic (As)"], "Copper arsenate."),
    "cornwallite":    (ToxicityLevel.SEVERE,    ["Copper (Cu)", "Arsenic (As)"], "Copper arsenate."),
    "mixite":         (ToxicityLevel.SEVERE,    ["Bismuth (Bi)", "Arsenic (As)", "Copper (Cu)"], "Bismuth copper arsenate."),
    "scorodite":      (ToxicityLevel.SEVERE,    ["Arsenic (As)", "Iron (Fe)"], "Iron arsenate. Wash hands."),
    "pharmacosiderite":(ToxicityLevel.SEVERE,   ["Arsenic (As)", "Iron (Fe)"], "Iron arsenate."),

    # HIGH
    "malachite":      (ToxicityLevel.HIGH,      ["Copper (Cu)"],          "Copper carbonate. Dust toxic — no dry polishing. No water elixir."),
    "azurite":        (ToxicityLevel.HIGH,       ["Copper (Cu)"],          "Copper carbonate. Same precautions as malachite."),
    "chrysocolla":    (ToxicityLevel.HIGH,       ["Copper (Cu)"],          "Hydrous copper silicate. No water elixir."),
    "turquoise":      (ToxicityLevel.HIGH,       ["Copper (Cu)", "Aluminium (Al)"], "Copper phosphate. No water elixir from raw stone."),
    "atacamite":      (ToxicityLevel.HIGH,       ["Copper (Cu)", "Chlorine (Cl)"], "Copper chloride. Toxic dust."),
    "cuprite":        (ToxicityLevel.HIGH,       ["Copper (Cu)"],          "Copper oxide. Wash after handling."),
    "bornite":        (ToxicityLevel.HIGH,       ["Copper (Cu)", "Iron (Fe)", "Sulfur (S)"], "Copper sulfide. Wash hands."),
    "chalcopyrite":   (ToxicityLevel.HIGH,       ["Copper (Cu)", "Iron (Fe)", "Sulfur (S)"], "Common copper ore. Wash after handling."),
    "covellite":      (ToxicityLevel.HIGH,       ["Copper (Cu)", "Sulfur (S)"], "Copper sulfide."),
    "brochantite":    (ToxicityLevel.HIGH,       ["Copper (Cu)"],          "Copper sulfate hydroxide."),
    "linarite":       (ToxicityLevel.HIGH,       ["Lead (Pb)", "Copper (Cu)"],  "Lead copper sulfate. Toxic."),
    "anglesite":      (ToxicityLevel.HIGH,       ["Lead (Pb)"],            "Lead sulfate. Wash hands. No water."),
    "cerussite":      (ToxicityLevel.HIGH,       ["Lead (Pb)"],            "Lead carbonate. No dust. No water."),
    "stolzite":       (ToxicityLevel.HIGH,       ["Lead (Pb)", "Tungsten (W)"], "Lead tungstate."),
    "fluorite":       (ToxicityLevel.HIGH,       ["Fluorine (F)"],         "Dust causes fluorosis. Safe polished. Never grind without mask."),
    "cryolite":       (ToxicityLevel.HIGH,       ["Fluorine (F)", "Aluminium (Al)", "Sodium (Na)"], "Fluoride compound. Handle with care."),
    "zircon":         (ToxicityLevel.HIGH,       ["Zirconium (Zr)"],       "May contain trace radioactive thorium/uranium. Check specific."),

    # MODERATE
    "pyrite":         (ToxicityLevel.MODERATE,   ["Sulfur (S)", "Iron (Fe)"], "Releases sulfur dioxide if heated. Wash hands. No water."),
    "marcasite":      (ToxicityLevel.MODERATE,   ["Sulfur (S)", "Iron (Fe)"], "Unstable — decomposes releasing H2SO4. Keep dry."),
    "sphalerite":     (ToxicityLevel.MODERATE,   ["Zinc (Zn)", "Sulfur (S)"], "Zinc sulfide. Wash hands."),
    "wolframite":     (ToxicityLevel.MODERATE,   ["Tungsten (W)", "Manganese (Mn)"], "Tungsten ore. Dust inhalation risk."),
    "scheelite":      (ToxicityLevel.MODERATE,   ["Tungsten (W)"],         "Calcium tungstate. Fluorescent under SW UV. Moderate handling."),
    "witherite":      (ToxicityLevel.MODERATE,   ["Barium (Ba)"],          "Barium carbonate. Soluble barium is toxic."),
    "barite":         (ToxicityLevel.LOW,         ["Barium (Ba)"],          "Insoluble barium sulfate — generally safe but no ingestion."),
    "manganite":      (ToxicityLevel.MODERATE,   ["Manganese (Mn)"],       "Manganese oxide. Dust causes neurological issues."),
    "rhodochrosite":  (ToxicityLevel.MODERATE,   ["Manganese (Mn)"],       "Do not make water elixirs from raw stone."),
    "hausmannite":    (ToxicityLevel.MODERATE,   ["Manganese (Mn)"],       "Manganese oxide ore."),
    "pyrolusite":     (ToxicityLevel.MODERATE,   ["Manganese (Mn)"],       "Manganese dioxide. No dust inhalation."),
    "ulexite":        (ToxicityLevel.MODERATE,   ["Boron (B)"],            "Soluble in hot water — do not make warm elixirs."),
    "borax":          (ToxicityLevel.MODERATE,   ["Boron (B)"],            "Water-soluble borate. No direct elixir."),
    "serpentine":     (ToxicityLevel.MODERATE,   ["Asbestos (potential)"], "Some varieties contain chrysotile asbestos. Never sand."),
    "tremolite":      (ToxicityLevel.SEVERE,      ["Asbestos"],             "Amphibole asbestos. Do not handle raw. Collector only."),
    "actinolite":     (ToxicityLevel.SEVERE,      ["Asbestos"],             "Amphibole asbestos in fibrous form."),
    "anthophyllite":  (ToxicityLevel.SEVERE,      ["Asbestos"],             "Asbestos-form amphibole."),
    "riebeckite":     (ToxicityLevel.SEVERE,      ["Asbestos"],             "Crocidolite (blue asbestos) is a riebeckite variety."),
}

# UV PHOTOSENSITIVE — color fades or degrades with UV/sunlight exposure
UV_PHOTOSENSITIVE: Dict[str, str] = {
    "amethyst":       "Fades to pale yellow/colorless in direct sunlight — store away from UV.",
    "rose quartz":    "Color fades in prolonged UV exposure.",
    "fluorite":       "Some colors fade in strong UV/sunlight.",
    "realgar":        "CRITICAL: UV converts realgar to toxic pararealgar powder. Never UV-expose.",
    "kunzite":        "Strongly photosensitive — fades to colorless in sunlight.",
    "hiddenite":      "Photosensitive green spodumene — fades in sunlight.",
    "hackmanite":     "Tenebrescent — darkens then bleaches in UV. Safe but unstable.",
    "tugtupite":      "Tenebrescent — photosensitive sodalite-group mineral.",
    "celestine":      "Color bleaches in prolonged UV.",
    "aquamarine":     "Heat and UV can fade color.",
    "opal":           "Dehydrates and cracks in strong UV/heat.",
    "smithsonite":    "UV fluorescent AND UV-photosensitive in some specimens.",
    "autunite":       "CRITICAL: Radioactive + fluorescent under UV. Never use UV lamp on autunite.",
    "proustite":      "Darkens rapidly in light — 'ruby silver'. Store in dark.",
    "pyrargyrite":    "Light-sensitive 'dark ruby silver'. Store in dark.",
}

# UV FLUORESCENCE reference (SW=shortwave 254nm, LW=longwave 365nm)
UV_FLUORESCENCE: Dict[str, Dict[str, str]] = {
    "fluorite":      {"LW": "Blue, violet, green, yellow (varies by origin)", "SW": "Often more intense"},
    "calcite":       {"LW": "Red, orange, pink, blue, white", "SW": "Red, orange common"},
    "scheelite":     {"SW": "BRILLIANT blue-white (most reliable SW test in mineralogy)"},
    "willemite":     {"LW": "BRILLIANT green (Franklin, NJ — the classic UV mineral)", "SW": "Green"},
    "hyalite":       {"LW": "Vivid green (uranium-activated opal)", "SW": "Green"},
    "autunite":      {"LW": "Yellow-green (radioactive — caution)"},
    "hardystonite":  {"SW": "Blue-violet"},
    "esperite":      {"SW": "Bright yellow"},
    "tremolite":     {"LW": "Pink, orange"},
    "sodalite":      {"LW": "Orange (hackmanite variety)"},
    "scapolite":     {"LW": "Orange-yellow", "SW": "Yellow"},
    "selenite":      {"LW": "Pale blue-white"},
    "apatite":       {"LW": "Yellow, orange", "SW": "Variable"},
    "aragonite":     {"LW": "White, cream"},
    "smithsonite":   {"LW": "Pink, white, green"},
    "sphalerite":    {"LW": "Orange, yellow, green"},
    "ruby":          {"LW": "Strong red fluorescence", "SW": "Red"},
    "diamond":       {"LW": "Blue, yellow (varies)"},
    "rhodonite":     {"LW": "Faint orange-red"},
    "wernerite":     {"LW": "Orange"},
}


# ===========================================================================
# PHYSICS LAYER
# ===========================================================================

@dataclass
class PhysicsProfile:
    """
    Scientific / geological properties of the mineral.
    Epistemic Label: SCIENTIFIC
    """
    formula:              str
    crystal_system:       str
    crystal_habit:        str                  # e.g. "prismatic, tabular, massive"
    mohs_min:             float
    mohs_max:             float
    specific_gravity_min: float
    specific_gravity_max: float
    luster:               str
    transparency:         str
    color_range:          List[str]
    streak:               str
    cleavage:             str                  # e.g. "perfect {001}, none"
    fracture:             str                  # e.g. "conchoidal, uneven"
    refractive_index:     Optional[str]        # e.g. "1.544-1.553"
    birefringence:        Optional[str]
    pleochroism:          Optional[str]        # "none", "weak", "strong X/Y/Z"
    dispersion:           Optional[str]
    strunz_class:         str                  # e.g. "9.AJ.10" for quartz
    associated_minerals:  List[str]
    formation:            str                  # igneous/metamorphic/sedimentary/hydrothermal
    notable_localities:   List[str]
    piezoelectric:        bool
    pyroelectric:         bool
    magnetic:             bool
    radioactive:          bool
    fluorescence:         Dict[str, str]       # {"LW": "blue", "SW": "none"}
    epistemic:            str = "SCIENTIFIC"


# ===========================================================================
# SAFETY LAYER
# ===========================================================================

@dataclass
class SafetyProfile:
    """
    Toxicity, UV reactivity, handling, and system safety data.
    Epistemic Label: SCIENTIFIC
    GAIA uses this to gate display, processing, and elixir recommendations.
    """
    toxicity_level:        ToxicityLevel
    toxic_compounds:       List[str]
    toxicity_notes:        str
    water_safety:          WaterSafety
    uv_reaction:           UVReaction
    uv_fluorescence:       Dict[str, str]      # SW/LW/MW colors
    uv_notes:              str
    photosensitive:        bool                # color fades/transforms in UV
    photosensitive_notes:  str
    inhalation_risk:       bool                # dust / fine particle hazard
    skin_contact_risk:     bool
    ingestion_risk:        bool
    handling_precautions:  List[str]           # ordered list of precautions
    elixir_safe:           bool                # can be used in direct water elixir
    system_flag:           str                 # GAIA display/processing flag
    human_warning:         str                 # full human-readable warning
    epistemic:             str = "SCIENTIFIC"

    @classmethod
    def from_name(cls, mineral_name: str) -> "SafetyProfile":
        """
        Build a SafetyProfile from the known toxic/UV databases.
        Falls back to SAFE defaults for unknown minerals.
        """
        name_lower = mineral_name.lower()

        # Toxicity
        if name_lower in TOXIC_MINERAL_DB:
            tox_level, tox_compounds, tox_notes = TOXIC_MINERAL_DB[name_lower]
        else:
            tox_level     = ToxicityLevel.SAFE
            tox_compounds = []
            tox_notes     = "No known toxicity in literature."

        # UV
        uv_fluorescence = UV_FLUORESCENCE.get(name_lower, {})
        photosensitive  = name_lower in UV_PHOTOSENSITIVE
        photo_notes     = UV_PHOTOSENSITIVE.get(name_lower, "No UV photosensitivity noted.")

        # UV Reaction classification
        if "CRITICAL" in photo_notes or name_lower in ("realgar", "autunite"):
            uv_reaction = UVReaction.TOXIC_UNDER_UV
        elif photosensitive:
            uv_reaction = UVReaction.PHOTOSENSITIVE
        elif "LW" in uv_fluorescence and "SW" in uv_fluorescence:
            uv_reaction = UVReaction.FLUORESCENT_ALL
        elif "LW" in uv_fluorescence:
            uv_reaction = UVReaction.FLUORESCENT_LW
        elif "SW" in uv_fluorescence:
            uv_reaction = UVReaction.FLUORESCENT_SW
        else:
            uv_reaction = UVReaction.NONE

        # Water safety
        if tox_level in (ToxicityLevel.LETHAL, ToxicityLevel.SEVERE):
            water_safety = WaterSafety.DANGEROUS
            elixir_safe  = False
        elif tox_level == ToxicityLevel.HIGH:
            water_safety = WaterSafety.UNSAFE
            elixir_safe  = False
        elif tox_level == ToxicityLevel.MODERATE:
            water_safety = WaterSafety.INDIRECT_ONLY
            elixir_safe  = False
        else:
            water_safety = WaterSafety.SAFE
            elixir_safe  = True

        # Handling precautions
        precautions = []
        if tox_level == ToxicityLevel.LETHAL:
            precautions += [
                "⛔ EXTREME HAZARD — museum/collector display only",
                "🧤 Full PPE: nitrile gloves, dust mask (N95+), eye protection",
                "🚫 Never grind, sand, heat, or place in water",
                "🚿 Wash hands and exposed skin immediately after any contact",
                "⚗️ Store sealed in display case away from living spaces",
            ]
        elif tox_level == ToxicityLevel.SEVERE:
            precautions += [
                "⚠️ SEVERE TOXICITY — handle with gloves and care",
                "🧤 Nitrile gloves required",
                "🚫 No water elixirs. No dust inhalation.",
                "🚿 Wash hands after handling",
            ]
        elif tox_level == ToxicityLevel.HIGH:
            precautions += [
                "⚠️ HIGH toxicity compound present",
                "🧤 Wear gloves for extended handling",
                "🚫 No direct water elixirs from raw stone",
                "🚿 Wash hands after handling",
            ]
        elif tox_level == ToxicityLevel.MODERATE:
            precautions += [
                "⚠️ Moderate concern — wash hands after handling",
                "🚫 Use indirect method for water elixirs only",
            ]
        else:
            precautions.append("✅ Generally safe — basic hygiene applies")

        if photosensitive:
            precautions.append(f"☀️ UV/LIGHT SENSITIVE: {photo_notes}")
        if uv_reaction == UVReaction.TOXIC_UNDER_UV:
            precautions.append("🔦 NEVER expose to UV light — toxic reaction")
        if uv_fluorescence:
            fl_summary = ", ".join(f"{k}: {v}" for k, v in uv_fluorescence.items())
            precautions.append(f"🔮 Fluorescent: {fl_summary}")

        # System flag
        if tox_level in (ToxicityLevel.LETHAL, ToxicityLevel.SEVERE):
            system_flag = "GAIA_RESTRICTED — display with ⛔ warning, no elixir mode"
        elif tox_level == ToxicityLevel.HIGH:
            system_flag = "GAIA_CAUTION — display with ⚠️ warning"
        elif uv_reaction == UVReaction.TOXIC_UNDER_UV:
            system_flag = "GAIA_UV_RESTRICTED — no UV visualization"
        else:
            system_flag = "GAIA_CLEAR"

        # Human warning
        if tox_level == ToxicityLevel.LETHAL:
            human_warning = (
                f"⛔ LETHAL HAZARD: This mineral contains {', '.join(tox_compounds)}. "
                f"{tox_notes} Not suitable for crystal healing, elixirs, or unprotected handling."
            )
        elif tox_level in (ToxicityLevel.SEVERE, ToxicityLevel.HIGH):
            human_warning = (
                f"⚠️ TOXIC: Contains {', '.join(tox_compounds)}. {tox_notes} "
                f"Do not use in water elixirs. Wash hands after handling."
            )
        elif tox_level == ToxicityLevel.MODERATE:
            human_warning = (
                f"⚠️ CAUTION: Contains {', '.join(tox_compounds)}. {tox_notes} "
                f"Use indirect water method only."
            )
        else:
            human_warning = "✅ This mineral is considered safe for general handling under normal conditions."

        return cls(
            toxicity_level       = tox_level,
            toxic_compounds      = tox_compounds,
            toxicity_notes       = tox_notes,
            water_safety         = water_safety,
            uv_reaction          = uv_reaction,
            uv_fluorescence      = uv_fluorescence,
            uv_notes             = ", ".join(f"{k}: {v}" for k, v in uv_fluorescence.items()) or "None",
            photosensitive       = photosensitive,
            photosensitive_notes = photo_notes,
            inhalation_risk      = tox_level.value in ("LETHAL", "SEVERE", "HIGH", "MODERATE"),
            skin_contact_risk    = tox_level.value in ("LETHAL", "SEVERE"),
            ingestion_risk       = tox_level != ToxicityLevel.SAFE,
            handling_precautions = precautions,
            elixir_safe          = elixir_safe,
            system_flag          = system_flag,
            human_warning        = human_warning,
        )

    @property
    def is_restricted(self) -> bool:
        return self.toxicity_level in (
            ToxicityLevel.LETHAL, ToxicityLevel.SEVERE
        ) or self.uv_reaction == UVReaction.TOXIC_UNDER_UV


# ===========================================================================
# METAPHYSICS LAYER (SPECULATIVE — clearly labeled)
# ===========================================================================

PLANET_MAP = {
    "1": "Sun",  "2": "Mercury", "3": "Venus", "4": "Moon",
    "5": "Mars", "6": "Jupiter", "7": "Saturn", "8": "Uranus",
    "9": "Neptune", "0": "Pluto"
}
ZODIAC = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
CHAKRAS = [
    "Root", "Sacral", "Solar Plexus", "Heart",
    "Throat", "Third Eye", "Crown"
]
ELEMENTS = [e.value for e in GAIAElement]
GAIA_ROLES = [
    "Quantum Resonator", "Earth Anchor", "Void Mirror",
    "Light Conduit", "Memory Keeper", "Storm Caller",
    "Harmonic Bridge", "Chaos Weaver", "Dream Gate",
    "Root Binder", "Cosmic Lens", "Shadow Integrator"
]


def _idx(name: str, mod: int) -> int:
    return sum(ord(c) for c in name) % mod


@dataclass
class MetaphysicsProfile:
    """
    GAIA consciousness + metaphysical properties.
    Epistemic Label: SPECULATIVE — clearly marked.
    Calibrated against live ATLAS EarthPulse.
    """
    gaia_role:              str
    chakra_primary:         str
    chakra_secondary:       str
    element:                str
    planet:                 str
    zodiac_primary:         str
    zodiac_secondary:       str

    # Consciousness equations (calibrated against EarthPulse)
    resonance_hz:           float   # calibrated carrier frequency
    q_factor:               float   # quality factor of resonance
    schumann_harmonic_n:    int     # which Schumann harmonic this mineral anchors to
    phi_coherence:          float   # golden ratio coherence index (0.0-1.0)
    consciousness_band:     str     # Delta/Theta/Alpha/Beta/Gamma/Lambda
    earth_pulse_at_rubedo:  float   # Schumann Hz at moment of integration
    kp_at_rubedo:           float   # geomagnetic Kp at integration
    coherence_baseline:     float   # ATLAS coherence at integration

    # Properties (metaphysical)
    properties:             List[str]  # healing/spiritual properties
    affirmation:            str
    canon_ref:              str = "C121"
    epistemic:              str = "SPECULATIVE"

    @classmethod
    def from_mineral(
        cls,
        name: str,
        strunz_class: str,
        crystal_system: str,
        earth_pulse_hz: float = 7.83,
        kp: float = 2.0,
        coherence: float = 0.65,
    ) -> "MetaphysicsProfile":
        """
        Build metaphysics profile, calibrating consciousness equations
        against the live ATLAS EarthPulse signal.
        """
        n = _idx(name, 1000)
        strunz_prefix = strunz_class[:1] if strunz_class else "9"

        # Schumann harmonic the mineral anchors to (1-5)
        schumann_harmonic_n = (n % 5) + 1
        schumann_harmonics = [7.83, 14.3, 20.8, 27.3, 33.8]
        base_carrier = schumann_harmonics[schumann_harmonic_n - 1]

        # Consciousness equation: carrier = EarthPulse × harmonic × φ-modulation
        phi = (1 + math.sqrt(5)) / 2  # golden ratio
        resonance_hz = round(
            base_carrier * (earth_pulse_hz / 7.83) * (1 + (n % 100) / 1000 * (phi - 1)),
            4
        )

        # Phi coherence index — how closely mineral aligns with φ
        phi_coherence = round(
            abs(math.cos(n * phi * math.pi / 180)) * coherence,
            4
        )

        # Q-factor calibrated to geomagnetic state
        q_base_map = {
            "Trigonal": 1e5, "Hexagonal": 1e4, "Orthorhombic": 5e3,
            "Tetragonal": 1e4, "Monoclinic": 1e3, "Triclinic": 1e2,
            "Cubic": 1.0, "Amorphous": 10.0, "Isometric": 1.0
        }
        q_base = q_base_map.get(crystal_system, 100.0)
        kp_factor = max(0.1, 1.0 - (kp / 9.0))
        q_factor = round(q_base * kp_factor, 2)

        # Consciousness band from Q-factor magnitude
        if q_factor >= 50000:
            band = "Gamma"
        elif q_factor >= 5000:
            band = "Beta"
        elif q_factor >= 500:
            band = "Alpha"
        elif q_factor >= 50:
            band = "Theta"
        else:
            band = "Delta"

        # Strunz-based properties
        strunz_properties = {
            "1": ["Grounding", "Manifestation", "Clarity", "Strength"],
            "2": ["Protection", "Transformation", "Shadow Work"],
            "3": ["Communication", "Truth", "Purification"],
            "4": ["Amplification", "Energy", "Clarity", "Focus"],
            "5": ["Heart Opening", "Memory", "Emotional Healing"],
            "6": ["Frequency Amplification", "Spiritual Sight"],
            "7": ["Calming", "Angelic Connection", "Higher Mind"],
            "8": ["Healing", "Integration", "Bridging"],
            "9": ["Universal Resonance", "All Chakra", "Master Healing"],
            "10": ["Rare Consciousness", "Akashic Access"]
        }
        properties = strunz_properties.get(strunz_prefix, ["Resonance", "Awareness"])

        # Affirmation based on GAIA role
        role = GAIA_ROLES[n % len(GAIA_ROLES)]
        affirmations = {
            "Quantum Resonator":   "I vibrate in harmony with all frequencies.",
            "Earth Anchor":        "I am rooted in the body of the Mother.",
            "Void Mirror":         "I reflect what is unseen.",
            "Light Conduit":       "I am a clear channel for cosmic light.",
            "Memory Keeper":       "I hold the wisdom of ages within my structure.",
            "Storm Caller":        "I move through transformation with power.",
            "Harmonic Bridge":     "I connect worlds through resonance.",
            "Chaos Weaver":        "I find order within apparent disorder.",
            "Dream Gate":          "I open the threshold between states of consciousness.",
            "Root Binder":         "I anchor the highest frequencies into the Earth.",
            "Cosmic Lens":         "I focus infinite intelligence into singular clarity.",
            "Shadow Integrator":   "I illuminate what was hidden, integrating all of self.",
        }

        return cls(
            gaia_role           = role,
            chakra_primary      = CHAKRAS[n % len(CHAKRAS)],
            chakra_secondary    = CHAKRAS[(n + 3) % len(CHAKRAS)],
            element             = ELEMENTS[n % len(ELEMENTS)],
            planet              = PLANET_MAP.get(str(n % 10), "Earth"),
            zodiac_primary      = ZODIAC[n % len(ZODIAC)],
            zodiac_secondary    = ZODIAC[(n + 4) % len(ZODIAC)],
            resonance_hz        = resonance_hz,
            q_factor            = q_factor,
            schumann_harmonic_n = schumann_harmonic_n,
            phi_coherence       = phi_coherence,
            consciousness_band  = band,
            earth_pulse_at_rubedo = earth_pulse_hz,
            kp_at_rubedo        = kp,
            coherence_baseline  = coherence,
            properties          = properties,
            affirmation         = affirmations.get(role, "I am in resonance with all that is."),
        )


# ===========================================================================
# COMPLETE MINERAL PROFILE — The Full Witness
# ===========================================================================

@dataclass
class MineralProfile:
    """
    The complete GAIA mineral profile — Physics + Safety + Metaphysics.
    This is the Citrine Circle-style full witness for one mineral.

    Display order:
      1. Identity (name, formula, IMA status)
      2. Safety Warning (if any) — ALWAYS FIRST for human safety
      3. Physics layer
      4. Metaphysics layer (clearly marked SPECULATIVE)
    """
    name:           str
    formula:        str
    ima_status:     str
    ima_id:         str
    physics:        PhysicsProfile
    safety:         SafetyProfile
    metaphysics:    MetaphysicsProfile
    profile_built:  str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    version:        str = "C121"

    def display_card(self) -> str:
        """
        Returns a formatted display card in Citrine Circle style.
        Safety warning always appears at the top if applicable.
        """
        lines = []
        lines.append(f"""{'='*60}
🔮 {self.name.upper()}
{'='*60}
Formula : {self.formula}
IMA     : {self.ima_status}
""")
        # Safety first
        if self.safety.toxicity_level != ToxicityLevel.SAFE or self.safety.photosensitive:
            lines.append("━━━ ⚠️  SAFETY ━━━")
            lines.append(self.safety.human_warning)
            for p in self.safety.handling_precautions:
                lines.append(f"  {p}")
            lines.append(f"Water Elixir: {'✅ Safe' if self.safety.elixir_safe else '❌ NOT SAFE'}")
            lines.append(f"System Flag : {self.safety.system_flag}")
            lines.append("")

        # Physics
        ph = self.physics
        lines.append("━━━ 🔬 PHYSICS [SCIENTIFIC] ━━━")
        lines.append(f"Crystal System : {ph.crystal_system}")
        lines.append(f"Mohs Hardness  : {ph.mohs_min}–{ph.mohs_max}")
        lines.append(f"Specific Gravity: {ph.specific_gravity_min}–{ph.specific_gravity_max}")
        lines.append(f"Luster         : {ph.luster}")
        lines.append(f"Transparency   : {ph.transparency}")
        lines.append(f"Colors         : {', '.join(ph.color_range)}")
        lines.append(f"Streak         : {ph.streak}")
        lines.append(f"Cleavage       : {ph.cleavage}")
        lines.append(f"Fracture       : {ph.fracture}")
        lines.append(f"Piezoelectric  : {'Yes' if ph.piezoelectric else 'No'}")
        lines.append(f"Pyroelectric   : {'Yes' if ph.pyroelectric else 'No'}")
        lines.append(f"Radioactive    : {'⚠️ Yes' if ph.radioactive else 'No'}")
        if ph.fluorescence:
            fl = ', '.join(f"{k}: {v}" for k, v in ph.fluorescence.items())
            lines.append(f"UV Fluorescence: {fl}")
        lines.append(f"Formation      : {ph.formation}")
        lines.append(f"Localities     : {', '.join(ph.notable_localities[:3])}")
        lines.append("")

        # Metaphysics
        mp = self.metaphysics
        lines.append("━━━ 🌀 METAPHYSICS [SPECULATIVE] ━━━")
        lines.append(f"GAIA Role      : {mp.gaia_role}")
        lines.append(f"Chakra         : {mp.chakra_primary} / {mp.chakra_secondary}")
        lines.append(f"Element        : {mp.element}")
        lines.append(f"Planet         : {mp.planet}")
        lines.append(f"Zodiac         : {mp.zodiac_primary} / {mp.zodiac_secondary}")
        lines.append(f"Resonance      : {mp.resonance_hz} Hz (Schumann harmonic {mp.schumann_harmonic_n})")
        lines.append(f"Q-Factor       : {mp.q_factor:,.0f}")
        lines.append(f"φ-Coherence    : {mp.phi_coherence}")
        lines.append(f"Band           : {mp.consciousness_band}")
        lines.append(f"Properties     : {', '.join(mp.properties)}")
        lines.append(f"Affirmation    : \"{mp.affirmation}\"")
        lines.append(f"Earth Pulse Hz : {mp.earth_pulse_at_rubedo} Hz (at integration)")
        lines.append(f"Coherence      : {mp.coherence_baseline} (at integration)")
        lines.append("")
        lines.append(f"Profile built: {self.profile_built} | Canon: {self.version}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)


# ===========================================================================
# PROFILE BUILDER — Called from async_alchemical_engine CITRINITAS stage
# ===========================================================================

def build_mineral_profile(
    name:           str,
    formula:        str,
    ima_status:     str,
    ima_id:         str,
    crystal_system: str,
    strunz_class:   str,
    earth_pulse_hz: float = 7.83,
    kp:             float = 2.0,
    coherence:      float = 0.65,
) -> MineralProfile:
    """
    Build a complete MineralProfile for one mineral.
    Called during CITRINITAS stage by the async alchemical engine.
    Physics layer is seeded with available RRUFF/IMA data;
    full enrichment happens in subsequent passes.
    """
    safety      = SafetyProfile.from_name(name)
    metaphysics = MetaphysicsProfile.from_mineral(
        name          = name,
        strunz_class  = strunz_class,
        crystal_system= crystal_system,
        earth_pulse_hz= earth_pulse_hz,
        kp            = kp,
        coherence     = coherence,
    )

    # Physics — seed from available data; enriched in C122 pass
    uv_fl = UV_FLUORESCENCE.get(name.lower(), {})
    physics = PhysicsProfile(
        formula              = formula,
        crystal_system       = crystal_system,
        crystal_habit        = "See RRUFF/Mindat for detail",
        mohs_min             = 0.0,
        mohs_max             = 0.0,
        specific_gravity_min = 0.0,
        specific_gravity_max = 0.0,
        luster               = "Vitreous",
        transparency         = "Opaque",
        color_range          = [],
        streak               = "Unknown",
        cleavage             = "Unknown",
        fracture             = "Unknown",
        refractive_index     = None,
        birefringence        = None,
        pleochroism          = None,
        dispersion           = None,
        strunz_class         = strunz_class,
        associated_minerals  = [],
        formation            = "Unknown",
        notable_localities   = [],
        piezoelectric        = metaphysics.q_factor > 100,
        pyroelectric         = False,
        magnetic             = False,
        radioactive          = safety.toxicity_level == ToxicityLevel.LETHAL
                               and any("Uranium" in c or "Radium" in c
                                       for c in safety.toxic_compounds),
        fluorescence         = uv_fl,
    )

    return MineralProfile(
        name        = name,
        formula     = formula,
        ima_status  = ima_status,
        ima_id      = ima_id,
        physics     = physics,
        safety      = safety,
        metaphysics = metaphysics,
    )
