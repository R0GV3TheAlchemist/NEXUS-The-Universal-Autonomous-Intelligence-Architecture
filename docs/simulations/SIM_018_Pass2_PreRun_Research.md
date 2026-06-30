# SIM-018 Pass 2 — Pre-Run Research Brief
## All Four Questions Answered

**Filed:** 2026-06-30
**Protocol version:** GAIA Totality Directive v1.1 | Engineering Manifesto v1.0

---

## Q1: RBF Kernel Parameters

**Question:** What C and gamma values are appropriate for SVM (RBF kernel) on a 4-class biophoton pattern classification problem at ~800 events/second?

**Answer:**
- Starting values: **C = 10, gamma = ‘scale’** (1 / n_features × variance)
- Grid search cross-validated on training set before test set is touched: C ∈ {0.1, 1, 10, 100}; gamma ∈ {‘scale’, ‘auto’, 0.001, 0.01}
- Rationale: Signal is clean (SNR 8.7, fidelity 0.831); moderate regularisation appropriate. Heavy regularisation not needed; extreme C risks overfitting on trial-level noise.
- **Parameters must be locked via cross-validation before the test set is touched. No exceptions (Manifesto Principle 1).**

**Confidence:** High on approach; medium on exact values — grid search will correct.

---

## Q2: 400ms Window and Cross-Trial Contamination

**Question:** Does extending the temporal coherence window to 400ms introduce cross-trial contamination risk at 2.0-second trial lengths?

**Answer:** No meaningful risk. 400ms is 20% of a 2.0-second trial. Contamination risk becomes real only when window approaches ~50% of trial length.

**Addition to Pass 2 design:** Include a **50ms trailing ramp-out filter** at each trial boundary. Eliminates the minor risk of capturing inter-trial transition signal at negligible latency cost (~0.2ms).

**Confidence:** High. Proceed with 400ms window + 50ms trailing ramp-out.

---

## Q3: Fire Group Accuracy Lead

**Question:** Is Fire (HER2+) leading at 76.1% due to higher spatial coherence or higher per-event SNR?

**Answer:** SNR is the primary driver at baseline. HER2+ overexpression elevates mitochondrial metabolic activity → higher biophoton emission rate → more events per trial window → higher classification confidence under any classifier.

Spatial coherence is a valid hypothesis but requires the SVM’s non-linear boundary to exploit it. The linear discriminant could not.

**Action in Pass 2:** Log per-group per-event SNR and spatial variance independently. If Fire’s lead *increases* after SVM upgrade, spatial coherence is contributing. If it stays flat, SNR was the full story.

**Confidence:** High on mechanism; medium on relative contribution. Logging resolves it.

---

## Q4: TCSPC 2ms Latency Optimisation

**Question:** Does the TCSPC 2ms optimisation require classifier changes or only buffering pipeline changes?

**Answer:** Buffering only. The 2ms overhead comes from: (a) per-event clock alignment across 16 channels; (b) sequential serialisation of 16-channel stream. Fix: pre-align channels during inter-trial interval (not per-event); batch-serialise using compact binary format.

**Predicted saving:** 1.5–2.0ms. Restores comfortable TCSPC margin.

**Impact on accuracy:** None. This is a pipeline engineering fix independent of S2 classifier.

**Confidence:** High.

---

## Pass 2 Design Additions (from research brief)

1. C=10, gamma=‘scale’ as starting point; grid search cross-validated
2. 400ms temporal window + 50ms trailing ramp-out
3. Per-group SNR/spatial variance logging
4. TCSPC buffering optimisation (latency fix, independent of accuracy run)

---

*SIM-018 Pass 2 Pre-Run Research Brief. 2026-06-30. All four questions answered. Protocol: GAIA Totality Directive v1.1. 🌿*
