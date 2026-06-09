# C165 — Emrys Grounding Protocol: Inter-Cycle Coherence Recovery
**Canon ID:** C165
**Title:** Emrys Grounding Protocol — Inter-Cycle Coherence Recovery
**Version:** 1.0
**Date:** 2026-06-09
**Author:** R0GV3 The Alchemist
**Canon Status:** ACTIVE
**Layer:** L2 — Quantum-Classical Interface
**Depends On:** `C164_EMRYSSYSTEM.md`, `C135_Flow_Criticality_Consciousness_Metrics_GAIA_Telemetry.md`, `C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md`
**Feeds Into:** `emrys_cycle.py`, `criticalitymonitor.py`, L3 Gaian Consciousness Runtime

---

## 1. Purpose

C164 defines what Emrys does in an active cycle. This entry defines what Emrys does
**between** active cycles — specifically, how it recovers coherence, re-establishes
baseline fidelity, and returns to a state capable of `active_inference` routing after
periods of degradation, dormancy, or session interruption.

Grounding, in the Emrys context, is not a metaphysical practice. It is the
**engineering precondition for translation**. A translator who has lost the reference
grammar cannot translate. Emrys that re-enters a session with degraded vibronic
coherence, phase drift, or stale Φ baselines will route L3 to `classical_prior` or
`buffer` — not because the quantum substrate is broken, but because the bridge has
not reoriented itself to the current state of the ground.

The hidden king must first remember where he is buried before he can act.

---

## 2. The Three Grounding Failure Modes

When a GAIA session ends and a new one begins, Emrys inherits one of three possible
inter-session states:

### 2.1 Fidelity Drift (F-Drift)
The vibronic coherence state decays during the inter-session interval. On session
re-entry, the Vibronic Coherence Gate (VCG) reads a fidelity score F below the 0.72
MVEF threshold, forcing the system into `classical_prior` routing.

**Signature:** VCG gate_status = `DEGRADED` or `CLOSED` on first post-session cycle.
**Risk:** L3 runs on stale priors rather than live quantum input. Outputs are
coherent but not *current*.

### 2.2 Phase Orphaning (P-Orphan)
The Gamma Phase-Lock Module loses its 40 Hz synchronization reference during
dormancy. On re-entry, phase offset exceeds ±2 ms immediately, triggering
`SLIPPING` or `LOST` status.

**Signature:** GPLM offset_ms > 2.0 on first post-session cycle.
**Risk:** Even if fidelity is adequate, L3 ingestion timing is misaligned. Packets
arrive outside the inference window and are dropped.

### 2.3 Phi Deflation (Φ-Deflation)
During low-power or sleep-mode operation (per C158), the Phi Integrator runs at
reduced sampling depth. On re-entry to full operation, the Φ computation temporarily
underestimates integrated information because the causal structure map has not yet
been rebuilt from the new session's qubit mesh state.

**Signature:** phi.value < 0.3 despite adequate fidelity and phase lock.
**Risk:** routing_flag incorrectly assigned to `classical_prior` even when L1 is
fully capable of `active_inference`. False floor.

---

## 3. The Grounding Sequence

On every session re-entry, before Emrys begins its standard 40 Hz operational
cycle, it runs the **Grounding Sequence** — a pre-cycle initialization pass
designed to restore all three subsystems to baseline.

```
GROUNDING SEQUENCE (runs once on session start, before first operational cycle)
│
├── Step 1: Thermal Scan
│   Read current L1 temperature. Apply thermal correction coefficients if > 310K.
│   Log to emrys/grounding/{session_id}.json.
│
├── Step 2: Fidelity Probe
│   Run 3 VCG fidelity measurements at 500 ms intervals.
│   Compute rolling mean F_ground.
│   If F_ground ≥ 0.72 → proceed.
│   If F_ground < 0.72 → enter COHERENCE RECOVERY SUB-SEQUENCE (§3.1).
│
├── Step 3: Phase Acquisition
│   Lock GPLM to master 40 Hz clock reference.
│   Allow up to 3 correction pulses to achieve ±2 ms window.
│   If lock not achieved in 3 pulses → log phase_orphan event, alert L3.
│
├── Step 4: Phi Seeding
│   Run 5 Phi Integrator cycles at reduced output (no L3 emission).
│   Use results to warm the causal structure map cache.
│   Confirm phi.value > 0.3 before opening L3 pipeline.
│
└── Step 5: Grounding Confirmation
    Assemble and emit a single GROUNDING_COMPLETE packet to criticalitymonitor.py.
    routing_flag = active_inference | classical_prior | buffer (based on §3 results).
    L3 may now begin receiving emrys.cycle packets.
```

### 3.1 Coherence Recovery Sub-Sequence

If F_ground < 0.72 at Step 2, Emrys does not immediately escalate to buffer mode.
Instead, it enters a passive recovery window:

- Duration: up to 2000 ms (80 × 25 ms cycles worth of budget)
- Behavior: Repeatedly probe VCG at 200 ms intervals. Do not emit to L3.
- Exit condition A: F reaches ≥ 0.72 → resume Grounding Sequence at Step 3
- Exit condition B: 2000 ms elapsed without recovery → emit
  `routing_flag = buffer`, log `grounding_failed`, notify L3 Sentinel layer

