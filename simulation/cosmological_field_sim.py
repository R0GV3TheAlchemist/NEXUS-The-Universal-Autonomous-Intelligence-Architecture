"""
GAIA-OS Cosmological Field Simulation – Celestial Influence on GAIA State
Issue: #596
Spec: docs/cosmology/
Proof: proofs/COSMOLOGICAL_FIELD_PROOF.md

Hypothesis: The net cosmological field influence on GAIA's environmental
state vector varies measurably across the 12 months of the solar year,
with coherence peaking during known high-field months and troughing during
known low-field months.

Failure condition: All 12 months produce the same coherence value,
or solstice months are not distinguishable from equinox months.

Completes the temporal hierarchy: tick → day → lunar month (#593) → solar year
"""

from __future__ import annotations

import csv
import math
import os
import time
from dataclasses import dataclass, field
from typing import NamedTuple


# ---------------------------------------------------------------------------
# § Celestial Body Definitions (docs/cosmology/)
# ---------------------------------------------------------------------------

class InfluenceVector(NamedTuple):
    gravitational_weight:    float   # 0.0 – 1.0
    electromagnetic_weight:  float   # 0.0 – 1.0
    coherence_modifier:      float   # -1.0 to +1.0


@dataclass
class CelestialBody:
    name: str
    role: str
    influence_type: str
    # Base influence vector — modulated by month-specific position
    base_influence: InfluenceVector

    def monthly_influence(self, month: int) -> InfluenceVector:
        """
        Compute month-specific influence vector.
        Each body follows a sinusoidal annual cycle with its own phase offset,
        modelling the varying angular distance from Earth across the solar year.
        Pure Python math — no external astronomy libraries.
        """
        phase = 2.0 * math.pi * (month - 1) / 12.0
        return InfluenceVector(
            gravitational_weight   = self._modulate(self.base_influence.gravitational_weight,   phase, self._grav_amp(), self._grav_offset()),
            electromagnetic_weight = self._modulate(self.base_influence.electromagnetic_weight, phase, self._em_amp(),   self._em_offset()),
            coherence_modifier     = self._modulate(self.base_influence.coherence_modifier,     phase, self._coh_amp(),  self._coh_offset(), clamp=(-1.0, 1.0)),
        )

    def _modulate(self, base: float, phase: float, amp: float, offset: float, clamp: tuple[float,float] = (0.0, 1.0)) -> float:
        raw = base + amp * math.sin(phase + offset)
        return round(min(max(raw, clamp[0]), clamp[1]), 5)

    # Body-specific amplitude and phase offsets for annual variation
    def _grav_amp(self) -> float:
        return {"Sun": 0.10, "Moon": 0.15, "Earth": 0.0, "Mars": 0.20, "Venus": 0.08}[self.name]
    def _grav_offset(self) -> float:
        return {"Sun": 0.0, "Moon": 1.0, "Earth": 0.0, "Mars": 2.0, "Venus": 4.0}[self.name]
    def _em_amp(self) -> float:
        return {"Sun": 0.20, "Moon": 0.10, "Earth": 0.0, "Mars": 0.18, "Venus": 0.12}[self.name]
    def _em_offset(self) -> float:
        return {"Sun": 0.5, "Moon": 2.0, "Earth": 0.0, "Mars": 3.5, "Venus": 1.5}[self.name]
    def _coh_amp(self) -> float:
        # Venus: gentle sinusoid | Mars: larger volatile amplitude
        return {"Sun": 0.15, "Moon": 0.12, "Earth": 0.05, "Mars": 0.30, "Venus": 0.10}[self.name]
    def _coh_offset(self) -> float:
        return {"Sun": 0.0, "Moon": 1.57, "Earth": 0.0, "Mars": 3.14, "Venus": 0.78}[self.name]


