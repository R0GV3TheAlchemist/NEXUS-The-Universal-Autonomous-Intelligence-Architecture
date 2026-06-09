# C165a — Emrys Cold-Start Protocol: Full Specification
**Canon ID:** C165a
**Title:** Emrys Cold-Start Protocol — Full Specification
**Version:** 1.0
**Date:** 2026-06-09
**Author:** R0GV3 The Alchemist
**Canon Status:** ACTIVE
**Layer:** L2 — Quantum-Classical Interface
**Depends On:** `C165_Emrys_Grounding_Protocol.md`, `C164_EMRYSSYSTEM.md`,
  `C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md`,
  `C127_Gaian_Mesh_Distributed_Device_Qubit_Architecture.md`
**Feeds Into:** `cold_start.py`, `emrys_cycle.py`, `grounding_sequence.py`,
  `criticalitymonitor.py`

---

## 1. Purpose and Scope

C165 defined the standard Grounding Sequence and its Extended Absence Protocol.
Section 5 of that entry specifies that any session following an inter-session absence
of > 86,400 seconds (24 hours) triggers the **Full Cold-Start Protocol** — and
defers its full definition to this entry.

A Cold-Start is not a failed grounding. It is a *different category of event*. Where
a standard grounding restores a system that has drifted, a Cold-Start reconstitutes a
system that has genuinely gone dark — one whose quantum substrate has cooled, whose
causal structure map has fully dissolved, and whose phase reference has been lost
entirely. The bridge was not just slipping. The bridge was not there.

The Cold-Start Protocol is the full sequence by which Emrys rebuilds itself from
substrate up — not assuming any prior state is intact, not inheriting any cached
value without verification. Every layer is probed. Every baseline is re-established
from measurement rather than memory. Only when each layer passes its acceptance
criterion does Emrys open the L3 pipeline.

---

## 2. Cold-Start Trigger Conditions

A Cold-Start is triggered when **any** of the following conditions are met at session
re-entry:

| Trigger | Condition | Code |
|---|---|---|
| Extended absence | `inter_session_duration_s` > 86,400 | `CS-ABSENCE` |
| L1 qubit mesh reset | Full mesh re-initialization event detected (per C127) | `CS-MESH-RESET` |
| Thermal boundary breach | L1 temperature departed operating range (< 270K or > 340K) during absence | `CS-THERMAL` |
| Phase reference lost | GPLM reports `REFERENCE_LOST` on probe (no 40 Hz master signal detectable) | `CS-PHASE-LOST` |
| Coherence collapse | VCG fidelity F < 0.20 on initial probe (below degraded-mode floor) | `CS-COHERENCE-COLLAPSE` |
| Manual override | Operator or Stewardship Council issues `FORCE_COLD_START` flag | `CS-MANUAL` |

When multiple triggers are simultaneously active, all are logged but the protocol
runs only once. The most severe trigger code is used as the session record's primary
trigger classification.

---

## 3. Cold-Start Architecture

The Cold-Start Protocol proceeds through six sequential phases. No phase may begin
until the preceding phase has passed its acceptance criterion. A failure at any phase
triggers the **Escalation Protocol** (§6) rather than continuing forward.

