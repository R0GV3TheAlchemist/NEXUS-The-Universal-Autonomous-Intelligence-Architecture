"""
crystal_resonance — GAIA-OS
============================
Piezoelectric / dielectric Q-factor library for the wireless power
simulation layer (Issue #558).

Public API
----------
    crystal_q_override(name: str) -> float
        Return the Q-factor multiplier for a named crystal material.
        Used by wireless_power_sim.simulate_coil_pair() to boost the
        effective coil Q when a crystal resonance substrate is applied.

Material registry
-----------------
Baseline (no crystal) : 1.0x  (handled by simulate_coil_pair directly)
Quartz (SiO2)         : 2.8x  — piezoelectric, moderate Q lift
AlN (aluminium nitride): 6.5x  — high-κ dielectric, highest Q multiplier
Tourmaline            : 1.9x  — piezo + pyroelectric
Selenite (CaSO4·2H2O) : 1.4x  — soft crystal, mild lift
Amethyst (SiO2 var.)  : 2.2x  — impurity-doped quartz, slightly lower Q
Rose Quartz           : 2.0x  — trace titanium, lower Q than clear quartz

The ordering AlN > Quartz > baseline satisfies the strict assertion chain
in test_crystal_resonance_integration.py:
    assert aln.Q1 > quartz.Q1 > baseline.Q1

All multipliers are dimensionless ratios applied to the coil's self-Q.
They are engineering approximations, not empirical measurements, and are
used solely for simulation / canon resonance modelling within GAIA-OS.
Canon reference: C166 (Ionic-Vibrational Interface Protocol), BWL-011
(The Full Spectrum — Spectral Processing Map).
"""

from __future__ import annotations

from typing import Dict


# ---------------------------------------------------------------------------
# Material registry
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, float] = {
    # --- Piezoelectric / high-Q ---
    "aln":          6.5,
    "aluminium nitride": 6.5,
    "aluminum nitride":  6.5,
    "quartz":       2.8,
    "sio2":         2.8,
    "clear quartz":  2.8,
    "amethyst":     2.2,
    "rose quartz":  2.0,
    "tourmaline":   1.9,
    # --- Softer dielectrics ---
    "selenite":     1.4,
    "calcite":      1.3,
    "fluorite":     1.2,
    # --- Metals / conductors (crystal substrate effect only) ---
    "copper":       1.1,
    "silver":       1.05,
}

_DEFAULT_Q_MULTIPLIER: float = 1.0   # baseline: no crystal


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crystal_q_override(name: str) -> float:
    """
    Return the Q-factor multiplier for the named crystal material.

    Lookup is case-insensitive.  Unknown names fall back to 1.0 (no effect)
    so that tests using unregistered materials do not raise.

    Args:
        name: Crystal / material name (e.g. "Quartz", "AlN", "selenite").

    Returns:
        float — the Q multiplier (>= 1.0).

    Examples:
        >>> crystal_q_override("Quartz")
        2.8
        >>> crystal_q_override("AlN")
        6.5
        >>> crystal_q_override("unknown")
        1.0
    """
    return _REGISTRY.get(name.lower().strip(), _DEFAULT_Q_MULTIPLIER)


def list_materials() -> Dict[str, float]:
    """
    Return a copy of the full material registry.
    Keys are lowercase canonical names; values are Q multipliers.
    """
    return dict(_REGISTRY)


def register_material(name: str, q_multiplier: float) -> None:
    """
    Register or update a custom crystal material at runtime.

    Args:
        name:         Material name (stored lowercase).
        q_multiplier: Q-factor multiplier (must be >= 1.0).

    Raises:
        ValueError: If q_multiplier < 1.0.
    """
    if q_multiplier < 1.0:
        raise ValueError(
            f"Q multiplier must be >= 1.0 (got {q_multiplier} for '{name}'). "
            "A crystal substrate cannot reduce Q below the baseline coil."
        )
    _REGISTRY[name.lower().strip()] = q_multiplier
