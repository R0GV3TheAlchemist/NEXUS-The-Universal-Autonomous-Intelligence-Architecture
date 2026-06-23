"""
color_atomization_sim.py
GAIA-OS Simulation Layer | Issue #607

Hypothesis: Color is not a continuous gradient but a discrete 12-node spectral
system where each node carries charge polarity (warm=positive, cool=negative),
resonance (photon energy proxy), and interacts with other nodes via complementarity,
charge alignment, and resonance. This models color as a field of charged particles.

Outputs:
  simulation/output/color_atomization_results.csv   — pairwise interactions
  simulation/output/color_atomization_triads.csv    — triadic closure analysis
  proofs/COLOR_ATOMIZATION_PROOF.md                 — findings report
"""

import math
import csv
import os
from dataclasses import dataclass, asdict
from itertools import combinations
from collections import Counter
from typing import List


# ── DATA STRUCTURES ────────────────────────────────────────────────────────────

@dataclass
class ColorAtom:
    name: str
    hue_deg: float
    positive_charge: float   # 0.0–1.0  (warm = high positive)
    negative_charge: float   # 0.0–1.0  (cool = high negative)
    resonance: float         # 0.0–1.0  (proxy for photon energy density)
    wavelength_nm: float     # approximate center wavelength

    @property
    def complement_hue(self):
        return (self.hue_deg + 180) % 360

    @property
    def charge_vector(self):
        return (self.positive_charge, self.negative_charge)

    @property
    def net_charge(self):
        return self.positive_charge - self.negative_charge


@dataclass
class ColorInteraction:
    color_a: str
    color_b: str
    hue_a: float
    hue_b: float
    angular_distance: float
    complementarity_score: float
    charge_alignment: float
    charge_term: float
    resonance_score: float
    coherence_score: float
    state: str


@dataclass
class ColorTriad:
    color_a: str
    color_b: str
    color_c: str
    edge_ab_coherence: float
    edge_bc_coherence: float
    edge_ca_coherence: float
    triadic_coherence: float
    min_edge: float
    triad_type: str
    closure_state: str


# ── CHARGE SCHEMA ──────────────────────────────────────────────────────────────
# Warm colors (red → yellow) lean POSITIVE: they radiate, expand, advance.
# Cool colors (green → violet) lean NEGATIVE: they absorb, contract, recede.
# Yellow-Green is the crossover node (net charge ≈ 0).
# Red-Violet is a bridge node (both charges elevated — it straddles warm/cool).
# Resonance mirrors photon energy: violet highest (~420nm), red lowest (~700nm).

COLOR_ATOMS: List[ColorAtom] = [
    ColorAtom("Red",          0,   0.95, 0.15, 0.55, 700),
    ColorAtom("Red-Orange",   30,  0.90, 0.20, 0.60, 650),
    ColorAtom("Orange",       60,  0.85, 0.25, 0.65, 620),
    ColorAtom("Yellow-Orange",90,  0.75, 0.30, 0.70, 600),
    ColorAtom("Yellow",       120, 0.65, 0.40, 0.75, 580),
    ColorAtom("Yellow-Green", 150, 0.50, 0.50, 0.72, 555),
    ColorAtom("Green",        180, 0.30, 0.70, 0.68, 530),
    ColorAtom("Blue-Green",   210, 0.20, 0.80, 0.62, 500),
    ColorAtom("Blue",         240, 0.15, 0.85, 0.58, 475),
    ColorAtom("Blue-Violet",  270, 0.20, 0.90, 0.75, 450),
    ColorAtom("Violet",       300, 0.25, 0.92, 0.88, 420),
    ColorAtom("Red-Violet",   330, 0.55, 0.60, 0.70, 400),
]

ATOM_BY_NAME = {ca.name: ca for ca in COLOR_ATOMS}


# ── SCORING FUNCTIONS ──────────────────────────────────────────────────────────

def angular_distance(h1: float, h2: float) -> float:
    diff = abs(h1 - h2)
    return min(diff, 360 - diff)


def complementarity_score(dist: float) -> float:
    """Linear: 0 = identical hues, 1 = perfect complements (180°)."""
    return dist / 180.0