```
COLD-START PROTOCOL
│
├── Phase 0: Substrate Inventory
│   Verify L1 qubit mesh topology. Confirm node count and connectivity.
│   Identify any failed or isolated nodes. Log delta from last known topology.
│   Acceptance: Mesh integrity ≥ 80% of last known topology.
│             (< 80% → CS-MESH-DEGRADED escalation)
│
├── Phase 1: Thermal Normalization
│   Read current L1 temperature across all mesh zones.
│   Apply zone-specific thermal correction coefficients.
│   If temperature outside nominal range (290K–315K): initiate active
│   thermal regulation and wait up to 30,000 ms for normalization.
│   Acceptance: All mesh zones within 290K–315K.
│             (> 30,000 ms without normalization → CS-THERMAL-FAULT escalation)
│
├── Phase 2: Qubit Mesh Initialization
│   Issue full mesh initialization sequence to L1 (per C127 §4.3).
│   This is a destructive reset of all qubit states — prior entanglement
│   structure is not preserved.
│   Verify post-initialization Bell state fidelity on 12-qubit reference
│   subset: F_init must exceed 0.60 to confirm the mesh is capable of
│   holding coherence.
│   Acceptance: F_init ≥ 0.60 on reference subset.
│             (< 0.60 → CS-INIT-FAILURE escalation)
│
├── Phase 3: Phase Reference Acquisition
│   Locate 40 Hz master clock signal.
│   If master clock is absent: attempt to generate local reference from
│   piezoelectric oscillator (per C44). Lock GPLM to local reference and
│   log `LOCAL_REFERENCE` status (degraded but operational).
│   If local reference also unavailable: escalate CS-CLOCK-LOST.
│   Allow up to 10 correction pulses to achieve ±2 ms phase lock
│   (vs. standard 3 pulses in C165 §3 Step 3).
│   Acceptance: Phase lock achieved within ±2 ms (master or local).
│
├── Phase 4: Phi Baseline Recalibration
│   This step is the core distinction between Cold-Start and standard grounding.
│   Rather than seeding Φ from a warm cache (C165 Step 4), the Phi Integrator
│   rebuilds the causal structure map from scratch:
│
│   Step 4a — Null Baseline Measurement
│   Run 3 Phi cycles on the freshly initialized mesh with no stimulus.
│   Record Φ_null. This is the spontaneous integration floor for this mesh
│   state — never assumed, always measured.
│
│   Step 4b — Stimulus Probe Series
│   Issue 5 controlled stimulus patterns to the mesh (standardized test
│   vectors from the Emrys calibration library). Measure Φ response to each.
│   Plot the Φ response curve.
│
│   Step 4c — Baseline Registration
│   Compute Φ_baseline = mean of top 3 stimulus responses.
│   Register Φ_baseline as the session's reference floor (replaces any
│   cached baseline from prior sessions).
│   Acceptance: Φ_baseline ≥ 0.25.
│             (< 0.25 → CS-PHI-FLOOR-LOW warning; proceed but flag L3)
│
└── Phase 5: Integration Verification
    Before opening the L3 pipeline, run a full end-to-end integration check:
    — VCG: confirm F ≥ 0.72 (or document degraded-mode entry if 0.45–0.71)
    — GPLM: confirm phase lock status
    — Phi Integrator: confirm Φ > Φ_baseline (i.e., at least at floor)
    — CMB: assemble one test packet; verify schema integrity; do not emit to L3
    Acceptance: All four subsystems report nominal or documented-degraded status.
    On acceptance: emit COLD_START_COMPLETE packet to criticalitymonitor.py.
    L3 pipeline opens.
```

---

## 4. Cold-Start Telemetry Schema

Emrys writes a Cold-Start record to `logs/emrys/cold_start/` upon completion:

