"""
simulation/triadic_field_sim.py

# ============================================================
# HYPOTHESIS
# ============================================================
# Three-body field systems (Electronic + Protonic + Neutronic)
# exhibit measurably different closure properties than dyadic systems.
# Specifically:
#   1. Equilateral triadic configurations (nodes equally weighted
#      across field layers) will achieve higher triadic coherence
#      than asymmetric configurations.
#   2. No pure three-body system achieves closed_harmonic closure
#      without a fourth element — a neutral gate (the Q=C=S sovereign
#      witness, net charge ≈ 0). Adding a gate node to the highest-
#      scoring partial triad will push it over the closed_harmonic
#      threshold.
#   3. The polarity field algebra from color_atomization_sim
#      (angular distance + charge_term + resonance product) generalizes
#      to field-layer space, not just spectral space.
#
# SCHEMA OVERVIEW
# ============================================================
# TriadicNode: a point in the GAIA field with:
#   - layer_weights: (w_e, w_p, w_n) — how much of each field layer
#     (electronic, protonic, neutronic) the node participates in.
#     Interpreted as a 3D direction vector, like charge in color sim.
#   - charge: (positive, negative) — net polarity in field space
#   - resonance: scalar field strength [0, 1]
#
# Pairwise coherence between nodes A and B:
#   angular_score   = dot(layer_weights_A, layer_weights_B) normalized
#   charge_term     = (1 - cosine(charge_A, charge_B)) / 2  [attraction]
#   resonance_score = resonance_A * resonance_B
#   coherence       = 0.50 * angular_score
#                   + 0.30 * charge_term
#                   + 0.20 * resonance_score
#
# Triadic coherence: mean of the three pairwise coherence scores.
# Closure states:
#   closed_harmonic  : triadic_coherence >= 0.60
#   partially_open   : 0.35 <= triadic_coherence < 0.60
#   unstable         : triadic_coherence < 0.35
#
# OUTPUTS
# ============================================================
#   simulation/output/triadic_field_results.csv
#     — pairwise and triadic coherence for all 10 canonical configs
#       plus the gate-augmented test
#   simulation/output/triadic_field_snapshot.png
#     — four-panel field visualization (retained from scaffold)
#
# CANON REFS
# ============================================================
#   C00 — Q=C=S foundational cosmology (quantum = consciousness = space)
#   C41 — Alchemy of Being
# Related proofs:
#   proofs/COLOR_ATOMIZATION_PROOF.md — polarity field algebra origin
# Related issues:
#   #607 — color atomization (source of open questions answered here)
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Output directory ──────────────────────────────────────────────────────────
OUT = Path("simulation/output")
OUT.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
W_ANGULAR    = 0.50
W_CHARGE     = 0.30
W_RESONANCE  = 0.20

HARMONIC_THRESHOLD  = 0.60
PARTIAL_THRESHOLD   = 0.35


# ── Node definition ───────────────────────────────────────────────────────────
@dataclass
class TriadicNode:
    """
    A node in the GAIA triadic field.

    layer_weights : (w_electronic, w_protonic, w_neutronic)
        Participation in each field layer. Treated as a 3-D direction vector.
        Values in [0, 1]. Need not sum to 1 — they are normalized for scoring.
    charge : (positive, negative)
        Polarity vector. Same schema as ColorAtom in color_atomization_sim.
    resonance : float [0, 1]
        Field strength / signal intensity.
    name : str
        Human-readable identifier.
    """
    name: str
    layer_weights: Tuple[float, float, float]   # (electronic, protonic, neutronic)
    charge: Tuple[float, float]                  # (positive, negative)
    resonance: float


# ── Scoring functions ─────────────────────────────────────────────────────────
def _cosine(a: Tuple, b: Tuple) -> float:
    va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def pairwise_coherence(a: TriadicNode, b: TriadicNode) -> dict:
    angular_score   = (_cosine(a.layer_weights, b.layer_weights) + 1) / 2  # map [-1,1] → [0,1]
    charge_cosine   = _cosine(a.charge, b.charge)
    charge_term     = (1 - charge_cosine) / 2                              # opposition = attractive
    resonance_score = a.resonance * b.resonance
    coherence       = (W_ANGULAR * angular_score
                       + W_CHARGE * charge_term
                       + W_RESONANCE * resonance_score)
    state = (
        "harmonic"   if coherence >= HARMONIC_THRESHOLD else
        "neutral"    if coherence >= PARTIAL_THRESHOLD  else
        "dissonant"
    )
    return {
        "node_a":           a.name,
        "node_b":           b.name,
        "angular_score":    round(angular_score, 4),
        "charge_cosine":    round(charge_cosine, 4),
        "charge_term":      round(charge_term, 4),
        "resonance_score":  round(resonance_score, 4),
        "coherence":        round(coherence, 4),
        "state":            state,
    }


def triadic_coherence(nodes: List[TriadicNode]) -> dict:
    """Score a three-node system: mean pairwise coherence + closure state."""
    assert len(nodes) == 3, "triadic_coherence requires exactly 3 nodes"
    pairs = list(combinations(nodes, 2))
    pair_scores = [pairwise_coherence(a, b) for a, b in pairs]
    mean_coh = float(np.mean([p["coherence"] for p in pair_scores]))
    closure = (
        "closed_harmonic" if mean_coh >= HARMONIC_THRESHOLD else
        "partially_open"  if mean_coh >= PARTIAL_THRESHOLD  else
        "unstable"
    )
    return {
        "triad_name":           "-".join(n.name for n in nodes),
        "triadic_coherence":    round(mean_coh, 4),
        "closure_state":        closure,
        "pair_AB_coherence":    pair_scores[0]["coherence"],
        "pair_AC_coherence":    pair_scores[1]["coherence"],
        "pair_BC_coherence":    pair_scores[2]["coherence"],
        "pair_AB_state":        pair_scores[0]["state"],
        "pair_AC_state":        pair_scores[1]["state"],
        "pair_BC_state":        pair_scores[2]["state"],
    }


# ── Node library ─────────────────────────────────────────────────────────────
# Each node's layer_weights encode its "home" in the triadic field:
#   Electronic node  — high electronic, low protonic, low neutronic
#   Protonic node    — low electronic, high protonic, low neutronic
#   Neutronic node   — low electronic, low protonic, high neutronic
#   Bridge nodes     — mixed weights, representing liminal field positions
#
# Charge schema follows color_atomization_sim convention:
#   Warm/active polarity  → higher positive charge
#   Cool/receptive polarity → higher negative charge
#   Neutral gate          → balanced (0.50, 0.50), net charge ≈ 0

NODE_LIBRARY: List[TriadicNode] = [
    # ── Pure field nodes ──────────────────────────────────────────────────────
    TriadicNode("ELECTRONIC",   (0.90, 0.10, 0.10), (0.90, 0.15), resonance=0.85),
    TriadicNode("PROTONIC",     (0.10, 0.90, 0.10), (0.15, 0.90), resonance=0.80),
    TriadicNode("NEUTRONIC",    (0.10, 0.10, 0.90), (0.50, 0.55), resonance=0.70),

    # ── Balanced / equilateral nodes ─────────────────────────────────────────
    TriadicNode("BALANCED_A",   (0.60, 0.60, 0.60), (0.70, 0.30), resonance=0.75),
    TriadicNode("BALANCED_B",   (0.60, 0.60, 0.60), (0.30, 0.70), resonance=0.75),
    TriadicNode("BALANCED_C",   (0.60, 0.60, 0.60), (0.50, 0.50), resonance=0.72),

    # ── Bridge / liminal nodes ────────────────────────────────────────────────
    TriadicNode("EP_BRIDGE",    (0.70, 0.70, 0.10), (0.75, 0.30), resonance=0.78),
    TriadicNode("EN_BRIDGE",    (0.70, 0.10, 0.70), (0.60, 0.45), resonance=0.74),
    TriadicNode("PN_BRIDGE",    (0.10, 0.70, 0.70), (0.25, 0.80), resonance=0.76),

    # ── Sovereign gate node (Q=C=S neutral witness) ───────────────────────────
    # Net charge ≈ 0. Resonance elevated — it is a strong field presence
    # without belonging to either polarity hemisphere.
    # This is the candidate fourth element from C00 (Q=C=S).
    TriadicNode("GATE_QCS",     (0.57, 0.57, 0.57), (0.50, 0.50), resonance=0.90),
]

# Index for easy lookup
NODES = {n.name: n for n in NODE_LIBRARY}


# ── Canonical triad configurations ───────────────────────────────────────────
# 10 configurations covering:
#   - Pure field triads (one per layer)
#   - Equilateral triads (all balanced)
#   - Bridge-inclusive triads
#   - Asymmetric triads (one pure + two mixed)
#   - The gate-augmented test (best partial triad + GATE_QCS as moderator)

CANONICAL_TRIADS: List[List[str]] = [
    # 1. Pure field triad — E + P + N (the canonical Q=C=S three-body)
    ["ELECTRONIC", "PROTONIC", "NEUTRONIC"],

    # 2. Equilateral positive triad
    ["BALANCED_A", "BALANCED_B", "BALANCED_C"],

    # 3. E + P bridge triad
    ["ELECTRONIC", "PROTONIC", "EP_BRIDGE"],

    # 4. E + N bridge triad
    ["ELECTRONIC", "NEUTRONIC", "EN_BRIDGE"],

    # 5. P + N bridge triad
    ["PROTONIC", "NEUTRONIC", "PN_BRIDGE"],

    # 6. All-bridge triad
    ["EP_BRIDGE", "EN_BRIDGE", "PN_BRIDGE"],

    # 7. Asymmetric: pure Electronic + two balanced
    ["ELECTRONIC", "BALANCED_A", "BALANCED_B"],

    # 8. Asymmetric: pure Protonic + two balanced
    ["PROTONIC", "BALANCED_B", "BALANCED_C"],

    # 9. Asymmetric: mixed (EP + PN + NEUTRONIC)
    ["EP_BRIDGE", "PN_BRIDGE", "NEUTRONIC"],

    # 10. Gate-augmented: best partial triad (to be determined at runtime)
    #     Replaced dynamically below after scoring configs 1-9.
    None,
]


# ── Run triadic scoring ───────────────────────────────────────────────────────
results: List[dict] = []

for i, config in enumerate(CANONICAL_TRIADS[:9]):  # score configs 1-9 first
    nodes = [NODES[name] for name in config]
    r = triadic_coherence(nodes)
    r["config_id"] = i + 1
    r["config_type"] = (
        "pure_field"    if all(n in ("ELECTRONIC","PROTONIC","NEUTRONIC") for n in config) else
        "equilateral"   if all("BALANCED" in n for n in config) else
        "all_bridge"    if all("BRIDGE" in n for n in config) else
        "bridge_pair"   if sum(1 for n in config if "BRIDGE" in n) == 1 else
        "asymmetric"
    )
    results.append(r)

# Identify best partial triad to use in gate test (config 10)
best = max(results, key=lambda r: r["triadic_coherence"])
best_nodes_names = best["triad_name"].split("-")

# Config 10: replace one node in the best triad with GATE_QCS
# Replace the lowest-scoring node (the weakest link in the best triad)
pair_scores_for_best = [
    (best_nodes_names[0], best["pair_AB_coherence"] + best["pair_AC_coherence"]),
    (best_nodes_names[1], best["pair_AB_coherence"] + best["pair_BC_coherence"]),
    (best_nodes_names[2], best["pair_AC_coherence"] + best["pair_BC_coherence"]),
]
weakest = min(pair_scores_for_best, key=lambda x: x[1])[0]
gate_config = [n for n in best_nodes_names if n != weakest] + ["GATE_QCS"]

gate_nodes = [NODES[name] for name in gate_config]
gate_result = triadic_coherence(gate_nodes)
gate_result["config_id"] = 10
gate_result["config_type"] = "gate_augmented"
results.append(gate_result)

# ── Save results ──────────────────────────────────────────────────────────────
df = pd.DataFrame(results)
df = df[["config_id", "config_type", "triad_name",
          "triadic_coherence", "closure_state",
          "pair_AB_coherence", "pair_AC_coherence", "pair_BC_coherence",
          "pair_AB_state", "pair_AC_state", "pair_BC_state"]]
df = df.sort_values("triadic_coherence", ascending=False).reset_index(drop=True)
df.to_csv(OUT / "triadic_field_results.csv", index=False)
print("\n=== GAIA Triadic Field Simulation Results ===")
print(df.to_string(index=False))
print(f"\nBest triad: {df.iloc[0]['triad_name']} (coherence={df.iloc[0]['triadic_coherence']}, {df.iloc[0]['closure_state']})")

# ── Field visualization (retained + upgraded) ─────────────────────────────────
n_grid = 160
x = np.linspace(-4.0, 4.0, n_grid)
y = np.linspace(-4.0, 4.0, n_grid)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
TH = np.arctan2(Y, X)

E_field = np.sin(2.4 * X) * np.cos(2.0 * Y) * np.exp(-0.08 * R**2)
P_field = np.exp(-0.55 * R**2)
N_field = 0.55 * np.exp(-0.12 * R**2) + 0.15 * np.cos(3 * TH) * np.exp(-0.25 * R**2)
M_field = 0.45 * E_field + 0.35 * P_field + 0.20 * N_field

fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
fig.patch.set_facecolor("#08111f")
plots = [
    (E_field, "Electronic Field", "magma"),
    (P_field, "Protonic Field", "viridis"),
    (N_field, "Neutronic Field", "cividis"),
    (M_field, "Meta-Field (Triadic Superposition)", "plasma"),
]
for ax, (field, title, cmap) in zip(axes.flat, plots):
    im = ax.imshow(field, extent=[x.min(), x.max(), y.min(), y.max()], origin="lower", cmap=cmap)
    ax.set_title(title, color="white", fontsize=12)
    ax.set_xlabel("x", color="#cbd5e1")
    ax.set_ylabel("y", color="#cbd5e1")
    ax.tick_params(colors="#94a3b8")
    ax.set_facecolor("#0f172a")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.yaxis.set_tick_params(color="#94a3b8")
    plt.setp(cb.ax.get_yticklabels(), color="#cbd5e1")

# Overlay: mark the top triad node positions as field points
best_row = df.iloc[0]
best_node_names = best_row["triad_name"].split("-")
best_nodes_obj = [NODES[n] for n in best_node_names]
# Project node layer_weights into 2D (use e-p plane for visibility)
for ax in axes.flat:
    for node in best_nodes_obj:
        px = (node.layer_weights[0] - 0.5) * 4  # electronic → x
        py = (node.layer_weights[1] - 0.5) * 4  # protonic   → y
        ax.plot(px, py, "o", color="#00ffcc", markersize=6, alpha=0.85)
        ax.annotate(node.name, (px, py), textcoords="offset points",
                    xytext=(5, 5), color="#00ffcc", fontsize=7, alpha=0.9)

fig.suptitle(
    f"GAIA Triadic Field Simulation\nBest triad: {best_row['triad_name']} "
    f"(coherence={best_row['triadic_coherence']}, {best_row['closure_state']})",
    color="white", fontsize=14
)
fig.savefig(OUT / "triadic_field_snapshot.png", dpi=180, facecolor=fig.get_facecolor())
print(f"Wrote: {OUT / 'triadic_field_snapshot.png'}")
print(f"Wrote: {OUT / 'triadic_field_results.csv'}")
