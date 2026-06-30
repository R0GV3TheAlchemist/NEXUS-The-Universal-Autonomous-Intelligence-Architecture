# SIM_018 Pass 4 — Research Improvements

**Date:** 2026-06-30  
**Pass:** 4 (Optimisation — Distillation)  
**Score entering:** 86.8% | **Score exiting:** 89.6%

---

## What We Learned in Pass 4

### 1. The Gate Requires 3 Layers Minimum
2-layer CNN reached 87.83% — 0.17 pts short of the 88% gate. 3-layer CNN cleared it at 88.50%. This confirms the pre-run Q1 finding: the plateau is at 3 layers for this data regime, and the 2→3 layer step is non-trivial.

### 2. Transformers Outperform CNNs at This Task
The lightweight transformer (89.37%) beat the 3-layer CNN (88.50%) by 0.87 pts. Self-attention on 400ms event windows captures temporal dependencies that convolutional filters miss. **Transformer is the recommended architecture for all future passes on this simulation class.**

### 3. Time-Warping Augmentation is Valid at ±5%, Harmful at ±10%
Pre-run Q2 was validated empirically: ±5% gave +0.23 pts; ±10% gave −0.47 pts. The spec deviation (reducing from ±10% to ±5%) was correct and produced a net gain. **Conservative augmentation is the rule for biophotonic streams.**

### 4. The Architecture is Now Near-Optimal for Current Data Volume
At 89.6%, we are within ~1–1.5 pts of the estimated Bayes floor (~10–12% error rate). Further architectural changes will produce diminishing returns. The next meaningful gains require more data or cross-subject normalisation.

### 5. GATE-005 Tier 1 is Formally Cleared
All four conditions satisfied. This is the first gate clearance in the SIM_018 series.

---

## Recommendations for Future Work

1. **GATE-005 Tier 2 planning:** Define Tier 2 conditions before starting Pass 5 (if applicable)
2. **Cross-subject normalisation:** Most promising remaining gain (+0.5–1.5 pts projected)
3. **Transformer as default:** All future passes on this simulation should use the transformer architecture as baseline, not SVM + hand-crafted features
4. **Augmentation ceiling:** Do not exceed ±5% time-warping on biophotonic streams
5. **Data collection priority:** If Tier 2 requires ≥90%, increasing trial count (3,600+/class) should be scoped

---

*SIM_018 Pass 4 Research Improvements. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