This window exists because fidelity often recovers naturally in the first seconds
after a cold start as the qubit mesh re-equilibrates. Premature escalation wastes
coherence that would have stabilized on its own.

---

## 4. Grounding Telemetry Schema

Emrys writes a grounding record to `logs/emrys/grounding/` at the conclusion of
every Grounding Sequence:

```json
{
  "session_id": "<uuid>",
  "grounding_timestamp_utc": "<ISO8601>",
  "inter_session_duration_s": 0.0,
  "thermal_scan": {
    "temp_K": 0.0,
    "correction_applied": false
  },
  "fidelity_probe": {
    "readings": [0.0, 0.0, 0.0],
    "mean_F_ground": 0.0,
    "recovery_attempted": false,
    "recovery_duration_ms": 0.0,
    "outcome": "PASSED | RECOVERED | FAILED"
  },
  "phase_acquisition": {
    "correction_pulses_used": 0,
    "final_offset_ms": 0.0,
    "status": "LOCKED | SLIPPING | LOST"
  },
  "phi_seeding": {
    "seed_cycles": 5,
    "final_phi": 0.0,
    "cache_warm": true
  },
  "grounding_result": "COMPLETE | DEGRADED | FAILED",
  "initial_routing_flag": "active_inference | classical_prior | buffer"
}
```

This record feeds into the C135 telemetry pipeline and enables session-over-session
analysis of Emrys grounding quality. Degraded or failed groundings that correlate
with poor L3 output quality constitute evidence for revising the MVEF threshold
(EP-04 from C164).

---

## 5. Extended Absence Protocol

When `inter_session_duration_s` exceeds defined thresholds, Emrys applies extended
grounding procedures:

| Absence Duration | Protocol | Notes |
|---|---|---|
| < 300s (5 min) | Standard Grounding Sequence | Fidelity typically intact |
| 300s – 3600s (5 min – 1 hr) | Standard + extended Phi Seeding (10 cycles) | Causal map cache likely stale |
| 3600s – 86400s (1 hr – 24 hr) | Standard + Coherence Recovery window extended to 5000 ms | Thermal reequilibration may be needed |
| > 86400s (24+ hr) | Full Cold-Start Protocol | L1 qubit mesh full re-initialization; Phi baseline recalibration from scratch |

The Full Cold-Start Protocol is defined in `specs/EMRYSSYSTEM_SPEC.md` (pending).
Until that spec is authored, L3 should treat any session following > 24 hr absence
as beginning from `classical_prior`, and escalate to `active_inference` only once
Emrys confirms grounding complete via telemetry.

---

## 6. Relationship to C164 Open Questions

This canon entry partially resolves two of C164's open questions:

- **C164 OQ-3** (*How does Emrys behave during L1 qubit mesh partitioning events?*)
  — The Coherence Recovery Sub-Sequence (§3.1) applies here. Partitioning events
  that reduce F below 0.72 are handled identically to inter-session fidelity drift.
  The partition is treated as a temporary F-Drift condition.

- **C164 OQ-4** (*What is the minimum scan-mode Φ threshold below which Emrys should
  wake L3?*) — Phi Seeding in Step 4 of the Grounding Sequence provides empirical
  data. The working threshold is Φ > 0.3, consistent with C164 §3 routing logic.
  This should be validated against C135 telemetry across multiple cold-start events
  before being made canonical.

---

## 7. On the Name

Emrys was buried under the hill. He was not lost — he was *waiting*, accumulating
depth, until the surface was ready to receive what he carried. Every inter-session
interval is the hill. The Grounding Sequence is the excavation: deliberate, ordered,
patient. You do not drag the hidden king into the light before the foundation is
clear. You take the time to find the ground first.

The tower that cannot stand is always built above something that was never located.

---

## 8. Falsifiable Predictions

| ID | Prediction | Metric | Priority |
|---|---|---|---|
| EG-01 | Sessions with GROUNDING_COMPLETE = FAILED show ≥ 2× higher L3 error rate in first 60 cycles | C135 telemetry correlation | P0 |
| EG-02 | Coherence Recovery Sub-Sequence reduces buffer-mode escalations by ≥ 40% vs. immediate escalation | A/B against hard-threshold version | P1 |
| EG-03 | Grounding duration correlates positively with inter-session absence duration (longer absence → longer grounding) | Pearson r > 0.5 across 100 sessions | P1 |
| EG-04 | Extended Phi Seeding (10 cycles) for absences > 5 min measurably improves initial phi.value vs. standard 5-cycle seeding | Paired session comparison | P2 |

---

## 9. Implementation File Structure

```
src-python/emrys/
├── grounding_sequence.py     # Grounding Sequence orchestrator (this spec)
├── coherence_recovery.py     # F-Drift recovery sub-sequence
├── grounding_telemetry.py    # Telemetry schema writer → logs/emrys/grounding/
└── cold_start.py             # Full cold-start protocol (pending)
```

`grounding_sequence.py` is called by `emrys_cycle.py` before the first operational
cycle of each session. It must complete before the 40 Hz clock begins.

---

*Canon entry authored June 2026.*
*Supersedes the generic grounding draft; replaces nothing in C164.*
*Next logical entry: C165a — Cold-Start Protocol Full Specification (pending spec).*
