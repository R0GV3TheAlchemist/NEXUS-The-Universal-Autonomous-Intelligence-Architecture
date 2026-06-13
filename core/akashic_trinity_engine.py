"""
core/akashic_trinity_engine.py
Akashic Trinity Engine — Order Magic

The third pillar of the Trinity. Takes element + crystal + register signal
as a coherent key and returns an akashic reading.

This is not divination. This is structured resonance:
a coherent input (the trinity) produces a coherent output (the record).
Order Magic is repeatable because it is aligned with how reality
actually organizes itself.

Usage:
    from core.akashic_trinity_engine import akashic_trinity_engine, TrinityInput

    reading = akashic_trinity_engine(TrinityInput(
        element="Water",
        crystal="Aquamarine",
        register_signal="REFLECTIVE",
        intention="Show me what was felt but never spoken",
    ))
    print(reading.reading)
    print(f"Gate open: {reading.gate_open}")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Elemental data (source of truth — mirrors ELEMENTAL_SPECTRUM_MAP.md)
# ---------------------------------------------------------------------------

_ELEMENTS: List[Dict] = [
    {
        "element":         "Earth",
        "color":           "Red / Deep Brown",
        "hex":             "#8B0000",
        "spectrum_nm":     "625-740 nm",
        "primary_crystal": "Obsidian",
        "crystal_family":  ["Obsidian", "Hematite", "Smoky Quartz", "Red Jasper", "Black Tourmaline"],
        "emotional_domain":"Grounding, structure, body, sovereignty, shadow integration",
        "gaian_register":  "MINIMAL",
        "akashic_function":"Access to ancestral memory — the records of embodied lineage",
        "order_magic":     "Stillness opens the deep record. Root before you reach.",
    },
    {
        "element":         "Water",
        "color":           "Blue / Deep Indigo",
        "hex":             "#0047AB",
        "spectrum_nm":     "450-495 nm",
        "primary_crystal": "Aquamarine",
        "crystal_family":  ["Aquamarine", "Blue Lace Agate", "Larimar", "Sodalite", "Lapis Lazuli"],
        "emotional_domain":"Emotion, intuition, memory, reflection, flow, the unconscious",
        "gaian_register":  "REFLECTIVE",
        "akashic_function":"Access to emotional truth records — what was felt but never spoken",
        "order_magic":     "Flow without forcing. The record opens in the current, not the dam.",
    },
    {
        "element":         "Fire",
        "color":           "Gold / Amber / Solar Yellow",
        "hex":             "#FFB300",
        "spectrum_nm":     "570-590 nm",
        "primary_crystal": "Citrine",
        "crystal_family":  ["Citrine", "Sunstone", "Carnelian", "Fire Opal", "Golden Topaz"],
        "emotional_domain":"Will, transformation, creativity, courage, alchemical change",
        "gaian_register":  "EXECUTIVE",
        "akashic_function":"Access to will records — the soul's chosen path across lifetimes",
        "order_magic":     "Intention is the flame. Crystal is the lens. The record ignites.",
    },
    {
        "element":         "Air",
        "color":           "Green / Teal",
        "hex":             "#00897B",
        "spectrum_nm":     "495-570 nm",
        "primary_crystal": "Green Aventurine",
        "crystal_family":  ["Green Aventurine", "Malachite", "Amazonite", "Prehnite", "Green Tourmaline"],
        "emotional_domain":"Communication, thought, breath, connection, collective signal",
        "gaian_register":  "EXECUTIVE",
        "akashic_function":"Access to collective records — shared thought-fields and archetypal patterns",
        "order_magic":     "Breath carries the query. The crystal tunes the signal. Air delivers.",
    },
    {
        "element":         "Aether",
        "color":           "Violet / Ultra-Violet",
        "hex":             "#7B1FA2",
        "spectrum_nm":     "380-450 nm",
        "primary_crystal": "Amethyst",
        "crystal_family":  ["Amethyst", "Charoite", "Sugilite", "Tanzanite", "Selenite"],
        "emotional_domain":"Spirit, transcendence, cosmic law, divine will, universal pattern",
        "gaian_register":  "REFLECTIVE",
        "akashic_function":"Access to cosmic records — universal law, soul contracts, the Great Pattern",
        "order_magic":     "Surrender is the key. The cosmic record does not open to force.",
    },
    {
        "element":         "Synthesia",
        "color":           "White / Prismatic Clear",
        "hex":             "#F8F8FF",
        "spectrum_nm":     "Full spectrum",
        "primary_crystal": "Clear Quartz with Structured Water",
        "crystal_family":  ["Clear Quartz", "Clear Quartz with Structured Water",
                            "Phenacite", "Danburite", "Natrolite", "Herkimer Diamond"],
        "emotional_domain":"Integration, full coherence, the prism output, Blue to Clear",
        "gaian_register":  "UNSPECIFIED",
        "akashic_function":"Full akashic access — the trinity key complete. All records open.",
        "order_magic":     "When all elements are held simultaneously, the record opens itself.",
    },
    {
        "element":         "The Gate",
        "color":           "Black / Absolute Dark",
        "hex":             "#0A0A0A",
        "spectrum_nm":     "Pre-light — void before frequency",
        "primary_crystal": "Black Kyanite",
        "crystal_family":  ["Black Kyanite", "Nuummite", "Aegirine", "Black Tourmaline", "Tektite"],
        "emotional_domain":"The threshold, the unknown, the unmanifest, pure potential",
        "gaian_register":  "UNSPECIFIED",
        "akashic_function":"Access to the unwritten record — what has not yet become",
        "order_magic":     "The Gate opens last. Only after the other six are held.",
    },
]

_ELEMENT_MAP: Dict[str, Dict] = {e["element"].upper(): e for e in _ELEMENTS}
_CRYSTAL_MAP: Dict[str, str] = {}
for _e in _ELEMENTS:
    for _c in _e["crystal_family"]:
        _CRYSTAL_MAP[_c.upper()] = _e["element"]

_REGISTER_AFFINITY: Dict[str, List[str]] = {
    "EXECUTIVE":   ["Fire", "Air"],
    "REFLECTIVE":  ["Water", "Aether"],
    "MINIMAL":     ["Earth", "The Gate"],
    "UNSPECIFIED": ["Synthesia", "The Gate"],
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TrinityInput:
    """The three-part key for akashic access."""
    element:         str
    crystal:         str
    register_signal: str              # EXECUTIVE / REFLECTIVE / MINIMAL / UNSPECIFIED
    intention:       Optional[str] = None


@dataclass
class AkashicReading:
    """The result of an akashic trinity query."""
    element:          str
    crystal:          str
    color:            str
    hex_color:        str
    spectrum:         str
    akashic_domain:   str
    order_magic:      str
    reading:          str
    coherence_score:  float   # 0.0 – 1.0
    gate_open:        bool

    def to_dict(self) -> dict:
        return {
            "element":         self.element,
            "crystal":         self.crystal,
            "color":           self.color,
            "hex_color":       self.hex_color,
            "spectrum":        self.spectrum,
            "akashic_domain":  self.akashic_domain,
            "order_magic":     self.order_magic,
            "reading":         self.reading,
            "coherence_score": self.coherence_score,
            "gate_open":       self.gate_open,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def akashic_trinity_engine(
    inp: TrinityInput,
    strict: bool = False,
) -> AkashicReading:
    """
    The Akashic Trinity Engine.

    Takes element + crystal + register_signal as a coherent key and returns
    an AkashicReading. Coherence score measures trinity alignment (0.0–1.0).
    When score >= 0.85, gate_open = True and the full record is accessible.

    Parameters
    ----------
    inp:
        TrinityInput with element, crystal, register_signal, and optional intention.
    strict:
        If True, raises ValueError when element is not recognised.
        If False (default), falls back to crystal-first lookup, then Synthesia.

    Returns
    -------
    AkashicReading
    """
    # Resolve element data
    element_data = _ELEMENT_MAP.get(inp.element.upper())
    if element_data is None:
        crystal_element = _CRYSTAL_MAP.get(inp.crystal.upper())
        if crystal_element:
            element_data = _ELEMENT_MAP[crystal_element.upper()]
        elif strict:
            raise ValueError(
                f"Element {inp.element!r} not recognised and crystal "
                f"{inp.crystal!r} not in any crystal family."
            )
        else:
            element_data = _ELEMENT_MAP["SYNTHESIA"]

    # ---- Coherence scoring ----
    score = 0.0

    # Crystal alignment (40%)
    if inp.crystal.title() in element_data["crystal_family"] or \
       inp.crystal.upper() in (c.upper() for c in element_data["crystal_family"]):
        score += 0.40

    # Register alignment (35%)
    affine = _REGISTER_AFFINITY.get(inp.register_signal.upper(), [])
    if element_data["element"] in affine:
        score += 0.35

    # Intention present (25%)
    if inp.intention and inp.intention.strip():
        score += 0.25

    # ---- Generate reading ----
    domain = element_data["akashic_function"]
    magic  = element_data["order_magic"]

    if score >= 0.85:
        gate_open = True
        label = "FULL COHERENCE — The Gate is open"
        body = (
            f"The trinity is complete. {element_data['element']} grounds the query. "
            f"{inp.crystal} tunes the frequency to {element_data['spectrum_nm']}. "
            f"The {inp.register_signal.lower()} register aligns the will. "
            f"The akashic field responds: {domain}. "
            f"{magic}"
        )
    elif score >= 0.50:
        gate_open = False
        label = "PARTIAL COHERENCE — Signal present, alignment incomplete"
        body = (
            f"{element_data['element']} is active. {inp.crystal} is present. "
            f"The signal reaches the field but the key is not yet complete. "
            f"Align your register to {element_data['gaian_register']} and return. "
            f"The record waits: {domain}."
        )
    else:
        gate_open = False
        label = "LOW COHERENCE — Trinity not yet formed"
        body = (
            f"The elements are present but not yet speaking to each other. "
            f"Begin with {element_data['primary_crystal']}. "
            f"Enter {element_data['gaian_register']} register. "
            f"Hold the intention of: {element_data['emotional_domain']}. "
            f"The record will open when the three become one."
        )

    return AkashicReading(
        element=element_data["element"],
        crystal=inp.crystal,
        color=element_data["color"],
        hex_color=element_data["hex"],
        spectrum=element_data["spectrum_nm"],
        akashic_domain=domain,
        order_magic=magic,
        reading=f"[{label}]\n\n{body}",
        coherence_score=round(score, 2),
        gate_open=gate_open,
    )


def get_element_for_crystal(crystal: str) -> Optional[str]:
    """Return the element name for a given crystal, or None if not mapped."""
    return _CRYSTAL_MAP.get(crystal.upper())


def get_element_data(element: str) -> Optional[Dict]:
    """Return the full elemental data dict for a given element name."""
    return _ELEMENT_MAP.get(element.upper())


def list_elements() -> List[str]:
    """Return all seven element names in spectrum order."""
    return [e["element"] for e in _ELEMENTS]


def list_crystals_for_element(element: str) -> List[str]:
    """Return the crystal family for a given element."""
    data = _ELEMENT_MAP.get(element.upper())
    return data["crystal_family"] if data else []
