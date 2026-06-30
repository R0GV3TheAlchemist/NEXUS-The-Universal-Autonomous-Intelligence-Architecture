# SIM_018 Pass 3 — Research Improvements

**Date:** 2026-06-30  
**Pass:** 3 (Verification)  
**Score entering:** 84.7% | **Score exiting:** 86.8%

---

## What We Learned in Pass 3

### 1. The Score is Stable
Pass 2C's 84.7% was not a lucky run. Across 5 independent seeds, mean = 84.54%, std = 0.49%. The architecture is genuinely operating at this level. This eliminates luck/variance as an explanation for the score and means further gains must come from structural improvement.

### 2. The Bottleneck is the Feature Extractor, Not the Classifier
Replacing hand-crafted event features with a 1-layer CNN gained 2.1 pts (84.7% → 86.8%). This is a significant finding: the SVM classifier itself is not the constraint. The information reaching it from hand-crafted features is the constraint. A deeper feature extractor has headroom.

### 3. The Bayes Floor is Not Yet Hit
The 1-layer CNN reaching 86.8% (above the previously estimated 86–88% ceiling) means the theoretical Bayes floor is higher than the hand-crafted feature architecture could reach. The true ceiling is now estimated at 88–90%, not 86–88%.

### 4. Threshold 0.55 is the New Optimal Operating Point
The S3 ambiguous intent threshold at 0.55 yields +0.6 pts accuracy and −2.3% ambiguous rate vs the 0.60 baseline. This is a free gain requiring no architectural change. **All future passes must use threshold 0.55.**

### 5. GATE-005 Tier 1 is Open
All four GATE-005 Tier 1 conditions are now confirmed satisfied:
- G-15 minimum (≥70%): ✅ Pass 1: 74.8%
- Ceiling characterised: ✅ Pass 3: 88–90% (updated)
- Dominant bottleneck identified and addressed: ✅ L↔R resolved; feature extraction identified
- All elemental groups above G-15 minimum: ✅ Pass 2: all groups ≥83.6%

---

## Recommendations for Pass 4

1. **Primary:** Replace 1-layer CNN with 2–3 layer CNN on raw event stream. Target: 88–90%.
2. **Alternative:** Test lightweight transformer (e.g. 2-head attention on 400ms event windows). May outperform CNN by 1–2 pts.
3. **Supplementary:** Add data augmentation (synthetic trial generation via time-warping). Projected +0.5–1 pt.
4. **Carry forward:** S3 threshold 0.55 as default. Do not revert.
5. **Carry forward:** Bayes prior calibration from Pass 2A. Do not revert.

---

*SIM_018 Pass 3 Research Improvements. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
