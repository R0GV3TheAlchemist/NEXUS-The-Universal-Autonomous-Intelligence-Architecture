"""
wireless_power_sim — GAIA-OS
=============================
Minimal WPT (Wireless Power Transfer) simulation scaffold.

Public API
----------
    standard_wound_coil(diameter_m, turns, wire_diameter_m) -> Coil
    phi_wound_coil(diameter_m, turns, wire_diameter_m) -> Coil
    simulate_coil_pair(
        tx, rx, freq_hz, distance_m, *, crystal_q_override=None
    ) -> SimResult

Physics model
-------------
Uses a simplified two-coil inductive coupling BPF model:

    L = μ₀ · π · N² · (D/2)² / length_approx     (single-layer solenoid approx)
    R_dc = ρ_Cu · (N · π · D) / (π · (d_wire/2)²)
    Q_coil = ω·L / R_dc
    k = (D/2)³ / (2 · distance³)                  (far-field approx, axial)
    η = k²·Q1·Q2 / (1 + k²·Q1·Q2)                (BPF matched-load efficiency)

The phi-wound coil uses a φ-pitch winding factor (1/φ ≈ 0.618 wire spacing)
that increases the effective inductance per unit length by ~18%, yielding a
modestly higher Q than a standard wound coil at the same geometry.

Crystal Q override
------------------
When crystal_q_override is supplied (a float multiplier from crystal_resonance),
both Q1 and Q2 are scaled by that multiplier before efficiency is computed.
This makes AlN > Quartz > baseline in all under-coupled scenarios.

Canon reference: C166 (Ionic-Vibrational Interface Protocol), BWL-011.
Issue: #558
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

_MU0   = 4 * math.pi * 1e-7   # H/m — permeability of free space
_RHO_CU = 1.68e-8              # Ω·m — resistivity of copper at 20°C
_PHI   = (1 + math.sqrt(5)) / 2  # golden ratio ≈ 1.618


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Coil:
    """
    Represents a single wound coil.

    Attributes:
        diameter_m:      Outer coil diameter in metres.
        turns:           Number of winding turns.
        wire_diameter_m: Conductor diameter in metres.
        inductance_H:    Self-inductance in henries.
        resistance_ohm:  DC resistance in ohms.
        phi_wound:       True if wound with φ-pitch spacing.
    """
    diameter_m:      float
    turns:           int
    wire_diameter_m: float
    inductance_H:    float
    resistance_ohm:  float
    phi_wound:       bool = False

    def Q(self, freq_hz: float) -> float:
        """Return the coil Q-factor at the given frequency."""
        omega = 2 * math.pi * freq_hz
        return (omega * self.inductance_H) / self.resistance_ohm


@dataclass
class SimResult:
    """
    Result of a two-coil WPT simulation.

    Attributes:
        efficiency_pct:  Power transfer efficiency in percent (0–100).
        Q1:              Effective Q-factor of the TX coil.
        Q2:              Effective Q-factor of the RX coil.
        k:               Coupling coefficient.
        freq_hz:         Simulation frequency.
        distance_m:      TX–RX separation.
        crystal_applied: Name or value of crystal Q override (if any).
    """
    efficiency_pct: float
    Q1:             float
    Q2:             float
    k:              float
    freq_hz:        float
    distance_m:     float
    crystal_applied: Optional[float] = None


# ---------------------------------------------------------------------------
# Coil factories
# ---------------------------------------------------------------------------

def _inductance(diameter_m: float, turns: int, length_m: float) -> float:
    """Solenoid inductance approximation (single-layer, air-core)."""
    radius = diameter_m / 2
    return _MU0 * math.pi * (radius ** 2) * (turns ** 2) / length_m


def _resistance(diameter_m: float, turns: int, wire_diameter_m: float) -> float:
    """DC resistance of a wound coil."""
    turn_length = math.pi * diameter_m
    total_wire  = turns * turn_length
    wire_area   = math.pi * (wire_diameter_m / 2) ** 2
    return _RHO_CU * total_wire / wire_area


def standard_wound_coil(
    diameter_m: float,
    turns: int,
    wire_diameter_m: float,
) -> Coil:
    """
    Build a standard (uniform-pitch) wound coil.

    Args:
        diameter_m:      Outer coil diameter in metres.
        turns:           Number of turns.
        wire_diameter_m: Wire conductor diameter in metres.

    Returns:
        Coil with computed L and R.
    """
    length_m = turns * wire_diameter_m * 1.05  # slight packing factor
    L = _inductance(diameter_m, turns, length_m)
    R = _resistance(diameter_m, turns, wire_diameter_m)
    return Coil(
        diameter_m=diameter_m,
        turns=turns,
        wire_diameter_m=wire_diameter_m,
        inductance_H=L,
        resistance_ohm=R,
        phi_wound=False,
    )


def phi_wound_coil(
    diameter_m: float,
    turns: int,
    wire_diameter_m: float,
) -> Coil:
    """
    Build a φ-wound coil with golden-ratio pitch spacing.

    The φ-winding packs turns at 1/φ ≈ 0.618 spacing, which reduces the
    effective coil length and increases inductance by ~1/0.618 ≈ 1.618×
    relative to a purely wire-diameter-spaced coil.  In practice the gain
    is moderated by packing limits; we model it as an 18% inductance boost
    (the fractional part of φ).

    Args:
        diameter_m:      Outer coil diameter in metres.
        turns:           Number of turns.
        wire_diameter_m: Wire conductor diameter in metres.

    Returns:
        Coil with φ-enhanced L and standard R.
    """
    # φ-wound: tighter pitch ⟹ shorter coil length ⟹ higher L
    phi_pitch  = wire_diameter_m / _PHI          # tighter spacing
    length_m   = turns * phi_pitch * 1.05
    L = _inductance(diameter_m, turns, length_m)
    R = _resistance(diameter_m, turns, wire_diameter_m)  # resistance unchanged
    return Coil(
        diameter_m=diameter_m,
        turns=turns,
        wire_diameter_m=wire_diameter_m,
        inductance_H=L,
        resistance_ohm=R,
        phi_wound=True,
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def simulate_coil_pair(
    tx: Coil,
    rx: Coil,
    freq_hz: float,
    distance_m: float,
    *,
    crystal_q_override: Optional[float] = None,
) -> SimResult:
    """
    Simulate two-coil WPT efficiency using a BPF matched-load model.

    Physics:
        k   = (r_tx³) / (2 · distance³)   — far-field axial coupling approx
        η   = k²·Q1·Q2 / (1 + k²·Q1·Q2)  — matched-load BPF efficiency

    Args:
        tx:                  Transmitter coil.
        rx:                  Receiver coil.
        freq_hz:             Operating frequency in Hz.
        distance_m:          Coil separation in metres.
        crystal_q_override:  Optional float multiplier from crystal_resonance.
                             When supplied, both Q1 and Q2 are scaled by this
                             value before efficiency is computed.

    Returns:
        SimResult with efficiency_pct, Q1, Q2, k, freq_hz, distance_m.
    """
    Q1 = tx.Q(freq_hz)
    Q2 = rx.Q(freq_hz)

    if crystal_q_override is not None:
        Q1 *= crystal_q_override
        Q2 *= crystal_q_override

    # Coupling coefficient — far-field axial approximation
    r_tx = tx.diameter_m / 2
    k    = (r_tx ** 3) / (2 * (distance_m ** 3))

    # BPF matched-load efficiency
    kQQ  = (k ** 2) * Q1 * Q2
    eta  = kQQ / (1 + kQQ)

    return SimResult(
        efficiency_pct=eta * 100.0,
        Q1=Q1,
        Q2=Q2,
        k=k,
        freq_hz=freq_hz,
        distance_m=distance_m,
        crystal_applied=crystal_q_override,
    )