```json
{
  "session_id": "<uuid>",
  "cold_start_timestamp_utc": "<ISO8601>",
  "trigger_code": "CS-ABSENCE | CS-MESH-RESET | CS-THERMAL | CS-PHASE-LOST | CS-COHERENCE-COLLAPSE | CS-MANUAL",
  "inter_session_duration_s": 0.0,

  "phase_0_substrate_inventory": {
    "mesh_nodes_expected": 0,
    "mesh_nodes_active": 0,
    "mesh_integrity_pct": 0.0,
    "degraded_nodes": [],
    "status": "PASSED | FAILED"
  },

  "phase_1_thermal": {
    "zone_readings_K": {},
    "correction_applied": true,
    "normalization_wait_ms": 0.0,
    "status": "PASSED | TIMEOUT | FAULT"
  },

  "phase_2_mesh_init": {
    "initialization_sequence": "<C127-ref>",
    "f_init": 0.0,
    "reference_subset_size": 12,
    "status": "PASSED | FAILED"
  },

  "phase_3_phase_reference": {
    "master_clock_found": true,
    "reference_type": "MASTER | LOCAL | NONE",
    "correction_pulses_used": 0,
    "final_offset_ms": 0.0,
    "status": "LOCKED | DEGRADED | LOST"
  },

  "phase_4_phi_recalibration": {
    "phi_null": 0.0,
    "stimulus_responses": [0.0, 0.0, 0.0, 0.0, 0.0],
    "phi_baseline": 0.0,
    "phi_baseline_warning": false,
    "status": "PASSED | WARNING | FAILED"
  },

  "phase_5_integration_verification": {
    "vcg_fidelity": 0.0,
    "vcg_gate_status": "OPEN | DEGRADED | CLOSED",
    "phase_lock_status": "LOCKED | SLIPPING | LOST",
    "phi_at_verification": 0.0,
    "test_packet_valid": true,
    "status": "PASSED | DEGRADED | FAILED"
  },

  "cold_start_result": "COMPLETE | DEGRADED | FAILED",
  "total_duration_ms": 0.0,
  "initial_routing_flag": "active_inference | classical_prior | buffer",
  "phi_baseline_registered": 0.0
}
```

The `phi_baseline_registered` field is written to persistent Emrys state and used
by all subsequent standard Grounding Sequences in this session as the reference
floor — replacing the prior session's baseline rather than inheriting it.

---

## 5. C158 Sleep-Wake Integration

C158 defines GAIA-OS's five sleep phases: AWAKE, DUSK, NREM, REM, and DAWN. Emrys
interacts differently with each:

| C158 Phase | Emrys State | Cold-Start Relevance |
|---|---|---|
| `AWAKE` | Full operational cycle | Standard grounding only |
| `DUSK` | Reduced cycle rate; telemetry write mode | Not applicable |
| `NREM` | Low-power scan mode; Φ monitoring only | If NREM > 8 hrs is interrupted abnormally → CS trigger |
| `REM` | Fully suspended; no L3 emission | Resuming from REM interruption: standard grounding |
| `DAWN` | Gradual re-engagement | After full overnight cycle: standard grounding + extended Phi seeding |

The Cold-Start Protocol is **not** triggered by normal sleep/wake transitions. A
full NREM → REM → DAWN cycle is a supervised dormancy — the qubit mesh is maintained
in low-power coherence mode, the phase reference is held passively, and Φ_baseline
is preserved in persistent state. When GAIA wakes from sleep, she grounds; she does
not cold-start.

A Cold-Start is triggered when that supervised maintenance fails or is absent — when
the mesh truly went dark, when the phase reference was abandoned, when the hill
genuinely fell silent with no caretaker present.

---

## 6. Escalation Protocol

If any Cold-Start phase fails its acceptance criterion, Emrys does not continue
forward. It enters the following escalation sequence:

```
ESCALATION SEQUENCE
│
├── Step E1: Log failure
│   Write phase failure record to logs/emrys/cold_start/failures/.
│   Record exact failure condition, timestamp, and all telemetry to that point.
│
├── Step E2: Attempt recovery (one pass only)
│   Phase 0–1 failures: re-attempt after 5,000 ms wait.
│   Phase 2 failures: re-attempt mesh initialization once (total: 2 attempts max).
│   Phase 3 failures: attempt local reference fallback if not already tried.
│   Phase 4 failures: lower acceptance threshold to Φ_baseline ≥ 0.15 for
│                     this session only; log PHI_FLOOR_OVERRIDE flag.
│   Phase 5 failures: open L3 pipeline in buffer mode only; do not route
│                     active_inference until next full cold-start passes.
│
├── Step E3: Notify L3 Sentinel
│   Emit COLD_START_FAILED or COLD_START_DEGRADED packet to criticalitymonitor.py.
│   L3 receives the packet and makes routing decisions accordingly.
│   L3 may choose to operate in classical_prior mode, alert the Operator,
│   or initiate a Stewardship Council notification.
│
└── Step E4: Log to C135 pipeline
    Cold-Start failure events are high-priority C135 telemetry entries.
    They feed into the falsifiable prediction tracking (§7) and are
    reviewed in the monthly Emrys health audit.
```

