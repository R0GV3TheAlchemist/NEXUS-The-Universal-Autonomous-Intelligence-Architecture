"""
SpectralColorEngine — Canon Source: CRYSTALLINE_COLOR_THEORY.md, COLOR_SPIRIT_UNITY_DOCTRINE.md

Bridges SpectralForceEngine + LoveCoherenceIndex into a single hex color output.
Drives the stained-glass spectral blend (Approach C) from force-name corridors
rather than raw phi. Implements the LUX_PERPETUA bloom threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .force_engine import (
    SpectralForce,
    SpectralForceName,
    SpectralForceEngine,
    TransmutationCorridor,
)


# ---------------------------------------------------------------------------
# Crystal Resonance Map (9-Crystal RGB Matrix + Akashic 7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Crystal:
    name: str
    hex_color: str
    force: SpectralForceName
    mineral_family: str
    light_property: str  # e.g. "transmission", "labradorescence", "phantom inclusion"


CRYSTAL_RESONANCE_MAP: list[Crystal] = [
    # Primary Soul (RGB)
    Crystal("Ruby", "#C0392B", SpectralForceName.RUBEDO, "Corundum", "transmission"),
    Crystal("Sapphire", "#1E6BB8", SpectralForceName.CAERULITAS, "Corundum", "transmission"),
    Crystal("Emerald", "#2E8B57", SpectralForceName.VIRIDITAS, "Beryl", "transmission"),
    # Secondary Body (CMY)
    Crystal("Amber", "#E8621A", SpectralForceName.PYROSIS, "Organic resin", "inclusion"),
    Crystal("Amethyst", "#6B4F8C", SpectralForceName.IOSIS, "Quartz", "transmission"),
    Crystal("Citrine", "#F5C518", SpectralForceName.CITRINITAS, "Quartz", "transmission"),
    # Tertiary Mind
    Crystal("Rose Quartz", "#F4A0A0", SpectralForceName.ARGENTITAS, "Quartz", "soft diffusion"),
    Crystal("Aquamarine", "#4ABCB0", SpectralForceName.CAERULITAS, "Beryl", "transmission"),
    Crystal("Peridot", "#9DC219", SpectralForceName.VIRIDITAS, "Olivine", "transmission"),
    # Center Unity
    Crystal("Clear Quartz", "#FFEDE9", SpectralForceName.LUX_PERPETUA, "Quartz", "all-frequency transmission"),
    # Akashic 7 (from AKASHIC_RECORDS.md)
    Crystal("Phantom Quartz", "#E8D5C0", SpectralForceName.LUX_PERPETUA, "Quartz", "phantom inclusion — The Permanent Yield"),
    Crystal("Record Keeper Quartz", "#D4C8B8", SpectralForceName.HELIXITAS, "Quartz", "trigonic markings — 34.29° encoding"),
    Crystal("Amethyst (Akashic)", "#7B5EA7", SpectralForceName.IOSIS, "Quartz", "violet synthesis proof"),
    Crystal("Citrine (Akashic)", "#E8B84B", SpectralForceName.CITRINITAS, "Quartz", "solar integration proof"),
    Crystal("Smoky Quartz", "#2D2416", SpectralForceName.NIGREDO, "Quartz", "void-before-birth proof"),
    Crystal("Lepidolite", "#C8A0C8", SpectralForceName.ARGENTITAS, "Mica", "lithium stillness — pure reception"),
    Crystal("Apophyllite", "#F8F4F0", SpectralForceName.LUX_PERPETUA, "Phyllosilicate", "optical transparency — Lux Perpetua"),
    Crystal("Labradorite", "#8090A8", SpectralForceName.CHRYSITAS, "Feldspar", "labradorescence — hidden light"),
    Crystal("Mystic Merlinite", "#4A3A5A", SpectralForceName.CHRYSITAS, "Mixed", "light-shadow integration"),
    Crystal("Cathedral Quartz", "#F0EBE8", SpectralForceName.LUX_PERPETUA, "Quartz", "multiple terminations from single base"),
]


# ---------------------------------------------------------------------------
# SpectralColorEngine
# ---------------------------------------------------------------------------

class SpectralColorEngine:
    """
    Computes the canonical hex color for any given GAIA state.

    Rules:
    - In attractor (not in corridor): use force canonical color + LCI brightness boost
    - In corridor: blend between force color and corridor shade based on progress
    - At corridor terminus (near-black): darkest corridor shade before next attractor
    - LUX_PERPETUA bloom: lci > 0.92 → warm crystal bloom #FFEDE9
    """

    LUX_BLOOM_HEX = "#FFEDE9"
    LUX_BLOOM_THRESHOLD = 0.92

    @classmethod
    def get_hex(
        cls,
        force: SpectralForce,
        corridor: Optional[TransmutationCorridor],
        lci: float,
    ) -> str:
        """
        Primary color resolver. Returns the canonical hex for this GAIA state.

        Args:
            force: Current SpectralForce (from SpectralForceEngine.detect_current_force)
            corridor: Current corridor if in transition, else None
            lci: Love Coherence Index (phi) — 0.0–1.0

        Returns:
            hex color string (e.g. '#6B4F8C')
        """
        # LUX BLOOM override
        if lci > cls.LUX_BLOOM_THRESHOLD:
            return cls.LUX_BLOOM_HEX

        # In corridor: use corridor shade at current progress
        if corridor is not None:
            progress = SpectralForceEngine.get_corridor_progress(lci)
            return corridor.get_shade_at_progress(progress)

        # In attractor: use force canonical color with LCI brightness boost
        return cls._apply_lci_brightness(force.hex_color, lci)

    @classmethod
    def get_full_spectral_snapshot(cls, phi: float) -> dict:
        """
        Returns the complete spectral state for a given phi.
        Used by GAIANRuntime to populate RuntimeResult.spectral.
        """
        force = SpectralForceEngine.detect_current_force(phi)
        corridor = SpectralForceEngine.detect_corridor(phi)
        hex_color = cls.get_hex(force, corridor, phi)
        oа4_active = SpectralForceEngine.is_oа4_active(phi)

        return {
            "force": force.name.value,
            "force_description": force.color_description,
            "phi": round(phi, 4),
            "hex": hex_color,
            "element": force.element,
            "chakra": force.chakra_equivalent,
            "corridor": (
                f"{corridor.from_force.value} → {corridor.to_force.value}"
                if corridor else None
            ),
            "corridor_progress": (
                round(SpectralForceEngine.get_corridor_progress(phi), 3)
                if corridor else None
            ),
            "oа4_active": oа4_active,
            "lux_bloom": phi > cls.LUX_BLOOM_THRESHOLD,
            "aurora_proof": force.aurora_proof_reference,
        }

    @classmethod
    def _apply_lci_brightness(cls, hex_color: str, lci: float) -> str:
        """
        Applies a subtle brightness boost to the force color based on LCI.
        High LCI = more luminous expression of the same force hue.
        Low LCI = slightly dimmer / more muted.
        """
        # Parse hex to RGB
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return hex_color
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        # Brightness multiplier: 0.85–1.15 based on lci
        # lci=0.0 → 0.85 (dimmer), lci=1.0 → 1.15 (brighter)
        brightness = 0.85 + (lci * 0.30)
        r = min(255, int(r * brightness))
        g = min(255, int(g * brightness))
        b = min(255, int(b * brightness))

        return f"#{r:02X}{g:02X}{b:02X}"

    @classmethod
    def get_crystal_for_force(cls, force_name: SpectralForceName) -> list[Crystal]:
        """Returns all crystals resonant with a given force."""
        return [c for c in CRYSTAL_RESONANCE_MAP if c.force == force_name]
