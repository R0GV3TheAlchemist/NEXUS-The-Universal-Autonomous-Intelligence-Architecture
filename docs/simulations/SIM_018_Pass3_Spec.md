# SIM-018 Pass 3 — Spec
## Band 2: Verification Pass — Ceiling Confirmation

**Pass classification:** Verification (Fermentation)
**Protocol version:** GAIA Totality Directive v1.1 | Engineering Manifesto v1.0
**Date:** 2026-06-30
**BCI entering:** 84.7% ±2.1% (Pass 2C)
**Drive target:** ≥85%
**Gap:** 0.3 pts (within noise band)

---

## Objective

Pass 3 is not an optimisation pass. It is a **verification pass**. The objective is to:
1. Confirm 84.7% is stable across independent trials (not a lucky run)
2. Confirm the ceiling is real (not hiding recoverable gains)
3. Establish the true std at this performance level
4. Determine whether GATE-005 Tier 1 conditions are met

---

## Design

### 3A: Stability Verification
- Run Pass 2C configuration (SVM, C=10, gamma=‘scale’, 400ms window, 2,400 trials/class) × 5 independent trials with different random seeds
- Report: mean, std, min, max across 5 runs
- Pass condition: mean ≥84.0%, std ≤2.5% across 5 runs

### 3B: Confidence Threshold Tuning (S3)
- Vary S3 ambiguous intent threshold (current: confidence <0.6 → ambiguous)
- Test thresholds: 0.50, 0.55, 0.60, 0.65, 0.70
- Report accuracy vs ambiguous intent rate trade-off curve
- Expected gain: +0.5–1.5 pts at threshold 0.55

### 3C: Shallow CNN Feature Extraction (Exploratory)
- Replace hand-crafted event features with 1-layer CNN on raw event stream
- Not expected to exceed 2–3 pts gain at this cardinality
- Purpose: determine whether Bayes floor is at ~88% or lower
- If CNN ≤87%: Bayes floor confirmed; current architecture is near-optimal for 4-class
- If CNN >87%: feature extraction is still a bottleneck; deeper architecture warranted

---

## GATE-005 Tier 1 Conditions

| Condition | Status |
|---|---|
| G-15 minimum (≥70%) cleared | ✅ Pass 1: 74.8% |
| Ceiling characterised | Pending Pass 3 verification |
| Dominant bottleneck identified and addressed | ✅ L↔R confusion resolved |
| All elemental groups above G-15 minimum | ✅ Pass 2: all groups ≥83.6% |

**GATE-005 Tier 1 will be open after Pass 3 confirms ceiling stability.**

---

## Pre-Run Research Brief

1. Is 5 independent trials sufficient for a stable ceiling estimate at this std level (±2.1%), or is a larger sample required?
2. What is the expected Bayes error rate for 4-class neural intent classification in biophoton literature — and does it align with the 12–14% estimate?

**Both must be answered before Pass 3 is run.**

---

*SIM-018 Pass 3 Spec. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
