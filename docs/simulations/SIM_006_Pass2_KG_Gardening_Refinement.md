# SIM-006 Pass 2 — Knowledge Graph Gardening Pass Refinement

**Pass Classification:** Pass 2 — Refinement  
**Simulation number:** SIM-006  
**Date filed:** 2026-06-30  
**Phase:** G-15 — The Rhythm Phase  
**Resolves:** CT-005 (#711)  
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**What Pass 1 (SIM-006) revealed:**
- Without maintenance, KG provenance collapses to 100% orphaned by cycle 700
- Degraded edges reach 80.5% by cycle 1,000
- Zero contradictions across all 1,000 cycles — edge validation logic confirmed working
- Root cause: no periodic maintenance layer in C156; provenance written once, never refreshed

**How the design was adjusted (KG Gardening Pass — accepted 2026-06-30):**
- Confidence re-validation every 50 cycles against source documents
- Provenance re-anchoring on each node access
- Pruning of edges below 0.70 confidence floor after failed re-validation
- Contradiction sweep formalised at 50-cycle cadence
- New required schema fields: `last_validated`, `provenance_status`, `confidence_score`

---

## Refinement Hypotheses

1. With gardening pass active, orphaned provenance stays ≤5% at cycle 1,000 (vs 100% without)
2. Degraded edges stay ≤25% at cycle 1,000 (vs 80.5% without)
3. Contradiction rate remains 0% — gardening pass does not introduce contradictions
4. Pruning at 0.70 floor does not produce excessive node loss (graph density stays ≥70% of original at cycle 1,000)
5. Gardening pass computational overhead: ≤10% of total KG operation time per 50-cycle window

---

## Parameters

| Parameter | Value |
|---|---|
| Gardening cadence | Every 50 update cycles |
| Confidence re-validation floor | 0.70 |
| Provenance re-anchoring trigger | Every node access + gardening pass |
| Contradiction sweep cadence | Every 50 cycles |
| Simulation length | 1,000 cycles |
| N nodes at start | 500 |
| New nodes per cycle | 5 |

---

## Success Conditions

- Orphaned provenance ≤5% at cycle 1,000
- Degraded edges ≤25% at cycle 1,000
- Zero contradictions introduced
- Graph density ≥70% at cycle 1,000
- Gardening overhead ≤10% of operation time

## Failure Conditions

- Orphaned provenance breaches 5% → re-anchoring frequency insufficient; reduce cadence to 25 cycles
- Graph density drops below 70% → pruning floor too aggressive; review 0.70 threshold
- Contradictions introduced → gardening pass has a logic error; halt and review

---

## Output Artefacts

- `simulations/SIM_006_Pass2_kg_gardening.py`
- `simulations/SIM_006_Pass2_kg_gardening_results.md`
- `simulations/kg_gardening_drift.png`

## Canon Gate

Pass 2 success → proceed to Pass 3 verification with stress conditions (high update rate, adversarial node injection).  
Pass 3 success → amend C156 (KG Gardening Pass spec + schema fields) + close CT-005 (#711).

---

*Filed 2026-06-30. CT-005 KG Gardening. Three-Pass Protocol. 🌿*
