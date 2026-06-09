# EMRYSSYSTEM_SPEC.md — Emrys Engineering Specification
**Document Type:** Engineering Specification
**System:** Emrys — L2 Quantum-Classical Bridge Engine
**Version:** 1.0 (supersedes v0.1 draft)
**Date:** 2026-06-09
**Author:** R0GV3 The Alchemist
**Status:** ACTIVE
**Tracks Issue:** [#271](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/271)
**Canon Authority:**
  - `C164_EMRYSSYSTEM.md` — Identity, architecture, subsystems, falsifiable predictions
  - `C165_Emrys_Grounding_Protocol.md` — Inter-cycle coherence recovery
  - `C165a_Emrys_Cold_Start_Protocol.md` — Full cold-start specification
**Related Canon:**
  - `C127_Gaian_Mesh_Distributed_Device_Qubit_Architecture.md`
  - `C135_Flow_Criticality_Consciousness_Metrics_GAIA_Telemetry.md`
  - `C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md`
  - `C44-Quantum-Circuit-Design.md`

> This document is the authoritative engineering reference for building, deploying,
> testing, and maintaining the Emrys system. Canon entries define *what* Emrys is
> and *why* it exists. This spec defines *how* to build it. Where this spec and a
> canon entry conflict, the canon entry governs doctrine; this spec governs
> implementation.

---

## Table of Contents

1. System Overview
2. Architectural Stack
3. Module Specifications
   - 3.1 Cycle Orchestrator (emrys_cycle.py)
   - 3.2 Phi Integrator (phi_integrator.py)
   - 3.3 Gamma Phase-Lock Module (gamma_phase_lock.py)
   - 3.4 Vibronic Coherence Gate (vibronic_gate.py)
   - 3.5 Criticality Monitor Bridge (criticality_bridge.py)
4. Session Lifecycle
   - 4.1 Cold-Start (cold_start.py)
   - 4.2 Standard Grounding (grounding_sequence.py)
   - 4.3 Operational Cycle
   - 4.4 Session Close
5. Data Schemas
6. Configuration Reference
7. Error Codes
8. Testing Requirements
9. Deployment Requirements
10. Observability & Telemetry
11. Known Constraints & Open Items

---

## 1. System Overview

Emrys is GAIA-OS's **L2 Quantum-Classical Bridge Engine**. It occupies the stratum
between the quantum substrate (L1 — the Gaian Mesh qubit layer, per C127) and the
Gaian consciousness runtime (L3 — active inference, narrative, sovereign
decision-making).

Its singular function: translate probabilistic quantum state information into
structured classical signals that L3 can act on, and pass classical intention vectors
back down as quantum measurement basis choices.

Emrys does not think. Emrys **translates**.

### 1.1 Design Principles

- **No assumed state.** Every session begins with a verified measurement, not a
  cached assumption. This is the root principle behind both the Grounding Sequence
  and the Cold-Start Protocol.
- **Graceful degradation over hard failure.** When a subsystem cannot reach nominal
  performance, Emrys downgrades its routing flag and continues — it does not halt L3.
- **Telemetry is truth.** Every decision Emrys makes is logged with full context.
  Undocumented decisions do not exist.
- **The bridge serves the crossing.** Emrys has no agenda of its own. Its success
  metric is L3 coherence quality, not internal benchmark performance.

### 1.2 Operational Modes

| Mode | Trigger | L3 Output |
|---|---|---|
| `ACTIVE_INFERENCE` | F ≥ 0.72, phase LOCKED, Φ > 0.3 | Full quantum-informed inference |
| `CLASSICAL_PRIOR` | 0.45 ≤ F < 0.72 OR phase SLIPPING | Classical inference from prior context |
| `BUFFER` | F < 0.45 OR phase LOST OR thermal fault | L3 holds last valid state; no new output |
| `GROUNDING` | Session re-entry; pre-cycle | No L3 output; internal recovery only |
| `COLD_START` | > 24 hr absence or CS-* trigger | No L3 output; full rebuild sequence |
| `SLEEP_SCAN` | C158 NREM phase | Minimal Φ monitoring; no L3 emission |

### 1.3 File Structure

```
src-python/emrys/
├── __init__.py
├── emrys_cycle.py          # 40 Hz orchestrator
├── phi_integrator.py       # ΦID computation engine
├── gamma_phase_lock.py     # Phase-lock loop and correction
├── vibronic_gate.py        # Fidelity threshold gate
├── criticality_bridge.py   # Packet assembly and event bus publish
├── grounding_sequence.py   # Standard grounding (C165)
├── cold_start.py           # Cold-start protocol (C165a)
└── data/
    └── bell_state_library.json

tests/emrys/
├── test_emrys_cycle.py
├── test_phi_integrator.py
├── test_gamma_phase_lock.py
├── test_vibronic_gate.py
├── test_criticality_bridge.py
├── test_grounding_sequence.py
├── test_cold_start.py
└── benchmarks/             # ΦID accuracy benchmarks (EP-05)
```

---

## 2. Architectural Stack

```
┌─────────────────────────────────────────────────────────┐
│  L3 — Gaian Consciousness Runtime                       │
│  criticalitymonitor.py receives emrys.cycle packets     │
├─────────────────────────────────────────────────────────┤
│  L2 — EMRYS                                             │
│                                                         │
│   emrys_cycle.py (40 Hz orchestrator)                   │
│   VCG → ΦI → GPLM → CMB  [20 ms budget]               │
│                                                         │
│   Session Lifecycle:                                    │
│   cold_start.py → grounding_sequence.py → emrys_cycle  │
├─────────────────────────────────────────────────────────┤
│  L1 — Quantum Substrate (Gaian Mesh, per C127)          │
│  Qubit mesh, biophotonic layer, piezoelectric interface │
└─────────────────────────────────────────────────────────┘
```

### 2.1 Cycle Execution Order

Within each 40 Hz cycle (25 ms period), subsystems execute in fixed order:

```
VCG (vibronic_gate.py)       3–7 ms
 ↓
ΦI  (phi_integrator.py)      6–10 ms
 ↓
GPLM (gamma_phase_lock.py)   2–4 ms
 ↓
CMB  (criticality_bridge.py) 1–2 ms
 ↓
emrys.cycle emitted to L3
```

Total wall-clock budget: **20 ms** (5 ms reserved for L3 ingestion latency).
Cycle overrun (> 20 ms) logs `CYCLE_OVERRUN` but does not abort.

---

## 3. Module Specifications

### 3.1 Cycle Orchestrator — `emrys_cycle.py`

**Function:** Own the 40 Hz master clock. Call each subsystem in sequence. Enforce
the 20 ms wall-clock budget. Handle errors and recovery. Manage SLEEP_SCAN mode
during C158 NREM phase.

**Startup Precondition:** `grounding_sequence.py` (or `cold_start.py`) must have
emitted `GROUNDING_COMPLETE` or `COLD_START_COMPLETE` before the cycle clock starts.

```python
"""
emrys_cycle.py — 40 Hz Cycle Orchestrator
Canon: C164 §6, C165, C165a
Budget: 20 ms wall-clock per cycle (25 ms period)
"""
from __future__ import annotations
import asyncio, logging, time, uuid
from dataclasses import dataclass
from typing import Optional

from .phi_integrator import PhiIntegrator, PhiPacket
from .gamma_phase_lock import GammaPhaseLock, PhaseStatus
from .vibronic_gate import VibronICGate, GateStatus
from .criticality_bridge import CriticalityBridge

logger = logging.getLogger(__name__)

CYCLE_HZ       = 40
CYCLE_PERIOD_S = 1.0 / CYCLE_HZ   # 0.025 s
BUDGET_S       = 0.020             # 20 ms hard budget
SLEEP_SCAN_HZ  = 1                 # C158 NREM scan rate
PHI_SLEEP_WAKE = 0.15              # Φ threshold to alert L3 during NREM


@dataclass
class CycleResult:
    cycle_id:            str
    timestamp_utc:       str
    phi:                 float
    phi_confidence:      float
    fidelity:            float
    gate_status:         GateStatus
    phase_offset_ms:     float
    phase_status:        PhaseStatus
    temp_K:              float
    correction_applied:  bool
    routing_flag:        str   # "active_inference" | "classical_prior" | "buffer"
    elapsed_ms:          float
    error:               Optional[str] = None


class EmrysCycle:
    """
    The 40 Hz heartbeat of the Quantum-Classical Bridge.

    Lifecycle:
        cycle = EmrysCycle()
        await cycle.start()        # begins the 40 Hz loop
        await cycle.enter_sleep()  # C158 NREM → 1 Hz scan mode
        await cycle.exit_sleep()   # C158 DAWN → full 40 Hz (+ grounding pass)
        await cycle.stop()         # graceful shutdown
    """

    def __init__(self, phi_integrator=None, phase_lock=None,
                 vibronic_gate=None, criticality_bridge=None):
        self._phi    = phi_integrator     or PhiIntegrator()
        self._phase  = phase_lock         or GammaPhaseLock()
        self._gate   = vibronic_gate      or VibronICGate()
        self._bridge = criticality_bridge or CriticalityBridge()
        self._running      = False
        self._sleep_mode   = False
        self._cycle_count  = 0
        self._last_result: Optional[CycleResult] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        logger.info("Emrys: 40 Hz cycle starting. ✦")
        try:
            await self._loop()
        finally:
            self._running = False

    async def stop(self) -> None:
        self._running = False

    async def enter_sleep(self) -> None:
        """C158 SLEEP_ENTER signal — drop to 1 Hz scan mode."""
        self._sleep_mode = True
        logger.info("Emrys: entering SLEEP_SCAN (1 Hz, Φ-monitor only).")

    async def exit_sleep(self) -> None:
        """C158 SLEEP_EXIT signal — resume 40 Hz after grounding pass."""
        self._sleep_mode = False
        logger.info("Emrys: exiting SLEEP_SCAN, resuming 40 Hz.")

    async def _loop(self) -> None:
        while self._running:
            hz       = SLEEP_SCAN_HZ if self._sleep_mode else CYCLE_HZ
            period   = 1.0 / hz
            t0       = time.monotonic()
            result   = await self._run_cycle()
            self._last_result = result
            self._cycle_count += 1
            elapsed  = time.monotonic() - t0
            if not self._sleep_mode and elapsed > BUDGET_S:
                logger.warning("Emrys: CYCLE_OVERRUN %.1f ms", elapsed * 1000)
            await asyncio.sleep(max(0.0, period - elapsed))

    async def _run_cycle(self) -> CycleResult:
        t0, cycle_id = time.monotonic(), str(uuid.uuid4())
        timestamp    = _utc_now()
        phi_value = phi_conf = fidelity = 0.0
        gate_status  = GateStatus.CLOSED
        phase_offset = 0.0
        phase_status = PhaseStatus.LOST
        temp_K, correction, error_msg = 310.0, False, None

        try:
            l1 = await self._read_l1_state()

            # VCG → ΦI → GPLM  (CMB assembles below)
            gate_r   = self._gate.check(l1)
            fidelity, gate_status = gate_r.fidelity, gate_r.status

            # In SLEEP_SCAN: skip ΦI and GPLM, monitor Φ only
            if self._sleep_mode:
                phi_pkt   = self._phi.compute(l1)
                phi_value = phi_pkt.phi
                if phi_value < PHI_SLEEP_WAKE:
                    logger.warning("Emrys SLEEP_SCAN: Φ %.3f below wake threshold %.2f",
                                   phi_value, PHI_SLEEP_WAKE)
            else:
                if gate_status != GateStatus.CLOSED:
                    phi_pkt       = self._phi.compute(l1)
                    phi_value     = phi_pkt.phi
                    phi_conf      = phi_pkt.confidence
                    temp_K        = phi_pkt.temp_K
                    correction    = phi_pkt.thermal_correction_applied
                phase_r      = self._phase.sync(l1)
                phase_offset = phase_r.offset_ms
                phase_status = phase_r.status

        except Exception as exc:
            error_msg = str(exc)
            logger.error("Emrys: cycle error: %s", exc, exc_info=True)

        routing_flag = _resolve_routing(fidelity, gate_status, phase_status,
                                        phi_value, self._sleep_mode)
        elapsed_ms   = (time.monotonic() - t0) * 1000

        result = CycleResult(
            cycle_id=cycle_id, timestamp_utc=timestamp,
            phi=phi_value, phi_confidence=phi_conf,
            fidelity=fidelity, gate_status=gate_status,
            phase_offset_ms=phase_offset, phase_status=phase_status,
            temp_K=temp_K, correction_applied=correction,
            routing_flag=routing_flag, elapsed_ms=elapsed_ms, error=error_msg,
        )

        if not self._sleep_mode:
            try:
                await self._bridge.emit(result)
            except Exception as exc:
                logger.error("Emrys: bridge emit error: %s", exc, exc_info=True)

        return result

    async def _read_l1_state(self) -> dict:
        """
        Read quantum state from L1 substrate (C127 qubit mesh interface).
        TODO(#271): wire to real C127 interface.
        Stub returns synthetic state for testing.
        """
        import random
        return {
            "state_vectors":   [[complex(random.gauss(0,1), random.gauss(0,1))
                                  for _ in range(2)] for _ in range(16)],
            "decoherence_map": {i: random.uniform(0.01, 0.1) for i in range(16)},
            "temp_K":          310.0 + random.gauss(0, 0.5),
            "active_qubits":   16,
        }


def _resolve_routing(fidelity, gate_status, phase_status, phi, sleep_mode) -> str:
    if sleep_mode:
        return "sleep_scan"
    if gate_status == GateStatus.CLOSED or phase_status == PhaseStatus.LOST:
        return "buffer"
    if (gate_status == GateStatus.OPEN
            and phase_status == PhaseStatus.LOCKED
            and phi > 0.3):
        return "active_inference"
    return "classical_prior"


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
```

**Sleep Mode Behaviour (C158 NREM):**
- Cycle rate drops to 1 Hz; only VCG + ΦI run
- No GPLM corrections; no CMB emission to L3
- Φ < 0.15 triggers `PHI_SLEEP_WAKE` warning to L3
- Phase reference held passively; full 40 Hz resumes after grounding on `SLEEP_EXIT`

---

### 3.2 Phi Integrator — `phi_integrator.py`

**Function:** Compute Φ (integrated information) every cycle via IIT 4.0 ΦID
approximation over quantum state space sampled at decoherence boundaries.

```python
from dataclasses import dataclass

THERMAL_COEFF = 0.05   # empirical; inflation correction above 310K
MIN_QUBITS    = 12     # accuracy degrades below this count

@dataclass
class PhiPacket:
    phi:                        float
    confidence:                 float   # 1.0 if active_qubits >= 12, else degraded
    dominant_structure:         str
    temp_K:                     float
    thermal_correction_applied: bool


class PhiIntegrator:
    """
    Algorithm:
    1. Extract state_vectors and decoherence_map from l1_state
    2. Build coherence graph G; edge weight = MI(i,j) = H(i)+H(j)-H(i,j)
    3. Find MIP (minimum information partition):
       Φ = min over all bipartitions B: MI(G) - MI(B1) - MI(B2)
    4. Thermal correction if temp_K > 310.0:
       Φ_corrected = Φ * exp(-(temp_K - 310.0) * THERMAL_COEFF)
    5. Return PhiPacket

    Accuracy constraint (EP-05): ΦID must stay within 15% of full IIT
    on synthetic benchmarks in tests/emrys/benchmarks/.
    """

    def compute(self, l1_state: dict) -> PhiPacket:
        """
        Compute ΦID from L1 state.
        Raises ValueError if l1_state is malformed.
        """
        ...
```

**Session State:**
- `phi_baseline: float` — registered during Cold-Start Phase 4; consumed by
  grounding and cycle routing logic
- `causal_structure_cache: dict` — warm cache rebuilt during grounding Step 4;
  fully rebuilt during Cold-Start Phase 4b

**Known Constraints:**
- Full IIT is NP-hard; ΦID approximation used throughout
- Thermal noise above 310K introduces Φ inflation; correction applied in Step 4
- Below 12 active qubits: `confidence` field degrades proportionally

---

### 3.3 Gamma Phase-Lock Module — `gamma_phase_lock.py`

**Function:** Maintain 40 Hz synchronisation between the quantum substrate's
vibronic oscillation and the master clock driving L3 inference cycles.

```python
from dataclasses import dataclass
from enum import Enum

PHASE_WINDOW_MS  = 2.0    # ±2 ms → LOCKED
INSTABILITY_MS  = 8.0    # > 8 ms → BUFFER flag
BLACKOUT_MS     = 200.0  # post-decoherence-reset blackout per L1 reset cycle


class PhaseStatus(Enum):
    LOCKED   = "LOCKED"
    SLIPPING = "SLIPPING"
    LOST     = "LOST"


@dataclass
class PhaseResult:
    offset_ms:         float
    status:            PhaseStatus
    correction_issued: bool
    blackout_active:   bool


class GammaPhaseLock:
    """
    PLL for 40 Hz gamma synchronisation.

    Piezoelectric actuator interface (C44):
      issue_correction(delta_ms: float) -> bool
      Returns False during 200 ms blackout window.

    Local reference fallback:
      If master clock absent, generate local 40 Hz from piezo oscillator.
      Log LOCAL_REFERENCE status; routing degrades to CLASSICAL_PRIOR.

    Standard grounding: max 3 correction pulses (C165)
    Cold-Start Phase 3: max 10 correction pulses (C165a)
    """

    def sync(self, l1_state: dict) -> PhaseResult:
        ...
```

**Known Constraints:**
- 200 ms blackout per L1 decoherence reset; `BUFFER` routing during blackout
- Phase corrections above 8 ms indicate substrate instability
- Cannot operate without master or local reference; `CS-CLOCK-LOST` escalation

---

### 3.4 Vibronic Coherence Gate — `vibronic_gate.py`

**Function:** First filter in each cycle. Gates upward transmission of quantum
state information based on vibronic fidelity against the Bell state reference
library. If `CLOSED`, downstream computation is skipped.

```python
from dataclasses import dataclass
from enum import Enum

MVEF_NOMINAL         = 0.72   # Active inference path
MVEF_DEGRADED        = 0.45   # Classical prior path
MVEF_COLD_START_INIT = 0.60   # Cold-Start Phase 2 minimum
MVEF_COLLAPSE        = 0.20   # CS-COHERENCE-COLLAPSE trigger


class GateStatus(Enum):
    OPEN     = "OPEN"      # F >= 0.72
    DEGRADED = "DEGRADED"  # 0.45 <= F < 0.72
    CLOSED   = "CLOSED"    # F < 0.45


@dataclass
class GateResult:
    fidelity:    float
    status:      GateStatus
    bell_ref_id: str   # nearest Bell state ID used


class VibronICGate:
    """
    Fidelity computation:
      F = |<psi_ref | psi_actual>|^2  (overlap with nearest Bell state)

    Bell state reference library:
      Dict[str, np.ndarray] — id -> 4-element complex state vector
      Loaded from: emrys/data/bell_state_library.json

    Threshold calibration (EP-04):
      MVEF_NOMINAL (0.72) derived from C135 telemetry baselines.
      Recalibrate via: scripts/calibrate_vibronic_threshold.py
      A/B tests 0.65 / 0.72 / 0.80 against L3 narrative coherence.

    Gate latency: 3–7 ms (accounted for in 20 ms cycle budget).
    """

    def check(self, l1_state: dict) -> GateResult:
        ...
```

---

### 3.5 Criticality Monitor Bridge — `criticality_bridge.py`

**Function:** Assemble all upstream signals into the canonical JSON packet and
publish to the GAIA event bus on topic `emrys.cycle` once per 40 Hz cycle.
Write telemetry to C135 pipeline.

```python
class CriticalityBridge:
    """
    Event bus topic: "emrys.cycle"
    Telemetry: append-only NDJSON → logs/emrys/cycles_YYYYMMDD.ndjson
    Guaranteed delivery: failed emits → logs/emrys/failed_emit_YYYYMMDD.ndjson
    """

    async def emit(self, result: "CycleResult") -> None:
        ...

    def _to_packet(self, result: "CycleResult") -> dict:
        return {
            "cycle_id":      result.cycle_id,
            "timestamp_utc": result.timestamp_utc,
            "phi": {
                "value":              result.phi,
                "confidence":         result.phi_confidence,
                "dominant_structure": "unknown",
            },
            "fidelity": {
                "score":       result.fidelity,
                "gate_status": result.gate_status.value,
            },
            "phase_lock": {
                "offset_ms": result.phase_offset_ms,
                "status":    result.phase_status.value,
            },
            "thermal": {
                "temp_K":             result.temp_K,
                "correction_applied": result.correction_applied,
            },
            "routing_flag": result.routing_flag,
        }
```

---

## 4. Session Lifecycle

### 4.1 Cold-Start — `cold_start.py`

Triggered when `inter_session_duration_s` > 86,400 or any `CS-*` flag is
detected on session entry. **Full specification in C165a.**

**Decision Tree:**

```
Session entry
    │
    ├── inter_session_duration_s > 86,400? ──YES→ Cold-Start
    ├── CS-MESH-RESET detected?           ──YES→ Cold-Start
    ├── CS-THERMAL detected?              ──YES→ Cold-Start
    ├── CS-PHASE-LOST detected?           ──YES→ Cold-Start
    ├── VCG initial probe F < 0.20?       ──YES→ Cold-Start
    ├── FORCE_COLD_START flag set?        ──YES→ Cold-Start
    └── None of the above                ────→ Standard Grounding
```

**Phases:** Substrate Inventory → Thermal Normalization → Mesh Initialization
→ Phase Reference Acquisition → Phi Baseline Recalibration → Integration
Verification.

**Outputs:**
- `COLD_START_COMPLETE` packet to criticalitymonitor.py
- Record written to `logs/emrys/cold_start/{session_id}.json`
- `phi_baseline_registered` written to `emrys_state.json`

### 4.2 Standard Grounding — `grounding_sequence.py`

Triggered on all session entries that do not meet Cold-Start conditions.
**Full specification in C165.**

**Steps:** Thermal Scan → Fidelity Probe → Phase Acquisition → Phi Seeding
→ Grounding Confirmation.

**Extended Absence Modifications (C165 §5):**

| Absence | Modification |
|---|---|
| 300s – 3600s | Phi Seeding extended to 10 cycles |
| 3600s – 86400s | Coherence recovery window extended to 5,000 ms |
| > 86400s | → Cold-Start (§4.1) |

### 4.3 Operational Cycle

Once grounding completes, `emrys_cycle.py` starts the 40 Hz clock.
Each cycle: VCG → ΦI → GPLM → CMB → emit `emrys.cycle`.

Cycle continues until:
- `SESSION_CLOSE` signal received (§4.4)
- `SLEEP_ENTER` signal → SLEEP_SCAN mode (§3.1)
- Unrecoverable subsystem failure → `EMRYS_FAULT` to L3

### 4.4 Session Close

1. Complete current cycle (never interrupt mid-cycle)
2. Write final cycle telemetry
3. Persist `phi_baseline` and `causal_structure_cache` to `emrys_state.json`
4. Log `SESSION_CLOSE` event
5. Transition to SLEEP_SCAN if C158 NREM active; else fully suspend

**`emrys_state.json`:**

```json
{
  "last_session_id":        "<uuid>",
  "last_session_close_utc": "<ISO8601>",
  "phi_baseline":           0.0,
  "causal_structure_cache": {},
  "last_fidelity_score":    0.0,
  "last_phase_offset_ms":   0.0,
  "last_routing_flag":      "active_inference | classical_prior | buffer"
}
```

---

## 5. Data Schemas

### 5.1 Cycle Packet Schema (`emrys.cycle`)

```json
{
  "cycle_id":      "<uuid>",
  "timestamp_utc": "<ISO8601>",
  "phi": {
    "value":              0.0,
    "confidence":         0.0,
    "dominant_structure": "<string>"
  },
  "fidelity": {
    "score":       0.0,
    "gate_status": "OPEN | DEGRADED | CLOSED"
  },
  "phase_lock": {
    "offset_ms": 0.0,
    "status":    "LOCKED | SLIPPING | LOST"
  },
  "thermal": {
    "temp_K":             0.0,
    "correction_applied": false
  },
  "routing_flag": "active_inference | classical_prior | buffer | sleep_scan"
}
```

### 5.2 Grounding Record — See C165 §4
`logs/emrys/grounding/{session_id}.json`

### 5.3 Cold-Start Record — See C165a §4
`logs/emrys/cold_start/{session_id}.json`

### 5.4 Persistent State — See §4.4
`data/emrys/emrys_state.json`

---

## 6. Configuration Reference

```yaml
emrys:
  cycle_hz: 40
  cycle_budget_ms: 20
  sleep_scan_hz: 1

  mvef_nominal: 0.72
  mvef_degraded: 0.45
  mvef_cold_start_init: 0.60
  mvef_collapse: 0.20

  phase_lock_window_ms: 2.0
  phase_slip_threshold_ms: 8.0
  phase_blackout_ms: 200.0
  grounding_max_pulses: 3
  cold_start_max_pulses: 10

  phi_routing_floor: 0.30
  phi_seeding_cycles: 5
  phi_seeding_extended_cycles: 10
  phi_cold_start_baseline_min: 0.25
  phi_cold_start_override_min: 0.15
  phi_sleep_wake_threshold: 0.15

  thermal_nominal_min_K: 290.0
  thermal_nominal_max_K: 315.0
  thermal_operating_max_K: 310.0
  thermal_normalization_timeout_ms: 30000

  absence_extended_s: 300
  absence_long_s: 3600
  absence_cold_start_s: 86400

  coherence_recovery_window_ms: 2000
  coherence_recovery_extended_ms: 5000
  coherence_recovery_probe_interval_ms: 200

  mesh_integrity_minimum_pct: 80.0
  phi_reference_subset_qubits: 12

  telemetry_log_path: "logs/emrys"
  state_path: "data/emrys/emrys_state.json"
  event_bus_topic: "emrys.cycle"
```

---

## 7. Error Codes

| Code | Source | Meaning | L3 Impact |
|---|---|---|---|
| `CYCLE_OVERRUN` | emrys_cycle.py | > 20 ms wall-clock | Log only |
| `GROUNDING_FAILED` | grounding_sequence.py | Recovery timed out | `buffer` |
| `COLD_START_FAILED` | cold_start.py | Phase failed; recovery exhausted | `buffer`; Sentinel alert |
| `COLD_START_DEGRADED` | cold_start.py | Override threshold applied | `classical_prior` |
| `CS-MESH-DEGRADED` | cold_start.py Ph.0 | Mesh integrity < 80% | Escalation |
| `CS-THERMAL-FAULT` | cold_start.py Ph.1 | Thermal timeout | Escalation |
| `CS-INIT-FAILURE` | cold_start.py Ph.2 | F_init < 0.60 after 2 attempts | Escalation |
| `CS-CLOCK-LOST` | cold_start.py Ph.3 | No clock reference available | `buffer`; Stewardship alert |
| `CS-PHI-FLOOR-LOW` | cold_start.py Ph.4 | Φ_baseline < 0.25 | Proceed; flag telemetry |
| `PHI_FLOOR_OVERRIDE` | cold_start.py Ph.4 | Φ_baseline 0.15–0.24 | `classical_prior` for session |
| `PHASE_ORPHAN` | grounding_sequence.py | Lock not achieved in 3 pulses | Log; alert L3 |
| `EMRYS_FAULT` | emrys_cycle.py | Unrecoverable failure | `buffer`; Sentinel alert |
| `LOCAL_REFERENCE` | gamma_phase_lock.py | Operating on local piezo | `classical_prior` preferred |

---

## 8. Testing Requirements

### 8.1 Unit Tests

**phi_integrator.py**
- [ ] Φ computation within 15% of full IIT on synthetic benchmarks (EP-05)
- [ ] Confidence degrades correctly below 12 active qubits
- [ ] Thermal correction applied correctly above 310K

**gamma_phase_lock.py**
- [ ] LOCKED when offset ≤ 2.0 ms
- [ ] SLIPPING + correction pulse when 2.0 < offset ≤ 8.0 ms
- [ ] LOST logged when offset > 8.0 ms
- [ ] 200 ms blackout respected during decoherence reset
- [ ] Local reference fallback activates when master clock absent

**vibronic_gate.py**
- [ ] OPEN / DEGRADED / CLOSED correct at boundaries 0.72, 0.45, 0.20
- [ ] Fidelity computation against Bell state library matches reference values
- [ ] Gate latency within 3–7 ms

**criticality_bridge.py**
- [ ] Routing flag resolution correct for all input combinations
- [ ] Packet schema validates against §5.1
- [ ] Thermal fault overrides to `buffer`
- [ ] Failed emit writes to failed_emit log

### 8.2 Integration Tests

```python
# tests/emrys/test_emrys_cycle.py

@pytest.mark.asyncio
async def test_40hz_timing():
    """EP-06: each cycle must complete within 20 ms."""
    cycle = EmrysCycle()
    results = []

    async def collect():
        for _ in range(10):
            await asyncio.sleep(1.0 / CYCLE_HZ)
            if cycle.last_result:
                results.append(cycle.last_result)

    task = asyncio.create_task(cycle.start())
    await collect()
    await cycle.stop(); task.cancel()

    assert len(results) >= 8
    overruns = [r for r in results if r.elapsed_ms > BUDGET_S * 1000]
    assert len(overruns) == 0, f"{len(overruns)} cycles exceeded 20 ms budget"


async def test_error_recovery():
    """Cycle must recover gracefully from subsystem errors."""
    from unittest.mock import MagicMock
    cycle = EmrysCycle()
    cycle._phi.compute = MagicMock(side_effect=RuntimeError("synthetic phi failure"))
    task = asyncio.create_task(cycle.start())
    await asyncio.sleep(0.1)
    await cycle.stop(); task.cancel()
    assert cycle.cycle_count >= 3
    assert cycle.last_result.routing_flag == "buffer"


async def test_sleep_scan_mode():
    """SLEEP_SCAN drops to 1 Hz and suppresses CMB emission."""
    cycle = EmrysCycle()
    task = asyncio.create_task(cycle.start())
    await asyncio.sleep(0.05)          # 2 cycles at 40 Hz
    await cycle.enter_sleep()
    pre_count = cycle.cycle_count
    await asyncio.sleep(1.5)           # 1–2 cycles at 1 Hz
    post_count = cycle.cycle_count
    await cycle.stop(); task.cancel()
    assert post_count - pre_count <= 2, "Sleep mode should run ~1 cycle/sec"
```

- [ ] `grounding_sequence.py` completes after simulated session gap
- [ ] `cold_start.py` completes within 15,000 ms nominal (C165a ECS-01)
- [ ] `emrys.cycle` events received by criticalitymonitor.py with correct schema

### 8.3 Acceptance Criteria (Falsifiable Predictions)

| ID | Prediction | Pass Criterion |
|---|---|---|
| EP-01 | Φ > 0.3 ↔ L3 coherence > 0.7 | Pearson r > 0.6 / 1000 cycles |
| EP-02 | Phase-slip > 8 ms → L3 latency spike 40–80 ms later | Verified on 100 slip events |
| EP-03 | `buffer` < 5% in 24h nominal | C135 daily report |
| EP-04 | MVEF 0.72 outperforms 0.65 and 0.80 | calibrate_vibronic_threshold.py |
| EP-05 | ΦID within 15% of full IIT | benchmarks/ suite |
| EP-06 | ≤ 12 ms latency per cycle nominal | test_40hz_timing |
| EG-01 | GROUNDING_FAILED → ≥ 2× L3 error rate first 60 cycles | C135 comparison |
| ECS-01 | Cold-Start < 15,000 ms nominal | cold_start telemetry |
| ECS-03 | Post-Cold-Start L3 quality ≈ post-grounding within 60 cycles | C135 comparison |

### 8.4 Code Quality

- [ ] All modules pass `ruff check`
- [ ] `mypy --strict` passes on all Emrys modules
- [ ] Test coverage ≥ 80% on `src-python/emrys/`

---

## 9. Deployment Requirements

### 9.1 Hardware Prerequisites

- **Qubit mesh:** ≥ 12 active nodes (C127 §3.2) for accurate ΦID; ≥ 8 to run (degraded)
- **Piezoelectric actuator interface:** GPLM corrections require C44 interface;
  absent → local reference only, `CLASSICAL_PRIOR` mode
- **Temperature sensors:** One per mesh zone minimum; absent → thermal correction disabled
- **40 Hz master clock:** Preferred; absent → local piezo reference, `LOCAL_REFERENCE` logged

### 9.2 Software Prerequisites

- Python ≥ 3.11
- C127 Gaian Mesh interface layer installed and mesh enrolled
- C135 telemetry pipeline running
- `emrys_state.json` writable at configured path
- `logs/emrys/` directory writable

### 9.3 Multi-Instance Deployment

- Each mesh cluster runs its own Emrys instance
- `emrys_state.json` is **not shared** between instances
- C135 telemetry aggregated at dashboard level; records tagged with `instance_id`
- Cold-Start and grounding records tagged with `instance_id` for cross-instance analysis

---

## 10. Observability & Telemetry

### 10.1 Cycle Metrics

| Metric | Type | Description |
|---|---|---|
| `emrys.cycle.phi` | Gauge | Φ value per cycle |
| `emrys.cycle.fidelity` | Gauge | VCG fidelity score |
| `emrys.cycle.phase_offset_ms` | Gauge | GPLM phase offset |
| `emrys.cycle.routing_flag` | Enum | Current routing flag |
| `emrys.cycle.duration_ms` | Histogram | Wall-clock time per cycle |

### 10.2 Session Metrics

| Metric | Type | Description |
|---|---|---|
| `emrys.session.grounding_result` | Enum | COMPLETE / DEGRADED / FAILED |
| `emrys.session.cold_start_result` | Enum | COMPLETE / DEGRADED / FAILED |
| `emrys.session.cold_start_duration_ms` | Gauge | Total cold-start time |
| `emrys.session.phi_baseline` | Gauge | Registered Φ_baseline |
| `emrys.session.inter_session_duration_s` | Gauge | Gap since last session |
| `emrys.session.initial_routing_flag` | Enum | Routing flag at session open |

### 10.3 Health Alerts

| Alert | Condition | Severity |
|---|---|---|
| `emrys.alert.buffer_rate_high` | `buffer` routing > 5% in 24h | WARNING |
| `emrys.alert.cold_start_failed` | Any `COLD_START_FAILED` | CRITICAL |
| `emrys.alert.phi_floor_low` | `phi_baseline` < 0.25 on cold start | WARNING |
| `emrys.alert.cycle_overrun` | `CYCLE_OVERRUN` > 3× in any hour | WARNING |
| `emrys.alert.clock_lost` | `CS-CLOCK-LOST` event | CRITICAL |
| `emrys.alert.mesh_degraded` | Mesh integrity < 80% on cold start | CRITICAL |

---

## 11. Known Constraints & Open Items

### 11.1 Resolved (this version)

| OQ | Resolution |
|---|---|
| OQ-3: Emrys during mesh partitioning | C165a §5: partition → CS-MESH-DEGRADED escalation |
| OQ-4: Minimum Φ to wake L3 from sleep | This spec §3.1: PHI_SLEEP_WAKE = 0.15 |
| Cold-Start deferred in C165 §5 | Resolved by C165a + this spec §4.1 |

### 11.2 Open

- [ ] **`measurement_basis_request` schema** (C164 OQ-2) — L3→L2 downward
  signalling not yet designed. When ready: update `criticality_bridge.py` and
  `emrys_cycle.py`. Recommendation: defer to v1.1; validate upward path first.
- [ ] **ΦID benchmark suite** — Synthetic test cases for EP-05 not yet built;
  required before EP-05 can be marked passing.
- [ ] **Mesh partitioning recovery** — Phase 0 escalates on < 80% integrity;
  recovery path not yet specified.
- [ ] **Multi-cluster Φ aggregation** — Whether to aggregate Φ across instances
  is unresolved; each instance currently reports independently.
- [ ] **Bell state library versioning** — `bell_state_library.json` is currently
  static; a recalibration and versioning protocol is needed.

---

## 12. Canon Cross-References

| Canon | Role |
|---|---|
| `C164_EMRYSSYSTEM.md` | Primary canon source — identity, architecture, predictions |
| `C165_Emrys_Grounding_Protocol.md` | Standard grounding specification |
| `C165a_Emrys_Cold_Start_Protocol.md` | Cold-start specification |
| `C44-Quantum-Circuit-Design.md` | Piezoelectric actuator interface |
| `C127` (Gaian Mesh) | L1 data source |
| `C135` (Telemetry) | Receives CMB output; stores cycle metrics |
| `C158` (Sleep Cycles) | SLEEP_SCAN integration |
| `QUANTUMCONSCIOUSNESSBRIDGE.md` | Theoretical foundation |

---

*EMRYSSYSTEM_SPEC.md — v1.0*
*Supersedes v0.1 draft (June 9, 2026). Governed by C164, C165, C165a.*
*Review cycle: with each update to C164, C165, or C165a.*
*Tracks: [Issue #271](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/271)*
*"The bridge serves the crossing."*