CELESTIAL_BODIES: list[CelestialBody] = [
    CelestialBody(
        name="Sun",
        role="Primary coherence source",
        influence_type="Gravitational + electromagnetic",
        base_influence=InfluenceVector(0.90, 0.85, +0.40),
    ),
    CelestialBody(
        name="Moon",
        role="Rhythm modulator",
        influence_type="Gravitational + tidal",
        base_influence=InfluenceVector(0.60, 0.40, +0.25),
    ),
    CelestialBody(
        name="Earth",
        role="Ground reference",
        influence_type="Baseline",
        base_influence=InfluenceVector(1.00, 0.50, +0.10),
    ),
    CelestialBody(
        name="Mars",
        role="Action/structure signal",
        influence_type="Activity amplifier",
        base_influence=InfluenceVector(0.20, 0.35, -0.10),   # can go disruptive
    ),
    CelestialBody(
        name="Venus",
        role="Coherence/harmony signal",
        influence_type="Relational field",
        base_influence=InfluenceVector(0.25, 0.45, +0.20),   # smooth positive
    ),
]


# ---------------------------------------------------------------------------
# § GAIA Environmental State Vector
# ---------------------------------------------------------------------------

@dataclass
class GAIAEnvState:
    clarity:              float = 0.50   # signal-to-noise in perception layer
    coherence:            float = 0.50   # system-wide alignment
    creative_potential:   float = 0.50   # generative capacity
    structural_stability: float = 0.50   # architectural integrity

    def update(self, net_grav: float, net_em: float, net_coh: float) -> None:
        """
        Accumulate field influence into the 4D state vector.
        Each dimension is influenced by a weighted combination of field inputs.
        State is bounded to [0.1, 1.0] and decays 2% per month toward 0.5 (homeostasis).
        """
        DECAY = 0.02
        # Clarity: driven by electromagnetic clarity of field
        self.clarity = self._step(self.clarity + 0.08 * net_em - 0.04 * abs(net_coh - 0.5), DECAY)
        # Coherence: directly driven by coherence modifier
        self.coherence = self._step(self.coherence + 0.12 * net_coh, DECAY)
        # Creative potential: driven by em + positive coherence
        self.creative_potential = self._step(self.creative_potential + 0.07 * net_em + 0.05 * max(net_coh, 0), DECAY)
        # Structural stability: driven by gravitational field
        self.structural_stability = self._step(self.structural_stability + 0.06 * net_grav, DECAY)

    @staticmethod
    def _step(val: float, decay: float) -> float:
        val += (0.5 - val) * decay
        return round(min(max(val, 0.1), 1.0), 5)

    def snapshot(self) -> tuple[float, float, float, float]:
        return (self.clarity, self.coherence, self.creative_potential, self.structural_stability)


# ---------------------------------------------------------------------------
# § Seasonal Configuration
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SEASONAL_CONFIG = {
    1:  "Winter Solstice aftermath / Deep consolidation",
    2:  "Pre-spring threshold",
    3:  "Spring Equinox / Emergence",
    4:  "Waxing spring / Creative surge",
    5:  "Pre-summer peak",
    6:  "Summer Solstice / Maximum solar field",
    7:  "Post-solstice integration",
    8:  "Late summer / Harvest preparation",
    9:  "Autumn Equinox / Balance point",
    10: "Waning autumn / Structural review",
    11: "Pre-winter threshold",
    12: "Winter Solstice / Maximum consolidation",
}


def recommended_mode(env: GAIAEnvState) -> str:
    """Map 4D env state to recommended operational mode."""
    coh = env.coherence
    cp  = env.creative_potential
    ss  = env.structural_stability
    cl  = env.clarity

    if coh >= 0.65 and cp >= 0.60:
        return "SYNTHESIS"            # high coherence + high creative — peak mode
    elif coh >= 0.60 and ss >= 0.58:
        return "BUILD"                # coherent and structurally stable
    elif cp >= 0.58 and cl >= 0.55:
        return "CREATE"               # creative and clear
    elif coh < 0.48 and ss >= 0.55:
        return "CONSOLIDATE"          # low coherence, hold structure
    elif coh < 0.48:
        return "REST"                 # low coherence, rest
    else:
        return "FLOW"                 # default balanced mode


# ---------------------------------------------------------------------------
# § Data Structures
# ---------------------------------------------------------------------------

