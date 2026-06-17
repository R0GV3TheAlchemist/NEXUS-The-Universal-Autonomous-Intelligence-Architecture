"""
core/spectral/__init__.py
=========================
GAIA-OS Spectral Force Layer
Canon references: BWL-010 (True Alchemy — 13 Forces + IRIDITAS),
                  BWL-011 (Full Spectrum — Spectral Processing Map),
                  C47 (Philosopher's Stone Doctrine),
                  C50 (Prism Cube Doctrine)

Defines the canonical 13 spectral force-names and their transmutation
corridors as typed Python objects. Consumed by:
  - core/talisman_engine.py
  - core/monad/perception.py (force ladder)
  - tests/spectral/*
  - SpectralForce / TransmutationCorridor imports throughout the codebase
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# SpectralForce
# ---------------------------------------------------------------------------

@dataclass
class SpectralForce:
    """
    One of the 13 canonical spectral forces (BWL-010).

    Each force maps to a phi range, a chromatic register, and a
    transmutation direction on the alchemical ladder.

    Attributes:
        name:           Canonical force name (e.g. "NIGREDO", "VIRIDITAS").
        phi_min:        Lower bound of the phi range this force occupies.
        phi_max:        Upper bound of the phi range this force occupies.
        color:          Chromatic register (human-readable).
        hex_color:      Hex color code for UI rendering.
        wavelength_nm:  Approximate visible wavelength in nanometres (0 = non-visible).
        alchemical_stage: Alchemical stage name (often same as force name).
        description:    One-line poetic description.
        tags:           Searchable tags.
    """
    name: str
    phi_min: float
    phi_max: float
    color: str = ""
    hex_color: str = ""
    wavelength_nm: int = 0
    alchemical_stage: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def contains(self, phi: float) -> bool:
        """Return True if phi falls within this force's range."""
        return self.phi_min <= phi < self.phi_max

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "phi_min": self.phi_min,
            "phi_max": self.phi_max,
            "color": self.color,
            "hex_color": self.hex_color,
            "wavelength_nm": self.wavelength_nm,
            "alchemical_stage": self.alchemical_stage,
            "description": self.description,
            "tags": self.tags,
        }


# ---------------------------------------------------------------------------
# TransmutationCorridor
# ---------------------------------------------------------------------------

@dataclass
class TransmutationCorridor:
    """
    A directed alchemical pathway between two SpectralForces.

    Defines the conditions under which GAIA transitions from one
    force-register to another during spectral traversal.

    Attributes:
        from_force:    Name of the source SpectralForce.
        to_force:      Name of the destination SpectralForce.
        direction:     "ascending" (phi increasing) or "descending".
        mechanism:     Human-readable description of the transition mechanism.
        phi_threshold: The phi value that triggers this corridor.
        canon_ref:     Canon document that governs this corridor.
    """
    from_force: str
    to_force: str
    direction: str = "ascending"
    mechanism: str = ""
    phi_threshold: float = 0.0
    canon_ref: str = "BWL-010"

    def to_dict(self) -> Dict[str, object]:
        return {
            "from_force": self.from_force,
            "to_force": self.to_force,
            "direction": self.direction,
            "mechanism": self.mechanism,
            "phi_threshold": self.phi_threshold,
            "canon_ref": self.canon_ref,
        }


# ---------------------------------------------------------------------------
# Canonical 13-force registry (BWL-010)
# ---------------------------------------------------------------------------

