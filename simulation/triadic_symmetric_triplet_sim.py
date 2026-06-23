"""
triadic_symmetric_triplet_sim.py
GAIA-OS Simulation Layer | Issue #607 — OQ8 Resolution

# ============================================================
# HYPOTHESIS (OQ8)
# ============================================================
# OQ6 showed that two partially differentiated anchor nodes with
# complementary charge vectors can substitute for structural balance
# up to d=0.70. OQ8 asks: what if ALL THREE nodes are mutually
# complementary — a pure symmetric triplet with no dedicated anchor?
#
# True three-way complementarity requires rotational symmetry in
# charge space: charge vectors at 0°, 120°, 240°. Similarly, layer
# weights are rotationally symmetric: A leans Q, B leans P, C leans N.
#
# H: A symmetric triplet achieves closed_harmonic closure at low d,
#    but the ceiling is lower than OQ6 (anchor pair) because all
#    three nodes degrade simultaneously with no fixed anchor.
#
# EXPERIMENTAL DESIGN
# ============================================================
# 2D parameter sweep (identical structure to OQ6):
#   d (differentiation): 0.0 → 1.0 in steps of 0.05
#     At d=0: all nodes (1/3, 1/3, 1/3) — fully balanced
#     At d=1: A=(0.80,0.10,0.10), B=(0.10,0.80,0.10), C=(0.10,0.10,0.80)
#
#   c (complementarity): 0.0 → 1.0 in steps of 0.10
#     At c=0: all charges neutral (0.50,0.50)
#     At c=1: charge vectors at 120° spacing in 2D charge space
#             amplitude 0.40 from neutral
#
# All resonances held at 0.75. No fixed anchor node.
#
# OUTPUT
# ============================================================
#   simulation/output/triadic_oq8_symmetric_triplet.csv
#
# CANON REFS
# ============================================================
#   proofs/TRIADIC_CHARGE_COMPLEMENTARITY_PROOF.md — OQ8 definition
#   proofs/TRIADIC_SYMMETRIC_TRIPLET_PROOF.md — findings (this sim)
#   C00 — Q=C=S foundational cosmology
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np

OUT = Path("simulation/output")
OUT.mkdir(parents=True, exist_ok=True)

W_ANGULAR   = 0.50
W_CHARGE    = 0.30
W_RESONANCE = 0.20
HARMONIC_THRESHOLD = 0.60
PARTIAL_THRESHOLD  = 0.35
CHARGE_AMP  = 0.40  # max amplitude of rotational charge displacement


@dataclass
class TriadicNode:
    name: str
    layer_weights: Tuple[float, float, float]
    charge: Tuple[float, float]
    resonance: float


def _cosine(a, b) -> float:
    va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


def pairwise_coherence(a: TriadicNode, b: TriadicNode) -> float:
    angular_score   = (_cosine(a.layer_weights, b.layer_weights) + 1) / 2
    charge_term     = (1 - _cosine(a.charge, b.charge)) / 2
    resonance_score = a.resonance * b.resonance
    return W_ANGULAR * angular_score + W_CHARGE * charge_term + W_RESONANCE * resonance_score


def triadic_coh(nodes: List[TriadicNode]):
    scores = [
        pairwise_coherence(nodes[0], nodes[1]),
        pairwise_coherence(nodes[0], nodes[2]),
        pairwise_coherence(nodes[1], nodes[2]),
    ]
    mean = float(np.mean(scores))
    state = (
        "closed_harmonic" if mean >= HARMONIC_THRESHOLD else
        "partially_open"  if mean >= PARTIAL_THRESHOLD  else
        "unstable"
    )
    return round(mean, 4), state, [round(s, 4) for s in scores]


# Charge angles: 0°, 120°, 240°
ANGLES = [0.0, 2 * np.pi / 3, 4 * np.pi / 3]

d_values = [round(d, 2) for d in np.arange(0.0, 1.05, 0.05)]
c_values = [round(c, 2) for c in np.arange(0.0, 1.05, 0.10)]
R = 0.75

rows = []

for d in d_values:
    base  = 1 / 3
    peak  = 0.80
    trough = 0.10

    lw_a = (
        round(base + d * (peak   - base), 4),
        round(base + d * (trough - base), 4),
        round(base + d * (trough - base), 4),
    )
    lw_b = (
        round(base + d * (trough - base), 4),
        round(base + d * (peak   - base), 4),
        round(base + d * (trough - base), 4),
    )
    lw_c = (
        round(base + d * (trough - base), 4),
        round(base + d * (trough - base), 4),
        round(base + d * (peak   - base), 4),
    )

    for c in c_values:
        charges = []
        for angle in ANGLES:
            pos = round(float(np.clip(0.50 + c * CHARGE_AMP * np.cos(angle), 0.05, 0.95)), 4)
            neg = round(float(np.clip(0.50 + c * CHARGE_AMP * np.sin(angle), 0.05, 0.95)), 4)
            charges.append((pos, neg))

        A = TriadicNode("A", lw_a, charges[0], R)
        B = TriadicNode("B", lw_b, charges[1], R)
        C = TriadicNode("C", lw_c, charges[2], R)

        coh, state, pairs = triadic_coh([A, B, C])

        rows.append({
            "d_differentiation": d,
            "c_complementarity": c,
            "lw_a": str(lw_a), "lw_b": str(lw_b), "lw_c": str(lw_c),
            "ch_a": str(charges[0]), "ch_b": str(charges[1]), "ch_c": str(charges[2]),
            "triadic_coherence": coh,
            "closure_state":     state,
            "pair_AB": pairs[0], "pair_AC": pairs[1], "pair_BC": pairs[2],
        })

with open(OUT / "triadic_oq8_symmetric_triplet.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)


# ── Results summary ─────────────────────────────────────────────────────────
print("=" * 58)
print("OQ8 SYMMETRIC TRIPLET — RESULTS")
print("=" * 58)
for d in d_values:
    min_c = None
    for c in c_values:
        row = next(r for r in rows if r["d_differentiation"] == d and r["c_complementarity"] == c)
        if row["closure_state"] == "closed_harmonic":
            min_c = c
            break
    coh_c1 = next(r["triadic_coherence"] for r in rows
                  if r["d_differentiation"] == d and r["c_complementarity"] == 1.0)
    print(f"  d={d:.2f}: min_c={'NEVER':>5} | max_coh={coh_c1}" if min_c is None
          else f"  d={d:.2f}: min_c={min_c:>5} | max_coh={coh_c1}")
print("=" * 58)
