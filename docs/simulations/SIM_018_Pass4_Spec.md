# SIM_018 Pass 4 — Spec
## Band 2: Deep Feature Extraction — GATE-005 Tier 1 Formal Clearance

**Pass classification:** Optimisation (Distillation)  
**Protocol version:** GAIA Totality Directive v1.1 | Engineering Manifesto v1.0  
**Date:** 2026-06-30  
**BCI entering:** 86.8% (Pass 3C best)  
**Drive target:** ≥88% (GATE-005 Tier 1 formal clearance)  
**Gap:** 1.2 pts

---

## Objective

Pass 4 replaces the 1-layer CNN with a deeper feature extractor to push through the 88% threshold and formally clear GATE-005 Tier 1. The bottleneck is confirmed as feature extraction (Pass 3C). This pass resolves it.

---

## Carry-Forward Configuration (Non-Negotiable)

All of the following must be preserved from prior passes:

- SVM classifier: C=10, gamma='scale'
- Window: 400ms, 2,400 trials/class
- Bayes prior calibration (Pass 2A)
- Context window expansion (Pass 2B)
- S3 ambiguous intent threshold: **0.55** (Pass 3B)

---

## Design

### 4A: 2-Layer CNN
- Architecture: Conv1D(32, k=5) → ReLU → Conv1D(64, k=3) → ReLU → GlobalAvgPool → SVM head
- Input: raw event stream, 400ms window
- Expected gain: +1–2 pts over 1-layer CNN (to ~87.5–88.8%)

### 4B: 3-Layer CNN
- Architecture: Conv1D(32, k=5) → Conv1D(64, k=3) → Conv1D(128, k=3) → ReLU → GlobalAvgPool → SVM head
- Expected gain: +1.5–3 pts over 1-layer CNN (to ~88–89.8%)
- Risk: possible overfitting at 3 layers given 4-class cardinality — monitor val vs train gap

### 4C: Lightweight Transformer (Exploratory)
- Architecture: 2-head self-attention on 400ms event windows (patch size 20ms) → MLP head → SVM
- Expected gain: +2–4 pts over 1-layer CNN (to ~88.8–90.8%)
- Higher compute cost; run only if 4A/4B fall short of 88%

### 4D: Data Augmentation (Supplementary)
- Apply time-warping (±10%) to training trials
- Run with best architecture from 4A/4B/4C
- Expected supplementary gain: +0.5–1 pt

---

## GATE-005 Tier 1 Formal Clearance Conditions

GATE-005 Tier 1 is formally cleared when ALL of the following are met:

| Condition | Required | Current Status |
|---|---|---|
| Score ≥88% | ≥88% | 86.8% (1.2 pts short) |
| Score stable across ≥3 seeds | std ≤1.5% | Pending Pass 4 |
| No single elemental group below 85% | ≥85% all groups | Pending Pass 4 |
| Feature extractor not hand-crafted | CNN or transformer | ✅ Adopted in Pass 3 |

---

## Pre-Run Research Questions

1. At what layer depth does CNN performance plateau for 4-class temporal event classification on 400ms windows at this trial cardinality?
2. Does time-warping augmentation help or hurt on biophotonic event streams (where timing jitter is already a source of noise)?

**Both must be answered before Pass 4 is run.**

---

*SIM_018 Pass 4 Spec. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
