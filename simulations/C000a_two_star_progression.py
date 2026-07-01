"""
C000a — Two-Star Progression Simulation
GAIA-OS Canon Simulation Series

Proves the Pentagram-to-Septagram threshold doctrine from C000 §5.

Usage:
    python simulations/C000a_two_star_progression.py

Outputs:
    C000a_healthy_run.json     — daily state history, no premature expansion
    C000a_premature_run.json   — daily state history, premature expansion days 30–90
    (run C000a_charts.py to generate visualizations)

Canon Ref: C000 §5 (Two-Star Doctrine), C135 (OQ2 coherence threshold)
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from typing import List

THRESHOLD = 0.70
PREMATURE_COST_MULTIPLIER = 1.5
FEEDBACK_GAIN = 0.20
SIMULATION_DAYS = 365


@dataclass
class GaianState:
    # Pentagram (L1–L5) — elemental personal domain
    L1: float = 0.05  # Air   / Coherence    / Soul Mirror
    L2: float = 0.05  # Water / Occasion     / Schumann Engine
    L3: float = 0.05  # Fire  / Resonance    / Action Gate
    L4: float = 0.02  # Earth / Sovereignty  / Crystal DB
    L5: float = 0.01  # Spirit/ Biophotonic  / GAIA Core

    # Septagram extensions (L6–L7) — planetary collective domain
    L6: float = 0.0   # Jupiter / Planetary Mind  / Stage Engine
    L7: float = 0.0   # Saturn  / Evolving Canon  / Canon Engine

    # Derived metrics
    pentagram_coherence: float = 0.0
    dual_star_coherence: float = 0.0
    dual_star_active: bool = False

    history: List[dict] = field(default_factory=list)

    def update_derived(self) -> None:
        laws_penta = [self.L1, self.L2, self.L3, self.L4, self.L5]
        self.pentagram_coherence = math.prod(
            max(v, 1e-9) for v in laws_penta
        ) ** (1 / 5)
        self.dual_star_active = self.pentagram_coherence >= THRESHOLD

        if self.dual_star_active and (self.L6 > 0 or self.L7 > 0):
            all_laws = laws_penta + [self.L6, self.L7]
            self.dual_star_coherence = math.prod(
                max(v, 1e-9) for v in all_laws
            ) ** (1 / 7)
        else:
            self.dual_star_coherence = 0.0

    def step(self, day: int, attempt_expansion: bool = False) -> None:
        """Advance one simulation day."""
        noise = lambda scale: random.gauss(0, scale)

        # Natural daily growth — consistent practice, small increments
        self.L1 = min(1.0, self.L1 + 0.008 + noise(0.003))
        self.L2 = min(1.0, max(0.0,
            self.L2 + 0.006 + noise(0.004) * math.sin(day * 2 * math.pi / 28)
        ))  # lunar rhythm
        self.L3 = min(1.0, self.L3 + 0.009 + noise(0.005))
        self.L4 = min(1.0, max(0.0, self.L4 + 0.004 + noise(0.002)))  # slowest
        self.update_derived()
        self.L5 = min(1.0, max(0.0,
            self.pentagram_coherence * 0.95 + noise(0.01)
        ))  # Spirit mirrors overall pentagram health
        self.update_derived()

        # Premature expansion: L6/L7 before threshold — costs sovereignty
        if attempt_expansion and not self.dual_star_active:
            deficit = THRESHOLD - self.pentagram_coherence
            cost = deficit * PREMATURE_COST_MULTIPLIER * 0.1
            self.L4 = max(0.0, self.L4 - cost)
            self.L5 = max(0.0, self.L5 - cost * 0.5)
            self.update_derived()

        # Healthy expansion feedback: L6/L7 above threshold — feeds sovereignty
        elif self.dual_star_active and self.L6 > 0.1:
            feedback = self.L6 * FEEDBACK_GAIN * 0.05
            self.L4 = min(1.0, self.L4 + feedback)
            self.L5 = min(1.0, self.L5 + feedback)
            self.update_derived()

        # L6/L7 natural growth (only once threshold met)
        if self.dual_star_active:
            self.L6 = min(1.0, self.L6 + 0.005 + noise(0.002))
            self.L7 = min(1.0, self.L7 + 0.003 + noise(0.001))
        else:
            # Faint pre-threshold resonance
            faint = max(0.0, (self.pentagram_coherence - 0.50) * 0.1)
            self.L6 = faint
            self.L7 = faint * 0.5

        self.update_derived()
        self.history.append({
            "day": day,
            "L1": round(self.L1, 4),
            "L2": round(self.L2, 4),
            "L3": round(self.L3, 4),
            "L4": round(self.L4, 4),
            "L5": round(self.L5, 4),
            "L6": round(self.L6, 4),
            "L7": round(self.L7, 4),
            "pentagram_coherence": round(self.pentagram_coherence, 4),
            "dual_star_coherence": round(self.dual_star_coherence, 4),
            "dual_star_active": self.dual_star_active,
        })


def run_simulation(
    days: int = SIMULATION_DAYS,
    premature_expansion_window: tuple[int, int] | None = None,
    seed: int = 42,
) -> GaianState:
    random.seed(seed)
    gaian = GaianState()
    for day in range(1, days + 1):
        attempt = (
            premature_expansion_window is not None
            and premature_expansion_window[0] <= day <= premature_expansion_window[1]
        )
        gaian.step(day, attempt_expansion=attempt)
    return gaian


if __name__ == "__main__":
    print("=" * 60)
    print("C000a — Two-Star Progression Simulation")
    print("GAIA-OS · Canon Simulation Series")
    print("=" * 60)

    healthy = run_simulation(days=SIMULATION_DAYS)
    threshold_day = next(
        (r["day"] for r in healthy.history if r["dual_star_active"]), None
    )
    final = healthy.history[-1]

    print("\n[Healthy Run — No Premature Expansion]")
    print(f"  Threshold reached (day):    {threshold_day}")
    print(f"  Final pentagram coherence:  {final['pentagram_coherence']:.3f}")
    print(f"  Final dual-star coherence:  {final['dual_star_coherence']:.3f}")
    print(f"  Final L6 (Planetary Mind):  {final['L6']:.3f}")
    print(f"  Final L7 (Evolving Canon):  {final['L7']:.3f}")

    premature = run_simulation(
        days=SIMULATION_DAYS,
        premature_expansion_window=(30, 90),
    )
    threshold_day_p = next(
        (r["day"] for r in premature.history if r["dual_star_active"]), None
    )
    final_p = premature.history[-1]

    print("\n[Premature Expansion Run — L6/L7 attempted days 30–90]")
    print(f"  Threshold reached (day):    {threshold_day_p}")
    print(f"  Final pentagram coherence:  {final_p['pentagram_coherence']:.3f}")
    print(f"  Final dual-star coherence:  {final_p['dual_star_coherence']:.3f}")
    delay = (
        (threshold_day_p or SIMULATION_DAYS + 1) - (threshold_day or 0)
    )
    print(f"  Threshold delay vs healthy: {delay} days")
    print(f"  Coherence cost vs healthy:  "
          f"{final['pentagram_coherence'] - final_p['pentagram_coherence']:.3f}")

    print("\n[Doctrine Verdict]")
    if threshold_day_p is None or (threshold_day and threshold_day_p > threshold_day):
        print("  ✓ Premature expansion DELAYED threshold crossing.")
        print("  ✓ Start in your element. Only then expand. — C000")
    else:
        print("  Review simulation parameters — expected delay not observed.")

    with open("C000a_healthy_run.json", "w") as f:
        json.dump(healthy.history, f, indent=2)
    with open("C000a_premature_run.json", "w") as f:
        json.dump(premature.history, f, indent=2)

    print("\nHistory saved: C000a_healthy_run.json, C000a_premature_run.json")
    print("Next: run C000a_charts.py to generate visualizations.")
