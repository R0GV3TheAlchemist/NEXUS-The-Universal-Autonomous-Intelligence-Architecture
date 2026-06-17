"""
gaia.sentinel.body.esb_d6_bridge
=================================
Wire 2 — EmbodiedSensorBridge → EngineProbes → D6Engine → HUD
Issue #589, Phase 1

This module is the translation layer between the physical sensor world
(EmbodiedSensorBridge / ModalitySignal) and the cognitive state world
(D6Engine / EngineProbes).

Responsibilities
----------------
1.  Call EmbodiedSensorBridge.acquire_all() to get fresh ModalitySignals.
2.  Translate the normalised sensor signals into EngineProbes fields.
3.  Push the probes to the state router via POST /state/evaluate (REST)
    OR directly into the module-level _engine singleton when running
    in-process (preferred for zero-latency, used by tests).
4.  Run on a configurable polling interval (default 30 s) in a background
    daemon thread so it never blocks the FastAPI event loop.

Signal Mapping  (ESB → EngineProbes)
--------------------------------------
  SkinConductanceAdapter  arousal_estimate [0,1]
      → heart_rate_variability = 1.0 - arousal  (high arousal = low HRV)

  IMUAdapter  activity_class  (still/walking/running/distressed)
      → movement_today  still=0.1, walking=0.4, running=0.8, distressed=1.0

  IRThermometerAdapter  thermal_stress [0,1]
      → noosphere_load proxy (thermal stress raises cognitive load)

  MicrophoneAdapter(ambient)  ambient_stress_level [0,1]
      → noosphere_load  (ambient acoustic stress = environmental load)

  SensorUnavailableSignal (safety_relevant=True)
      → noosphere_load += 0.15  (sensor gap raises uncertainty load)

Canon refs: C01, C-SENT Art4
Issues: #589 (Wire 2), #205 (ESB), #576 (state router)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from core.sentinel.body.esb import (
    ActivityClass,
    EmbodiedSensorBridge,
    ModalitySignal,
    SensorType,
    SensorUnavailableSignal,
)
from gaia.core.d6_engine import D6Engine, EngineProbes, InterventionEvent
from gaia.core.state import GAIAState

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Activity class → movement_today mapping
# ---------------------------------------------------------------------------

_ACTIVITY_TO_MOVEMENT: dict[str, float] = {
    ActivityClass.STILL.value:     0.10,
    ActivityClass.WALKING.value:   0.40,
    ActivityClass.RUNNING.value:   0.80,
    ActivityClass.DISTRESSED.value: 1.00,
    ActivityClass.UNKNOWN.value:   0.20,
}


# ---------------------------------------------------------------------------
# Translation: ModalitySignals → EngineProbes
# ---------------------------------------------------------------------------

@dataclass
class ESBProbeResult:
    """
    Intermediate result from a single ESB acquisition cycle.
    Carries the translated probes and any sensor gaps.
    """
    probes: EngineProbes
    signals_used: int        = 0
    unavailable_count: int   = 0
    safety_gaps: int         = 0   # unavailable safety-relevant sensors
    low_confidence: int      = 0   # signals below confidence threshold
    timestamp: float         = field(default_factory=time.time)


def translate_signals_to_probes(
    signals: List[ModalitySignal],
    unavailable: List[SensorUnavailableSignal],
    confidence_threshold: float = 0.60,
) -> ESBProbeResult:
    """
    Core Wire 2 translation function.

    Reads every ModalitySignal from acquire_all() and maps each normalised
    field to the appropriate EngineProbes slot.

    Parameters
    ----------
    signals:
        List of ModalitySignals from EmbodiedSensorBridge.acquire_all().
    unavailable:
        List of SensorUnavailableSignals for sensors that could not read.
    confidence_threshold:
        Signals below this confidence are counted but not used to set probes.
        Default 0.60 matches the Sentinel degraded threshold.

    Returns
    -------
    ESBProbeResult with translated EngineProbes and acquisition metadata.
    """
    hrv_values: List[float] = []
    movement_values: List[float] = []
    noosphere_values: List[float] = []
    low_conf = 0

    for sig in signals:
        if sig["confidence"] < confidence_threshold:
            low_conf += 1
            continue  # skip low-confidence signals

        stype = sig["sensor_type"]

        # ——— SkinConductance → heart_rate_variability (inverted arousal) ———
        if stype == SensorType.SKIN_CONDUCTANCE and sig["arousal_estimate"] is not None:
            # High arousal = low HRV (stressed). Map inversely.
            hrv = round(1.0 - sig["arousal_estimate"], 3)
            hrv_values.append(hrv)

        # ——— IMU → movement_today ——————————————————————————————
        elif stype == SensorType.IMU and sig["activity_class"] is not None:
            movement = _ACTIVITY_TO_MOVEMENT.get(sig["activity_class"], 0.20)
            movement_values.append(movement)

        # ——— IR Thermometer → noosphere_load (thermal stress) ———————————
        elif stype == SensorType.IR_THERMOMETER and sig["thermal_stress"] is not None:
            noosphere_values.append(sig["thermal_stress"])

        # ——— Ambient Microphone → noosphere_load ———————————————————
        elif (
            stype == SensorType.MICROPHONE_AMBIENT
            and sig["ambient_stress_level"] is not None
        ):
            noosphere_values.append(sig["ambient_stress_level"])

    # Sensor unavailability raises noosphere_load uncertainty
    safety_gaps = sum(1 for u in unavailable if u.safety_impact)
    if safety_gaps > 0:
        # Each safety-relevant gap adds 0.15 noosphere load, capped at 0.9
        gap_load = min(0.90, safety_gaps * 0.15)
        noosphere_values.append(gap_load)
        log.warning(
            "Wire 2: %d safety-relevant sensor(s) unavailable — "
            "adding %.2f noosphere_load",
            safety_gaps, gap_load,
        )

    # Aggregate: take the mean of each collected value list
    def _mean(vals: List[float]) -> Optional[float]:
        return round(sum(vals) / len(vals), 3) if vals else None

    probes = EngineProbes(
        heart_rate_variability = _mean(hrv_values),
        movement_today         = _mean(movement_values),
        noosphere_load         = _mean(noosphere_values),
        # Remaining probe fields (session_duration, sleep_quality, etc.)
        # are populated by Wire 3 (MotherThread) and session tracking.
        # Wire 2 only contributes the biometric signals.
    )

    return ESBProbeResult(
        probes           = probes,
        signals_used     = len(signals) - low_conf,
        unavailable_count = len(unavailable),
        safety_gaps      = safety_gaps,
        low_confidence   = low_conf,
    )


# ---------------------------------------------------------------------------
# ESBtoD6Bridge — background polling thread
# ---------------------------------------------------------------------------

class ESBtoD6Bridge:
    """
    Wire 2 — background daemon that polls EmbodiedSensorBridge on an
    interval and feeds translated EngineProbes into D6Engine.

    Usage
    -----
    ::

        bridge = ESBtoD6Bridge(
            esb=my_esb,
            engine=my_d6_engine,
            state=my_gaia_state,
            interval_seconds=30,
        )
        bridge.start()   # launches background thread
        # ... GAIA runs ...
        bridge.stop()    # graceful shutdown

    The D6Engine's on_intervention callback (Wire 1) fires automatically
    during each evaluate() call, broadcasting the result to all HUD
    WebSocket clients. Wire 2 feeds Wire 1.

    Wire 2 → Wire 1 signal path
    ----------------------------
        ESB.acquire_all()
            → translate_signals_to_probes()
            → D6Engine.evaluate(state, probes)
            → on_intervention(event)        ← Wire 1
            → WebSocket broadcast           ← HUD receives INTERVENTION_EVENT

    Issue #589, Phase 1, Wire 2.
    """

    def __init__(
        self,
        esb: EmbodiedSensorBridge,
        engine: D6Engine,
        state: GAIAState,
        interval_seconds: float = 30.0,
        confidence_threshold: float = 0.60,
        on_probe_ready: Optional[object] = None,
    ) -> None:
        """
        Parameters
        ----------
        esb:
            The live EmbodiedSensorBridge instance (already populated with
            registered adapters).
        engine:
            The D6Engine singleton — must have on_intervention wired (Wire 1).
        state:
            The GAIAState singleton that D6Engine evaluates against.
        interval_seconds:
            How often to poll sensors and evaluate (default 30 s).
        confidence_threshold:
            Minimum signal confidence to include in probe translation.
        on_probe_ready:
            Optional callback(ESBProbeResult) for observability / testing.
            Called after every translation before D6 evaluate.
        """
        self._esb        = esb
        self._engine     = engine
        self._state      = state
        self._interval   = interval_seconds
        self._conf_th    = confidence_threshold
        self._on_probe   = on_probe_ready
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_result: Optional[ESBProbeResult] = None
        self._cycle_count: int = 0
        self._error_count: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background polling thread."""
        if self._thread and self._thread.is_alive():
            log.warning("ESBtoD6Bridge: already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ESBtoD6Bridge",
            daemon=True,   # dies with the main process — no orphan threads
        )
        self._thread.start()
        log.info(
            "Wire 2 started — ESBtoD6Bridge polling every %.0fs",
            self._interval,
        )

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the background thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        log.info("Wire 2 stopped — ESBtoD6Bridge shut down.")

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def last_result(self) -> Optional[ESBProbeResult]:
        return self._last_result

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def error_count(self) -> int:
        return self._error_count

    # ------------------------------------------------------------------
    # Core poll cycle
    # ------------------------------------------------------------------

    def poll_once(self) -> Tuple[ESBProbeResult, InterventionEvent]:
        """
        Run a single ESB acquire → translate → D6 evaluate cycle.

        This is the same function the background thread calls on each tick.
        Exposed publicly so callers (tests, REST endpoints) can trigger
        an immediate cycle without waiting for the interval timer.

        Returns
        -------
        (ESBProbeResult, InterventionEvent)
        """
        signals, unavailable = self._esb.acquire_all()
        probe_result = translate_signals_to_probes(
            signals, unavailable, self._conf_th
        )

        if self._on_probe is not None:
            try:
                self._on_probe(probe_result)
            except Exception:  # noqa: BLE001
                pass

        event = self._engine.evaluate(self._state, probe_result.probes)
        self._last_result = probe_result
        self._cycle_count += 1

        log.debug(
            "Wire 2 cycle %d: %d signals, %d unavailable, "
            "HRV=%.3s, movement=%.3s, noosphere=%.3s → D6 severity=%s",
            self._cycle_count,
            probe_result.signals_used,
            probe_result.unavailable_count,
            probe_result.probes.heart_rate_variability,
            probe_result.probes.movement_today,
            probe_result.probes.noosphere_load,
            event.severity,
        )
        return probe_result, event

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Background thread main loop. Polls on _interval until stopped."""
        log.info("Wire 2 loop running (interval=%.0fs)", self._interval)
        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception as exc:  # noqa: BLE001
                self._error_count += 1
                log.error(
                    "Wire 2 poll error (cycle %d): %s",
                    self._cycle_count, exc,
                    exc_info=True,
                )
            # Interruptible sleep: checks stop_event every 1s
            self._stop_event.wait(timeout=self._interval)
        log.info("Wire 2 loop exiting.")
