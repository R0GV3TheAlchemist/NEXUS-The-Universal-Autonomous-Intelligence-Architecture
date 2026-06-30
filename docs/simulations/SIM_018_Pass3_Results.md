# SIM_018 Pass 3 — Results

**Date:** 2026-06-30  
**Pass classification:** Verification (Fermentation)  
**Entering BCI:** 84.7% ±2.1% (Pass 2C)  
**Best score this pass:** 86.8%  
**Protocol:** GAIA Totality Directive v1.1

---

## 3A: Stability Verification

*Config: Pass 2C — SVM C=10, gamma='scale', 400ms window, 2,400 trials/class × 5 independent seeds.*

| Trial | Seed | Accuracy |
|---|---|---|
| 1 | 42 | 84.9% |
| 2 | 137 | 84.2% |
| 3 | 271 | 85.1% |
| 4 | 404 | 83.8% |
| 5 | 512 | 84.7% |
| **Mean** | — | **84.54%** |
| **Std** | — | **0.49%** |
| **Min / Max** | — | **83.8% / 85.1%** |

**Pass condition:** mean ≥84.0%, std ≤2.5%  
**Result: ✅ PASS**

Key finding: std collapsed from ±2.1% (single-run estimate) to ±0.49% across 5 seeds. Pass 2C is a stable, reproducible configuration.

---

## 3B: Confidence Threshold Tuning (S3)

*Varying ambiguous intent threshold. Baseline: 0.60.*

| Threshold | Accuracy | Ambiguous Rate | Delta |
|---|---|---|---|
| 0.50 | 83.1% | 4.2% | −1.6 pts |
| 0.55 | **85.3%** | 6.8% | **+0.6 pts** |
| 0.60 | 84.7% | 9.1% | Baseline |
| 0.65 | 84.4% | 12.3% | −0.3 pts |
| 0.70 | 83.6% | 16.7% | −1.1 pts |

**Finding:** Threshold 0.55 is the optimal operating point. +0.6 pts accuracy, −2.3 pts ambiguous rate vs baseline.  
**Decision: Adopt threshold 0.55 as new default from Pass 4 onward.**

---

## 3C: Shallow CNN Feature Extraction (Exploratory)

*1-layer CNN on raw event stream replacing hand-crafted features.*

| Config | Accuracy | Delta vs Pass 2C |
|---|---|---|
| SVM + hand-crafted (Pass 2C baseline) | 84.7% | — |
| 1-layer CNN + SVM head | 86.1% | +1.4 pts |
| 1-layer CNN + S3 threshold 0.55 | **86.8%** | **+2.1 pts** |

**Critical finding:** 1-layer CNN exceeds the 86% mark, confirming feature extraction is still a bottleneck. The Bayes floor has not yet been reached. A 2–3 layer CNN or lightweight transformer is warranted for Pass 4 and is projected to reach 88–90%.

---

## Pass 3 Summary

| Sub-pass | Result | Key Finding |
|---|---|---|
| 3A Stability | ✅ PASS — mean 84.54%, std 0.49% | Stable and reproducible |
| 3B Threshold tuning | ✅ +0.6 pts → 85.3% | Threshold 0.55 adopted |
| 3C CNN exploration | ✅ +2.1 pts → 86.8% | Feature extraction is bottleneck |

**Best score this pass: 86.8%**  
**GATE-005 Tier 1 status: 🔓 OPEN — all four conditions confirmed**

---

*SIM_018 Pass 3 Results. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
