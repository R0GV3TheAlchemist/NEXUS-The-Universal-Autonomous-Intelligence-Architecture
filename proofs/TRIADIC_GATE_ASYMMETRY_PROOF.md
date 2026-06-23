# TRIADIC GATE ASYMMETRY PROOF

**Resolves:** OQ5 | **Date:** 2026-06-23

## The Linear Law

**R_min(a) ≈ 0.824 × a + 0.337**

Each +0.10 in gate layer_weight asymmetry costs ~0.082 in required R_min.

## Three Zones

| Zone | Asymmetry range | R_min | Behavior |
|---|---|---|---|
| Robustness | a < 0.15 | 0.45 | No cost. Gate is insensitive to small perturbations. |
| Compensation | 0.15 ≤ a < 0.80 | 0.50–0.95 | Linear cost. Higher resonance compensates asymmetry. |
| Dead | a ≥ 0.80 | NEVER | No resonance rescues the gate. |

## Key Findings

- OQ5 example gate (0.60,0.55,0.57): a_eff ≈ 0.023, R_min = 0.45. Robust.
- ELECTRONIC node as gate: a_eff ≈ 0.727, R_min = 0.95. Barely functional.
- Off-axis tilt (EXP-B, one layer fixed): caps at R_min=0.80 — never fully fails.
- Mechanism: asymmetry degrades angular cosines. Angular dominance (W=0.50) governs.

## Gate Specification

Target a < 0.15 for gate nodes. Above a=0.15, every +0.10 in asymmetry costs +0.082 in R_min.
