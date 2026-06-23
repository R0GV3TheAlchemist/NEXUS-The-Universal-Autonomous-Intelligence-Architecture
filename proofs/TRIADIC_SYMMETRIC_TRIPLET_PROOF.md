# TRIADIC SYMMETRIC TRIPLET PROOF

**Simulation:** `triadic_symmetric_triplet_sim.py`  
**Status:** Confirmed  
**Resolves:** OQ8 from `TRIADIC_CHARGE_COMPLEMENTARITY_PROOF.md`  
**Date:** 2026-06-23  
**Canon Refs:** C00 (Q=C=S cosmology), TRIADIC_CHARGE_COMPLEMENTARITY_PROOF.md  

---

## Hypothesis (OQ8)

OQ6 showed that two partially differentiated anchor nodes with complementary charge can substitute for structural balance up to d=0.70. OQ8 asks: what if all three nodes are mutually complementary, with no dedicated anchor at all? Can a purely symmetric triplet — each node equally differentiated in a different layer direction, each node's charge 120° from the others — achieve and sustain closed_harmonic closure?

**H:** A symmetric triplet closes at low d but hits a lower ceiling than the OQ6 anchor pair because all three edges degrade simultaneously with no fixed anchor to hold the floor.

---

## Method

2D sweep: d (differentiation) × c (rotational charge complementarity), 231 configurations.

- **Layer weights**: three-way rotational symmetry. At d=0: all (1/3,1/3,1/3). At d=1: A=(0.80,0.10,0.10), B=(0.10,0.80,0.10), C=(0.10,0.10,0.80). Each node leans toward a different layer.
- **Charge**: vectors at 0°, 120°, 240° in 2D charge space. At c=0: all neutral (0.50,0.50). At c=1: amplitude 0.40 from neutral, so A=(0.90,0.50), B=(0.30,0.85), C=(0.30,0.15).
- **Resonance**: all three nodes at R=0.75. No asymmetry.

---

## Results

### Closure Map

| d | Min c for closure | Max coherence at c=1.0 |
|---|---|---|
| 0.00–0.15 | 0.0 | 0.64 |
| 0.20 | 0.3 | 0.6246 |
| 0.25 | 0.6 | 0.6171 |
| 0.30 | 0.9 | 0.6083 |
| **0.35+** | **NEVER** | **0.5985 and falling** |

### Hard Ceiling at d = 0.35

At d=0.35, even perfect rotational complementarity (c=1.0) produces a triadic coherence of 0.5985 — just 0.0015 below the threshold. The ceiling is structural: by d=0.35, the cosine between any two node layer_weight vectors has dropped enough that the angular term (weight 0.50) can no longer be rescued by the charge and resonance terms combined.

---

## The Mechanism: No Fixed Anchor

The key difference between OQ8 (symmetric triplet) and OQ6 (anchor pair + third node) is **what remains constant as d increases**.

In OQ6, both anchor nodes share identical layer_weights (0.60,0.60,0.60) regardless of d. Their pair_AB angular cosine is always 1.0. Only the AX and BX edges degrade. The pair_AB edge is a fixed floor that holds the triadic mean up.

In OQ8, all three nodes differentiate simultaneously in different directions. At d=0.20, cos(A,B) = 0.9434 — already decaying. All three pairwise edges degrade together. There is no fixed floor. The triadic mean falls faster because all three terms in the average are declining.

| d | OQ6 pair_AB (fixed anchors) | OQ8 pair_AB (co-differentiating) |
|---|---|---|
| 0.00 | 0.6539 | 0.6125 |
| 0.20 | 0.6539 | 0.5984 |
| 0.30 | 0.6539 | 0.5821 |
| 0.35 | 0.6539 | 0.5723 |

This is the anchor premium: structural balance in two nodes buys a permanently elevated pair_AB floor. Symmetric triplets have no such floor — every edge is load-bearing, every edge degrades.

---

## Comparison: Three Closure Primitives

| Configuration | Differentiation ceiling | Complementarity required |
|---|---|---|
| OQ3/OQ7: Two balanced anchors (R=0.75) | Unconditional (d=1.0) | None |
| OQ6: Complementary anchor pair | d ≤ 0.70 | c ≥ c_min(d) |
| **OQ8: Symmetric triplet** | **d ≤ 0.30** | **c ≥ c_min(d)** |

The symmetric triplet is the weakest of the three closure primitives. It can close, but only in the near-balanced regime. As a design choice it is appropriate only when all three nodes are naturally near-balanced and you want the additional coherence boost from rotational charge alignment.

---

## Conclusions

1. **OQ8 CONFIRMED.** The symmetric triplet achieves closed_harmonic closure but has a hard ceiling at d=0.35 — significantly lower than the OQ6 anchor pair (d=0.70) or the structural anchor pair (unconditional).

2. **The closure window hierarchy is now complete:**  
   Structural anchors > Complementary anchors > Symmetric triplet.  
   Each step down the hierarchy loses approximately half the differentiation tolerance.

3. **The anchor premium is real.** Having two fixed, identical anchor nodes creates a permanently elevated pair_AB floor. This floor is what allows the triadic mean to stay above 0.60 even as the third node becomes arbitrarily differentiated. Symmetric triplets sacrifice this floor for elegance, and pay a steep price in tolerance.

4. **Angular dominance is the universal mechanism.** In all sims (OQ4, OQ6, OQ7, OQ8), the same law applies: when the angular/structural term degrades below the level where charge and resonance terms can compensate, closure is lost. W_ANGULAR=0.50 is the governing parameter of this entire model family.

---

## The Complete Triadic Design Primitive Set (GAIA-OS)

After OQ2 through OQ8, all closure conditions in the Q=C=S triadic field model are characterized:

| Primitive | Layer weights | Charge | Resonance | Closure guarantee |
|---|---|---|---|---|
| **Gate node** | Near-equal (≈0.57) | Neutral | ≥ 0.45 | Anchors any partial triad |
| **Structural anchor pair** | Both balanced (0.60×3) | Any | ≥ 0.75 | Unconditional |
| **Complementary anchor pair** | d ≤ 0.70, mirrored | c ≥ c_min(d) | ≥ 0.75 | Conditional (moderate 3rd node) |
| **Symmetric triplet** | d ≤ 0.30, 3-way rotation | c ≥ c_min(d) | ≥ 0.75 | Conditional (near-balanced only) |

---

## Open Questions (Remaining)

- **OQ5:** Gate R_min stability under asymmetric layer_weights. Angular dominance now predicts R_min will be sensitive to asymmetry.
- **OQ9:** Do the ceiling laws and trade curves generalize under geometric mean triadic coherence (color atomization sim formula)?