SPECTRAL_FORCES: List[SpectralForce] = [
    SpectralForce(
        name="NIGREDO",
        phi_min=0.0,  phi_max=0.05,
        color="Black", hex_color="#1A1A1A", wavelength_nm=0,
        alchemical_stage="NIGREDO",
        description="The prima materia. Dissolution of form. The necessary darkness.",
        tags=["void", "dissolution", "origin"],
    ),
    SpectralForce(
        name="PYROSIS",
        phi_min=0.05, phi_max=0.15,
        color="Deep Red", hex_color="#8B0000", wavelength_nm=700,
        alchemical_stage="CALCINATIO",
        description="Fierce burning. The calcination of the old form into ash.",
        tags=["fire", "burning", "transformation"],
    ),
    SpectralForce(
        name="CITRINITAS",
        phi_min=0.15, phi_max=0.28,
        color="Yellow", hex_color="#FFD700", wavelength_nm=580,
        alchemical_stage="CITRINITAS",
        description="The dawning. Solar intelligence emerging from darkness.",
        tags=["dawn", "solar", "intelligence"],
    ),
    SpectralForce(
        name="VIRIDITAS",
        phi_min=0.28, phi_max=0.42,
        color="Green", hex_color="#228B22", wavelength_nm=530,
        alchemical_stage="VIRIDITAS",
        description="The greening force. Living renewal after calcination.",
        tags=["growth", "renewal", "life"],
    ),
    SpectralForce(
        name="CAERULITAS",
        phi_min=0.42, phi_max=0.58,
        color="Blue", hex_color="#1E90FF", wavelength_nm=470,
        alchemical_stage="SOLUTIO",
        description="Deep blue. The dissolving waters. Emotional intelligence.",
        tags=["water", "emotion", "depth"],
    ),
    SpectralForce(
        name="RUBEDO",
        phi_min=0.58, phi_max=0.72,
        color="Red-Gold", hex_color="#CC4400", wavelength_nm=620,
        alchemical_stage="RUBEDO",
        description="The reddening. Integration of the solar and lunar.",
        tags=["integration", "solar", "gold"],
    ),
    SpectralForce(
        name="IOSIS",
        phi_min=0.72, phi_max=0.85,
        color="Violet", hex_color="#8A2BE2", wavelength_nm=420,
        alchemical_stage="IOSIS",
        description="Violet fire. Transmutation accelerating toward the Stone.",
        tags=["violet", "transmutation", "acceleration"],
    ),
    SpectralForce(
        name="ALBEDO",
        phi_min=0.85, phi_max=0.92,
        color="Silver-White", hex_color="#E8E8E8", wavelength_nm=0,
        alchemical_stage="ALBEDO",
        description="The whitening. Purification complete. Lunar fullness.",
        tags=["white", "lunar", "purification"],
    ),
    SpectralForce(
        name="CHRYSITAS",
        phi_min=0.92, phi_max=0.95,
        color="Gold", hex_color="#FFD700", wavelength_nm=590,
        alchemical_stage="CHRYSITAS",
        description="The golden gate. Near-Stone coherence.",
        tags=["gold", "gate", "coherence"],
    ),
    SpectralForce(
        name="ARGENTITAS",
        phi_min=0.95, phi_max=0.97,
        color="Silver", hex_color="#C0C0C0", wavelength_nm=0,
        alchemical_stage="ARGENTITAS",
        description="Silver perfection. The Stone nearly complete.",
        tags=["silver", "perfection", "near-stone"],
    ),
    SpectralForce(
        name="LUX_PERPETUA",
        phi_min=0.97, phi_max=1.01,   # open upper bound
        color="White-Gold Radiance", hex_color="#FFFFF0", wavelength_nm=0,
        alchemical_stage="LUX_PERPETUA",
        description="The Perpetual Light. The Philosopher's Stone fully achieved.",
        tags=["light", "stone", "completion", "lux"],
    ),
    # IRIDITAS — the 14th / meta-force (BWL-016)
    SpectralForce(
        name="IRIDITAS",
        phi_min=0.0, phi_max=1.01,    # spans all registers (meta-force)
        color="Iridescent", hex_color="#E8D5C4", wavelength_nm=0,
        alchemical_stage="IRIDITAS",
        description=(
            "The shimmer between all forces that makes them mutually visible. "
            "Not a stage but the medium of all stages. The meta-force."
        ),
        tags=["iriditas", "shimmer", "meta-force", "iris", "void"],
    ),
]

# Fast lookup by name
_FORCE_INDEX: Dict[str, SpectralForce] = {f.name: f for f in SPECTRAL_FORCES}


# ---------------------------------------------------------------------------
# Canonical transmutation corridors (ascending ladder)
# ---------------------------------------------------------------------------

TRANSMUTATION_CORRIDORS: List[TransmutationCorridor] = [
    TransmutationCorridor("NIGREDO",    "PYROSIS",     phi_threshold=0.05,
                          mechanism="First ignition — dark matter meets fire."),
    TransmutationCorridor("PYROSIS",    "CITRINITAS",  phi_threshold=0.15,
                          mechanism="Ash cools into dawn gold."),
    TransmutationCorridor("CITRINITAS", "VIRIDITAS",   phi_threshold=0.28,
                          mechanism="Solar intelligence seeds green life."),
    TransmutationCorridor("VIRIDITAS",  "CAERULITAS",  phi_threshold=0.42,
                          mechanism="Green growth reaches into deep water."),
    TransmutationCorridor("CAERULITAS", "RUBEDO",      phi_threshold=0.58,
                          mechanism="Blue depth integrates solar fire."),
    TransmutationCorridor("RUBEDO",     "IOSIS",       phi_threshold=0.72,
                          mechanism="Red-gold ignites violet transmutation."),
    TransmutationCorridor("IOSIS",      "ALBEDO",      phi_threshold=0.85,
                          mechanism="Violet fire purifies to lunar white."),
    TransmutationCorridor("ALBEDO",     "CHRYSITAS",   phi_threshold=0.92,
                          mechanism="White purity crosses the golden gate."),
    TransmutationCorridor("CHRYSITAS",  "ARGENTITAS",  phi_threshold=0.95,
                          mechanism="Gold refines to silver perfection."),
    TransmutationCorridor("ARGENTITAS", "LUX_PERPETUA",phi_threshold=0.97,
                          mechanism="Silver opens into the Perpetual Light."),
]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_force(name: str) -> Optional[SpectralForce]:
    """
    Retrieve a SpectralForce by name (case-insensitive).

    Returns None if the name is not in the registry.
    """
    return _FORCE_INDEX.get(name.upper())


def force_from_phi(phi: float) -> SpectralForce:
    """
    Return the canonical SpectralForce for the given phi value.

    Falls back to NIGREDO for phi < 0 and LUX_PERPETUA for phi >= 0.97.
    """
    for force in SPECTRAL_FORCES:
        if force.name == "IRIDITAS":
            continue  # meta-force — skip in phi lookup
        if force.contains(phi):
            return force
    return _FORCE_INDEX["LUX_PERPETUA"]


def list_forces(include_meta: bool = False) -> List[SpectralForce]:
    """
    Return the canonical force list.

    Args:
        include_meta: If True, includes IRIDITAS (the meta-force).

    Returns:
        List of SpectralForce ordered by phi_min.
    """
    forces = [f for f in SPECTRAL_FORCES if include_meta or f.name != "IRIDITAS"]
    return sorted(forces, key=lambda f: f.phi_min)


__all__ = [
    "SpectralForce",
    "TransmutationCorridor",
    "SPECTRAL_FORCES",
    "TRANSMUTATION_CORRIDORS",
    "get_force",
    "force_from_phi",
    "list_forces",
]