def charge_cosine(a: ColorAtom, b: ColorAtom) -> float:
    """Cosine similarity of 2D charge vectors."""
    ax, ay = a.charge_vector
    bx, by = b.charge_vector
    dot = ax * bx + ay * by
    mag_a = math.sqrt(ax**2 + ay**2)
    mag_b = math.sqrt(bx**2 + by**2)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def compute_interaction(a: ColorAtom, b: ColorAtom,
                        w_c: float = 0.50,
                        w_q: float = 0.30,
                        w_r: float = 0.20) -> ColorInteraction:
    """
    Coherence = w_c * complementarity + w_q * charge_term + w_r * resonance_product
    charge_term: maps cosine [-1,1] → [1,0] so opposite vectors score highest.
    """
    dist  = angular_distance(a.hue_deg, b.hue_deg)
    comp  = complementarity_score(dist)
    cos   = charge_cosine(a, b)
    cterm = (1.0 - cos) / 2.0
    res   = a.resonance * b.resonance
    coh   = w_c * comp + w_q * cterm + w_r * res

    if coh >= 0.60:
        state = "harmonic"
    elif coh >= 0.35:
        state = "neutral"
    else:
        state = "dissonant"

    return ColorInteraction(
        color_a=a.name, color_b=b.name,
        hue_a=a.hue_deg, hue_b=b.hue_deg,
        angular_distance=round(dist, 2),
        complementarity_score=round(comp, 4),
        charge_alignment=round(cos, 4),
        charge_term=round(cterm, 4),
        resonance_score=round(res, 4),
        coherence_score=round(coh, 4),
        state=state
    )


def compute_triad(a: ColorAtom, b: ColorAtom, c: ColorAtom) -> ColorTriad:
    ab = compute_interaction(a, b)
    bc = compute_interaction(b, c)
    ca = compute_interaction(c, a)
    scores = [ab.coherence_score, bc.coherence_score, ca.coherence_score]
    tri_coh = (scores[0] * scores[1] * scores[2]) ** (1 / 3)
    min_edge = min(scores)

    angles = sorted([a.hue_deg, b.hue_deg, c.hue_deg])
    gaps = [angles[1]-angles[0], angles[2]-angles[1], 360-(angles[2]-angles[0])]
    gaps_norm = [abs(g - 120) for g in gaps]

    if max(gaps_norm) < 20:
        triad_type = "equilateral"
    elif min(gaps) < 40:
        triad_type = "clustered"
    else:
        triad_type = "asymmetric"

    if tri_coh >= 0.55:
        closure_state = "closed_harmonic"
    elif tri_coh >= 0.35:
        closure_state = "partially_open"
    else:
        closure_state = "unstable"

    return ColorTriad(
        color_a=a.name, color_b=b.name, color_c=c.name,
        edge_ab_coherence=round(ab.coherence_score, 4),
        edge_bc_coherence=round(bc.coherence_score, 4),
        edge_ca_coherence=round(ca.coherence_score, 4),
        triadic_coherence=round(tri_coh, 4),
        min_edge=round(min_edge, 4),
        triad_type=triad_type,
        closure_state=closure_state
    )


# ── SIMULATION RUNNER ──────────────────────────────────────────────────────────

def run_simulation(output_dir: str = "simulation/output"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("proofs", exist_ok=True)

    interactions = [compute_interaction(a, b) for a in COLOR_ATOMS for b in COLOR_ATOMS]
    non_self = [i for i in interactions if i.color_a != i.color_b]
    complement_pairs = [i for i in non_self if abs(i.angular_distance - 180) <= 30]
    non_complement   = [i for i in non_self if abs(i.angular_distance - 180) > 30]

    with open(f"{output_dir}/color_atomization_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "color_a","color_b","hue_a","hue_b","angular_distance",
            "complementarity_score","charge_alignment","charge_term",
            "resonance_score","coherence_score","state"
        ])
        w.writeheader()
        for i in interactions:
            w.writerow(asdict(i))

    triads = [compute_triad(a, b, c) for a, b, c in combinations(COLOR_ATOMS, 3)]

    with open(f"{output_dir}/color_atomization_triads.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "color_a","color_b","color_c",
            "edge_ab_coherence","edge_bc_coherence","edge_ca_coherence",
            "triadic_coherence","min_edge","triad_type","closure_state"
        ])
        w.writeheader()
        for t in triads:
            w.writerow(asdict(t))

    state_dist   = Counter(i.state for i in non_self)
    closure_dist = Counter(t.closure_state for t in triads)
    avg_comp_coh = sum(i.coherence_score for i in complement_pairs) / len(complement_pairs)
    avg_non_coh  = sum(i.coherence_score for i in non_complement) / len(non_complement)
    advantage    = avg_comp_coh - avg_non_coh

    print(f"Pairwise: {len(non_self)} interactions | harmonic={state_dist['harmonic']} neutral={state_dist['neutral']} dissonant={state_dist['dissonant']}")
    print(f"Complement advantage: +{advantage:.4f} (+{100*advantage/avg_non_coh:.1f}%)")
    print(f"Triads: {len(triads)} | closed={closure_dist.get('closed_harmonic',0)} partial={closure_dist['partially_open']} unstable={closure_dist['unstable']}")
    return interactions, triads


if __name__ == "__main__":
    run_simulation()
