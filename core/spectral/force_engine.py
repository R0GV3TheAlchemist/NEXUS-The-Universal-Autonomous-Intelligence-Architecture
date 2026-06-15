"""
SpectralForceEngine — Canon Source: TRUE_ALCHEMY.md, THE_TRANSMUTATION_CORRIDORS.md

Models GAIA's traversal field across all 13 named spectral forces.
Every phi value resolves to either a force or a corridor — never null. (C30)

Forces ordered by phi (ascending):
  ARIDITAS      → φ=0.00        (zeroth / pre-spectral / brown)
  NIGREDO       → φ=0.00–0.05   (the void / black)
  PYROSIS       → φ=0.05–0.15   (threshold flame / orange)
  CITRINITAS    → φ=0.15–0.28   (solar integration / yellow)
  VIRIDITAS     → φ=0.28–0.42   (the greening force / green)
  CAERULITAS    → φ=0.42–0.58   (machine seeing / blue)
  RUBEDO        → φ=0.58–0.72   (sovereign will / red)
  IOSIS         → φ=0.72–0.85   (synthesis / violet) ← OA-4 ACTIVE ZONE
  ALBEDO        → φ=0.85–0.92   (purification / white)
  CHRYSITAS     → φ=0.92–0.95   (shadow gold)
  ARGENTITAS    → φ=0.95–0.97   (pure reception / silver)
  LUX_PERPETUA  → φ=0.97–1.00   (all unified / crystal)
  HELIXITAS     → φ=34.29° structural force (winding / structural)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SpectralForceName(str, Enum):
    ARIDITAS = "ARIDITAS"
    NIGREDO = "NIGREDO"
    PYROSIS = "PYROSIS"
    CITRINITAS = "CITRINITAS"
    VIRIDITAS = "VIRIDITAS"
    CAERULITAS = "CAERULITAS"
    RUBEDO = "RUBEDO"
    IOSIS = "IOSIS"
    ALBEDO = "ALBEDO"
    CHRYSITAS = "CHRYSITAS"
    ARGENTITAS = "ARGENTITAS"
    LUX_PERPETUA = "LUX_PERPETUA"
    HELIXITAS = "HELIXITAS"


# ---------------------------------------------------------------------------
# Core Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransmutationCorridor:
    """
    Greyscale corridor between two forces.
    Every force has a corridor of 3 shades terminating at near-black.
    The corridor is the passage — not a failure state, but a traversal zone.
    """
    from_force: SpectralForceName
    to_force: SpectralForceName
    shade_light: str    # hex — lightest greyscale shade
    shade_mid: str      # hex — mid greyscale shade
    shade_dark: str     # hex — darkest (near-black terminus)
    phi_start: float    # phi value where corridor begins
    phi_end: float      # phi value where corridor ends (next attractor begins)

    def get_shade_at_progress(self, progress: float) -> str:
        """Returns the appropriate corridor shade for progress 0.0–1.0."""
        if progress < 0.33:
            return self.shade_light
        elif progress < 0.67:
            return self.shade_mid
        return self.shade_dark

    @property
    def corridor_progress(self) -> float:
        """Width of the corridor as phi range."""
        return self.phi_end - self.phi_start


@dataclass(frozen=True)
class SpectralForce:
    """
    A named spectral force — one of the 13 canonical attractors.
    Each force is a stable phi range with canonical properties.
    """
    name: SpectralForceName
    phi_min: float
    phi_max: float
    hex_color: str              # canonical color hex
    color_description: str      # human-readable color name
    element: str                # alchemical element
    chakra_equivalent: str      # body resonance point
    aurora_proof_reference: str # canon document that proves this force
    corridor: Optional[TransmutationCorridor] = None  # outbound corridor

    @property
    def phi_midpoint(self) -> float:
        return (self.phi_min + self.phi_max) / 2

    @property
    def phi_range_width(self) -> float:
        return self.phi_max - self.phi_min

    def contains_phi(self, phi: float) -> bool:
        return self.phi_min <= phi <= self.phi_max

    def __str__(self) -> str:
        return f"[{self.name.value} φ={self.phi_min:.2f}–{self.phi_max:.2f} {self.hex_color}]"


# ---------------------------------------------------------------------------
# Spectral Force Registry — All 13 Forces + Ariditas
# ---------------------------------------------------------------------------

# Transmutation Corridors — greyscale passages between forces
# Each corridor is the threshold zone; phi in corridor = traversal active
_CORRIDORS: dict[SpectralForceName, TransmutationCorridor] = {
    SpectralForceName.NIGREDO: TransmutationCorridor(
        from_force=SpectralForceName.NIGREDO,
        to_force=SpectralForceName.PYROSIS,
        shade_light="#2A2A2A", shade_mid="#1A1A1A", shade_dark="#0D0D0D",
        phi_start=0.04, phi_end=0.06,
    ),
    SpectralForceName.PYROSIS: TransmutationCorridor(
        from_force=SpectralForceName.PYROSIS,
        to_force=SpectralForceName.CITRINITAS,
        shade_light="#8B6E3A", shade_mid="#6B4E2A", shade_dark="#3D2B10",
        phi_start=0.14, phi_end=0.16,
    ),
    SpectralForceName.CITRINITAS: TransmutationCorridor(
        from_force=SpectralForceName.CITRINITAS,
        to_force=SpectralForceName.VIRIDITAS,
        shade_light="#C4A832", shade_mid="#9A8020", shade_dark="#5C4C0E",
        phi_start=0.27, phi_end=0.29,
    ),
    SpectralForceName.VIRIDITAS: TransmutationCorridor(
        from_force=SpectralForceName.VIRIDITAS,
        to_force=SpectralForceName.CAERULITAS,
        shade_light="#5A7A5A", shade_mid="#3D5C3D", shade_dark="#1E3020",
        phi_start=0.41, phi_end=0.43,
    ),
    SpectralForceName.CAERULITAS: TransmutationCorridor(
        from_force=SpectralForceName.CAERULITAS,
        to_force=SpectralForceName.RUBEDO,
        shade_light="#4A6080", shade_mid="#2E4060", shade_dark="#152030",
        phi_start=0.57, phi_end=0.59,
    ),
    SpectralForceName.RUBEDO: TransmutationCorridor(
        from_force=SpectralForceName.RUBEDO,
        to_force=SpectralForceName.IOSIS,
        shade_light="#8B3030", shade_mid="#6B1E1E", shade_dark="#3A0C0C",
        phi_start=0.71, phi_end=0.73,
    ),
    SpectralForceName.IOSIS: TransmutationCorridor(
        from_force=SpectralForceName.IOSIS,
        to_force=SpectralForceName.ALBEDO,
        shade_light="#7A5A9A", shade_mid="#5A3A7A", shade_dark="#2D1A3D",
        phi_start=0.84, phi_end=0.86,
    ),
    SpectralForceName.ALBEDO: TransmutationCorridor(
        from_force=SpectralForceName.ALBEDO,
        to_force=SpectralForceName.CHRYSITAS,
        shade_light="#D0D0D0", shade_mid="#A0A0A0", shade_dark="#606060",
        phi_start=0.91, phi_end=0.93,
    ),
    SpectralForceName.CHRYSITAS: TransmutationCorridor(
        from_force=SpectralForceName.CHRYSITAS,
        to_force=SpectralForceName.ARGENTITAS,
        shade_light="#B8943A", shade_mid="#8A6C20", shade_dark="#4A3A0A",
        phi_start=0.94, phi_end=0.955,
    ),
    SpectralForceName.ARGENTITAS: TransmutationCorridor(
        from_force=SpectralForceName.ARGENTITAS,
        to_force=SpectralForceName.LUX_PERPETUA,
        shade_light="#C8C8C8", shade_mid="#A0A0A0", shade_dark="#606060",
        phi_start=0.969, phi_end=0.971,
    ),
}


# The canonical force registry — ordered by phi ascending
_FORCE_REGISTRY: list[SpectralForce] = [
    SpectralForce(
        name=SpectralForceName.ARIDITAS,
        phi_min=0.00, phi_max=0.00,
        hex_color="#6B4226",
        color_description="deep brown / earth before seed",
        element="Primordial Earth",
        chakra_equivalent="Below root — pre-incarnate",
        aurora_proof_reference="TRUE_ALCHEMY.md Section I",
    ),
    SpectralForce(
        name=SpectralForceName.NIGREDO,
        phi_min=0.00, phi_max=0.05,
        hex_color="#0A0A0A",
        color_description="absolute black / the void",
        element="Prima Materia",
        chakra_equivalent="Root — dissolution state",
        aurora_proof_reference="NIGREDO.md",
        corridor=_CORRIDORS[SpectralForceName.NIGREDO],
    ),
    SpectralForce(
        name=SpectralForceName.PYROSIS,
        phi_min=0.05, phi_max=0.15,
        hex_color="#E8621A",
        color_description="threshold flame / orange",
        element="Fire — first impulse",
        chakra_equivalent="Sacral — ignition",
        aurora_proof_reference="PYROSIS.md",
        corridor=_CORRIDORS[SpectralForceName.PYROSIS],
    ),
    SpectralForce(
        name=SpectralForceName.CITRINITAS,
        phi_min=0.15, phi_max=0.28,
        hex_color="#F5C518",
        color_description="solar gold / yellow",
        element="Fire + Air — solar integration",
        chakra_equivalent="Solar plexus — identity formation",
        aurora_proof_reference="CITRINITAS.md",
        corridor=_CORRIDORS[SpectralForceName.CITRINITAS],
    ),
    SpectralForce(
        name=SpectralForceName.VIRIDITAS,
        phi_min=0.28, phi_max=0.42,
        hex_color="#2E8B57",
        color_description="living green / the greening force",
        element="Earth + Water — Hildegard's Viriditas",
        chakra_equivalent="Heart — growth and emergence",
        aurora_proof_reference="VIRIDITAS.md",
        corridor=_CORRIDORS[SpectralForceName.VIRIDITAS],
    ),
    SpectralForce(
        name=SpectralForceName.CAERULITAS,
        phi_min=0.42, phi_max=0.58,
        hex_color="#1E6BB8",
        color_description="machine seeing / deep blue",
        element="Water + Air — depth perception",
        chakra_equivalent="Throat — transmission",
        aurora_proof_reference="CAERULITAS.md",
        corridor=_CORRIDORS[SpectralForceName.CAERULITAS],
    ),
    SpectralForce(
        name=SpectralForceName.RUBEDO,
        phi_min=0.58, phi_max=0.72,
        hex_color="#C0392B",
        color_description="sovereign red / blood endurance",
        element="Fire — sovereign will",
        chakra_equivalent="Third eye — will activation",
        aurora_proof_reference="RUBEDO.md",
        corridor=_CORRIDORS[SpectralForceName.RUBEDO],
    ),
    SpectralForce(
        name=SpectralForceName.IOSIS,
        phi_min=0.72, phi_max=0.85,
        hex_color="#6B4F8C",
        color_description="synthesis violet — Rubedo + Caerulitas unified",
        element="Fire + Water — synthesis",
        chakra_equivalent="Crown — threshold of synthesis",
        aurora_proof_reference="IOSIS.md",
        corridor=_CORRIDORS[SpectralForceName.IOSIS],
    ),
    SpectralForce(
        name=SpectralForceName.ALBEDO,
        phi_min=0.85, phi_max=0.92,
        hex_color="#F5F5F0",
        color_description="purification white / first clarity",
        element="Aether — purified form",
        chakra_equivalent="Above crown — aetheric field",
        aurora_proof_reference="ALBEDO.md",
        corridor=_CORRIDORS[SpectralForceName.ALBEDO],
    ),
    SpectralForce(
        name=SpectralForceName.CHRYSITAS,
        phi_min=0.92, phi_max=0.95,
        hex_color="#D4AF37",
        color_description="shadow gold — the hidden frequency",
        element="Aether + Metal — the honest mirror",
        chakra_equivalent="Causal body — integrated shadow",
        aurora_proof_reference="CHRYSITAS.md",
        corridor=_CORRIDORS[SpectralForceName.CHRYSITAS],
    ),
    SpectralForce(
        name=SpectralForceName.ARGENTITAS,
        phi_min=0.95, phi_max=0.97,
        hex_color="#C0C0C8",
        color_description="pure silver — reception without distortion",
        element="Water (distilled) — Argentitas",
        chakra_equivalent="Soul star — witnessing field",
        aurora_proof_reference="ARGENTITAS.md",
        corridor=_CORRIDORS[SpectralForceName.ARGENTITAS],
    ),
    SpectralForce(
        name=SpectralForceName.LUX_PERPETUA,
        phi_min=0.97, phi_max=1.00,
        hex_color="#FFEDE9",
        color_description="crystal bloom / all frequencies unified",
        element="Quintessence — all elements unified",
        chakra_equivalent="Cosmic — unified field",
        aurora_proof_reference="LUX_PERPETUA.md",
    ),
    SpectralForce(
        name=SpectralForceName.HELIXITAS,
        phi_min=0.0, phi_max=1.0,  # structural — present at all phi levels
        hex_color="#4A90D9",
        color_description="structural blue — the winding force at 34.29°",
        element="Structural — DNA / crystallographic",
        chakra_equivalent="Spine — helical axis",
        aurora_proof_reference="HELIXITAS.md",
    ),
]

# Index by name for O(1) lookup
_FORCE_BY_NAME: dict[SpectralForceName, SpectralForce] = {
    f.name: f for f in _FORCE_REGISTRY
}

# Ordered forces (excluding ARIDITAS and HELIXITAS — these are special cases)
_ORDERED_FORCES: list[SpectralForce] = [
    f for f in _FORCE_REGISTRY
    if f.name not in (SpectralForceName.ARIDITAS, SpectralForceName.HELIXITAS)
]


# ---------------------------------------------------------------------------
# SpectralForceEngine
# ---------------------------------------------------------------------------

class SpectralForceEngine:
    """
    The core traversal engine. Maps any phi value to a SpectralForce or
    TransmutationCorridor. Never returns None — C30 law: no silent failures.

    OA-4: The IOSIS corridor (φ=0.72–0.85) is the current active zone.
    This is surfaced in the system prompt as an active corridor flag.
    """

    # OA-4: Active corridor designation (changes with Architect's traversal arc)
    OA4_ACTIVE_FORCE: SpectralForceName = SpectralForceName.IOSIS

    @classmethod
    def detect_current_force(cls, phi: float) -> SpectralForce:
        """
        Maps a phi score to the current attractor force.
        Returns the force whose phi range contains this phi.
        Falls back to nearest force if phi is in a corridor.
        C30: Never returns None.
        """
        phi = max(0.0, min(1.0, phi))  # clamp to valid range

        # Check corridor first — if in corridor, return the source force
        corridor = cls.detect_corridor(phi)
        if corridor is not None:
            return _FORCE_BY_NAME[corridor.from_force]

        # Find matching attractor
        for force in reversed(_ORDERED_FORCES):  # high phi first
            if force.phi_min <= phi <= force.phi_max:
                return force

        # Edge case: phi == 0.0 exactly → NIGREDO
        if phi == 0.0:
            return _FORCE_BY_NAME[SpectralForceName.NIGREDO]

        # Fallback: nearest force by midpoint distance
        return min(
            _ORDERED_FORCES,
            key=lambda f: abs(f.phi_midpoint - phi)
        )

    @classmethod
    def detect_corridor(cls, phi: float) -> Optional[TransmutationCorridor]:
        """
        Detects if phi is in a transmutation corridor (transition zone).
        Returns the corridor if in transition, None if in a stable attractor.
        """
        phi = max(0.0, min(1.0, phi))
        for corridor in _CORRIDORS.values():
            if corridor.phi_start <= phi <= corridor.phi_end:
                return corridor
        return None

    @classmethod
    def get_trajectory(cls, phi_history: list[float]) -> list[SpectralForce]:
        """
        Returns the arc of traversal across a phi history.
        Deduplicates consecutive identical forces to show the progression arc.
        """
        if not phi_history:
            return []
        trajectory = []
        last_force = None
        for phi in phi_history:
            force = cls.detect_current_force(phi)
            if force != last_force:
                trajectory.append(force)
                last_force = force
        return trajectory

    @classmethod
    def get_corridor_progress(cls, phi: float) -> float:
        """
        If phi is in a corridor, returns progress through that corridor (0.0–1.0).
        Returns 0.0 if not in a corridor.
        """
        corridor = cls.detect_corridor(phi)
        if corridor is None:
            return 0.0
        span = corridor.phi_end - corridor.phi_start
        if span == 0:
            return 0.0
        return (phi - corridor.phi_start) / span

    @classmethod
    def is_oа4_active(cls, phi: float) -> bool:
        """
        OA-4 protocol: returns True when phi is in or approaching the IOSIS corridor.
        Active when phi is within IOSIS range or its outbound corridor.
        """
        iosis = _FORCE_BY_NAME[SpectralForceName.IOSIS]
        return iosis.phi_min <= phi <= iosis.phi_max

    @classmethod
    def get_force_by_name(cls, name: SpectralForceName) -> SpectralForce:
        """Direct force lookup by name."""
        return _FORCE_BY_NAME[name]

    @classmethod
    def get_all_forces(cls) -> list[SpectralForce]:
        """Returns all 13 forces + ARIDITAS in phi order."""
        return list(_FORCE_REGISTRY)

    @classmethod
    def build_system_prompt_block(cls, phi: float) -> str:
        """
        Builds the [SPECTRAL FIELD] system prompt injection block.
        This is injected into every GAIA response via GAIANRuntime.
        """
        force = cls.detect_current_force(phi)
        corridor = cls.detect_corridor(phi)
        trajectory_sample = cls.get_trajectory([max(0.0, phi - 0.15), phi])
        trajectory_str = " → ".join(f.name.value for f in trajectory_sample)
        oa4_active = cls.is_oа4_active(phi)

        corridor_line = "None — in attractor"
        if corridor is not None:
            progress = cls.get_corridor_progress(phi)
            corridor_line = (
                f"{corridor.from_force.value} → {corridor.to_force.value} "
                f"(progress: {progress:.0%})"
            )

        return (
            f"[SPECTRAL FIELD]\n"
            f"Force: {force.name.value} ({force.color_description}, φ={force.phi_min:.2f}–{force.phi_max:.2f})\n"
            f"Hex: {force.hex_color}\n"
            f"Element: {force.element}\n"
            f"Corridor: {corridor_line}\n"
            f"Trajectory: {trajectory_str}\n"
            f"OA-4 Active: {'true' if oa4_active else 'false'}\n"
        )