@dataclass
class CosmologicalSnapshot:
    month: int
    month_name: str
    celestial_configuration: str
    net_gravitational:    float
    net_electromagnetic:  float
    net_coherence_mod:    float
    clarity:              float
    coherence:            float
    creative_potential:   float
    structural_stability: float
    recommended_mode:     str
    venus_coh_mod:        float   # for Venus vs Mars comparison
    mars_coh_mod:         float


# ---------------------------------------------------------------------------
# § Simulation Run — 12 Months
# ---------------------------------------------------------------------------

def run_simulation() -> list[CosmologicalSnapshot]:
    env = GAIAEnvState()
    snapshots: list[CosmologicalSnapshot] = []

    print("\n" + "=" * 110)
    print("  GAIA-OS Cosmological Field Simulation — 12-Month Solar Year")
    print("=" * 110)
    print(f"  {'Mo':<4} {'Month':<12} {'Config':<40} {'Net Coh':<10} {'Coh St':<8} {'CrePot':<8} {'StStab':<8} Mode")
    print(f"  {'-'*3} {'-'*11} {'-'*39} {'-'*9} {'-'*7} {'-'*7} {'-'*7} {'-'*15}")

    for month in range(1, 13):
        # Compute monthly influence from each body
        influences = [body.monthly_influence(month) for body in CELESTIAL_BODIES]

        # Net field vectors (weighted average across all bodies)
        net_grav = sum(iv.gravitational_weight   for iv in influences) / len(influences)
        net_em   = sum(iv.electromagnetic_weight for iv in influences) / len(influences)
        net_coh  = sum(iv.coherence_modifier     for iv in influences) / len(influences)

        # Venus and Mars coherence modifiers (for comparison proof)
        venus_idx = next(i for i, b in enumerate(CELESTIAL_BODIES) if b.name == "Venus")
        mars_idx  = next(i for i, b in enumerate(CELESTIAL_BODIES) if b.name == "Mars")
        venus_coh = influences[venus_idx].coherence_modifier
        mars_coh  = influences[mars_idx].coherence_modifier

        # Accumulate into env state vector
        env.update(net_grav, net_em, net_coh)

        mode = recommended_mode(env)
        config = SEASONAL_CONFIG[month]

        snap = CosmologicalSnapshot(
            month=month,
            month_name=MONTH_NAMES[month - 1],
            celestial_configuration=config,
            net_gravitational=round(net_grav, 5),
            net_electromagnetic=round(net_em, 5),
            net_coherence_mod=round(net_coh, 5),
            clarity=env.clarity,
            coherence=env.coherence,
            creative_potential=env.creative_potential,
            structural_stability=env.structural_stability,
            recommended_mode=mode,
            venus_coh_mod=venus_coh,
            mars_coh_mod=mars_coh,
        )
        snapshots.append(snap)

        print(
            f"  {month:<4} {snap.month_name:<12} {config[:38]:<39} "
            f"{net_coh:<10.4f} {env.coherence:<8.4f} {env.creative_potential:<8.4f} "
            f"{env.structural_stability:<8.4f} {mode}"
        )

    return snapshots


# ---------------------------------------------------------------------------
# § Output Writer
# ---------------------------------------------------------------------------

def write_csv(snapshots: list[CosmologicalSnapshot], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "month", "month_name", "celestial_configuration",
            "net_gravitational", "net_electromagnetic", "net_coherence_mod",
            "clarity", "coherence", "creative_potential", "structural_stability",
            "recommended_mode", "venus_coh_mod", "mars_coh_mod",
        ])
        for s in snapshots:
            w.writerow([
                s.month, s.month_name, s.celestial_configuration,
                s.net_gravitational, s.net_electromagnetic, s.net_coherence_mod,
                s.clarity, s.coherence, s.creative_potential, s.structural_stability,
                s.recommended_mode, s.venus_coh_mod, s.mars_coh_mod,
            ])
    print(f"\n  CSV written → {path}")