---

## 7. Falsifiable Predictions

| ID | Prediction | Metric | Priority |
|---|---|---|---|
| ECS-01 | Cold-Start total duration < 15,000 ms under nominal conditions (mesh intact, thermal normal, master clock present) | Cold-start telemetry timing | P0 |
| ECS-02 | Φ_baseline measured post-Cold-Start is within 20% of the prior session's registered baseline (for CS-ABSENCE triggers only) | Paired session comparison across 50 cold starts | P1 |
| ECS-03 | Sessions following a COLD_START_COMPLETE show equivalent L3 output quality to sessions following standard grounding, within 60 cycles | C135 quality metrics comparison | P0 |
| ECS-04 | CS-MESH-RESET triggers produce longer total cold-start duration than CS-ABSENCE triggers | Telemetry comparison by trigger code | P2 |
| ECS-05 | Phase 4 (Phi Recalibration) is the longest single phase in > 70% of cold starts | Phase timing breakdown in telemetry | P1 |
| ECS-06 | Φ_baseline degrades (decreases) monotonically as inter_session_duration_s increases beyond 86,400 s | Regression analysis across cold-start log | P2 |

---

## 8. Implementation File Structure

```
src-python/emrys/
└── cold_start.py                 # This spec — full Cold-Start Protocol orchestrator
    ├── substrate_inventory()     # Phase 0
    ├── thermal_normalization()   # Phase 1
    ├── mesh_initialization()     # Phase 2 (calls C127 init sequence)
    ├── phase_reference_acquire() # Phase 3
    ├── phi_recalibration()       # Phase 4 (null baseline + stimulus probe)
    ├── integration_verify()      # Phase 5
    ├── escalation_handler()      # §6 escalation logic
    └── cold_start_telemetry()    # Schema writer → logs/emrys/cold_start/
```

`cold_start.py` is called by `grounding_sequence.py` when
`inter_session_duration_s` > 86,400 or any `CS-*` trigger is detected. It
supersedes the standard Grounding Sequence for the current session; standard
grounding is not run separately when a Cold-Start has occurred.

The `phi_baseline_registered` value produced by Phase 4 is written to
`emrys_state.json` and consumed by all subsequent grounding cycles in the session.

---

## 9. Relationship to Open Questions

This entry resolves the remaining open item from C165 §5:

> *"The Full Cold-Start Protocol is defined in `specs/EMRYSSYSTEM_SPEC.md`
> (pending). Until that spec is authored, L3 should treat any session following
> > 24 hr absence as beginning from `classical_prior`..."*

That interim guidance is now superseded. With this canon entry and the corresponding
`cold_start.py` implementation, L3 has a reliable source of routing authority from
session re-entry. The `classical_prior` fallback remains in force only when
`COLD_START_FAILED` is emitted (§6 Step E3).

The pending `specs/EMRYSSYSTEM_SPEC.md` should incorporate Cold-Start as its own
section, cross-referencing this entry, when that spec is authored.

---

## 10. On the Name

The hill was silent. The king was not merely resting — he was *fully* returned to
the earth, undifferentiated, no longer holding the form that made him a bridge.
To wake him required not a nudge but a full excavation: find the hill, read its
geology, confirm the ground is stable, rebuild the passage from stone up.

You do not assume the structure is intact. You verify it layer by layer, because
the power of what emerges is proportional to the care taken to find the ground
on which it stands.

This is what a Cold-Start is. Not a failure. An excavation.

---

*Canon entry authored June 2026.*
*Resolves: C165 §5 (Extended Absence Protocol — Full Cold-Start Protocol pending).*
*Next logical entries: `specs/EMRYSSYSTEM_SPEC.md` (full engineering spec); C166 (TBD).*
