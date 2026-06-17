"""
test_crystal_resonance_integration.py
GAIA-OS — Issue #558 Part 2

Goal:
- Prove crystal_q_override("Quartz") and crystal_q_override("AlN")
  actually affect wireless_power_sim.py simulation output.
- Keep the test surface small and explicit.

Expected behavior:
- Higher Q override should produce higher efficiency at the same geometry.
- AlN should outperform Quartz, which should outperform the baseline coil when
  the coupling regime is not already saturated (1.5m is firmly under-coupled
  for a standard coil, so the crystal effect is maximally visible here).
"""

from crystal_resonance import crystal_q_override
from wireless_power_sim import (
    standard_wound_coil,
    phi_wound_coil,
    simulate_coil_pair,
)


def run_integration_checks() -> dict:
    freq_hz    = 6.78e6
    distance_m = 1.50        # firmly under-coupled for standard coil
    diameter_m = 0.072
    turns      = 12
    wire_d     = 0.001

    tx_std = standard_wound_coil(diameter_m, turns, wire_d)
    rx_std = standard_wound_coil(diameter_m, turns, wire_d)
    tx_phi = phi_wound_coil(diameter_m, turns, wire_d)
    rx_phi = phi_wound_coil(diameter_m, turns, wire_d)

    baseline = simulate_coil_pair(tx_std, rx_std, freq_hz, distance_m)
    quartz   = simulate_coil_pair(
        tx_phi, rx_phi, freq_hz, distance_m,
        crystal_q_override=crystal_q_override("Quartz"),
    )
    aln      = simulate_coil_pair(
        tx_phi, rx_phi, freq_hz, distance_m,
        crystal_q_override=crystal_q_override("AlN"),
    )

    # Quartz must beat baseline
    assert quartz.efficiency_pct > baseline.efficiency_pct, (
        f"Quartz override did not improve efficiency over baseline: "
        f"{quartz.efficiency_pct:.4f}% <= {baseline.efficiency_pct:.4f}%"
    )

    # AlN must beat Quartz
    assert aln.efficiency_pct > quartz.efficiency_pct, (
        f"AlN override did not beat Quartz: "
        f"{aln.efficiency_pct:.4f}% <= {quartz.efficiency_pct:.4f}%"
    )

    # Q chain must be strictly ordered
    assert aln.Q1 > quartz.Q1 > baseline.Q1, (
        f"Q chain invalid: "
        f"baseline={baseline.Q1}, quartz={quartz.Q1}, aln={aln.Q1}"
    )

    return {
        "baseline_efficiency_pct": baseline.efficiency_pct,
        "quartz_efficiency_pct":   quartz.efficiency_pct,
        "aln_efficiency_pct":      aln.efficiency_pct,
        "baseline_Q":              baseline.Q1,
        "quartz_Q":                quartz.Q1,
        "aln_Q":                   aln.Q1,
        "distance_m":              distance_m,
        "freq_hz":                 freq_hz,
    }


if __name__ == "__main__":
    result = run_integration_checks()
    print("=" * 60)
    print("Issue #558 — crystal override integration checks PASSED ✅")
    print("=" * 60)
    for k, v in result.items():
        print(f"  {k}: {v}")
    print()
    print("For the Good and the Greater Good. 🔥")