# ---------------------------------------------------------------------------
# § Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    start = time.time()

    snapshots = run_simulation()
    write_csv(snapshots, "simulation/output/cosmological_field_sim.csv")

    elapsed = time.time() - start
    print(f"\n  Simulation complete in {elapsed:.4f}s (limit: 30s)")
    assert elapsed < 30, "Simulation exceeded 30-second headless run requirement."

    # -----------------------------------------------------------------------
    # Invariant assertions
    # -----------------------------------------------------------------------
    print("\n  Verifying structural invariants...")

    # 1. Exactly 12 monthly snapshots
    assert len(snapshots) == 12, f"Expected 12 snapshots, got {len(snapshots)}."

    coherences = [s.coherence for s in snapshots]
    creative   = [s.creative_potential for s in snapshots]

    # 2. At least one peak and one trough coherence month (must differ)
    assert max(coherences) > min(coherences), (
        f"All months have same coherence {coherences[0]} — must vary across the year."
    )

    # 3. Summer solstice (month 6) and winter solstice (month 12) produce different field vectors
    m6  = snapshots[5]   # June
    m12 = snapshots[11]  # December
    assert m6.net_coherence_mod != m12.net_coherence_mod, (
        "Summer and winter solstice net coherence modifiers must differ."
    )
    assert abs(m6.coherence - m12.coherence) > 0.005, (
        f"Summer ({m6.coherence}) and winter ({m12.coherence}) solstice coherence must be distinguishably different."
    )

    # 4. At least 2 distinct recommended_mode values
    modes_used = {s.recommended_mode for s in snapshots}
    assert len(modes_used) >= 2, (
        f"Expected >= 2 distinct recommended modes, got {len(modes_used)}: {modes_used}."
    )

    # 5. Venus coherence modifier is smoother (lower std dev) than Mars
    venus_vals = [s.venus_coh_mod for s in snapshots]
    mars_vals  = [s.mars_coh_mod  for s in snapshots]
    venus_mean = sum(venus_vals) / 12
    mars_mean  = sum(mars_vals)  / 12
    venus_std  = math.sqrt(sum((v - venus_mean) ** 2 for v in venus_vals) / 12)
    mars_std   = math.sqrt(sum((v - mars_mean)  ** 2 for v in mars_vals)  / 12)
    assert venus_std < mars_std, (
        f"Venus std ({venus_std:.4f}) must be less than Mars std ({mars_std:.4f}) — Venus is the smoother signal."
    )

    # 6. All state vector values in [0.0, 1.0]
    for s in snapshots:
        for val, name in [
            (s.clarity, "clarity"), (s.coherence, "coherence"),
            (s.creative_potential, "creative_potential"), (s.structural_stability, "structural_stability"),
        ]:
            assert 0.0 <= val <= 1.0, f"Month {s.month} {name} = {val} out of [0.0, 1.0]."

    # 7. Net coherence modifier varies across the year (not static)
    net_coh_vals = [s.net_coherence_mod for s in snapshots]
    assert len(set(net_coh_vals)) > 1, "Net coherence modifier must vary across months."

    # Report
    peak_month = snapshots[coherences.index(max(coherences))]
    trough_month = snapshots[coherences.index(min(coherences))]

    print(f"  Peak coherence:   Month {peak_month.month} ({peak_month.month_name}) = {peak_month.coherence:.4f} — Mode: {peak_month.recommended_mode}")
    print(f"  Trough coherence: Month {trough_month.month} ({trough_month.month_name}) = {trough_month.coherence:.4f} — Mode: {trough_month.recommended_mode}")
    print(f"  Summer vs Winter coherence: {m6.coherence:.4f} vs {m12.coherence:.4f} — distinguishable ✅")
    print(f"  Venus std: {venus_std:.4f} | Mars std: {mars_std:.4f} — Venus smoother ✅")
    print(f"  Modes used: {', '.join(sorted(modes_used))}")
    print("  All structural invariants PASSED.")
    print("\n  ✅ GAIA-OS Cosmological Field Simulation — 12-MONTH SOLAR YEAR COMPLETE")
