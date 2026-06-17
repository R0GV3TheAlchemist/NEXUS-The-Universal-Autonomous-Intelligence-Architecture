"""
tests/test_esb_d6_bridge.py
============================
Wire 2 Test Suite — EmbodiedSensorBridge → EngineProbes → D6Engine → HUD
Issue #589, Phase 1

Tests:
  T01 — translate_signals_to_probes: calm baseline maps correctly
  T02 — translate_signals_to_probes: high arousal inverts to low HRV
  T03 — translate_signals_to_probes: safety-relevant sensor gap adds noosphere_load
  T04 — translate_signals_to_probes: low-confidence signals are excluded
  T05 — ESBtoD6Bridge.poll_once() returns (ESBProbeResult, InterventionEvent)
  T06 — ESBtoD6Bridge background thread starts, cycles, stops cleanly
  T07 — Wire 2 → Wire 1: poll_once() fires D6 on_intervention callback
"""

from __future__ import annotations

import time
import threading
from unittest.mock import MagicMock, patch
from typing import List

import pytest

from core.sentinel.body.esb import (
    ActivityClass,
    EmbodiedSensorBridge,
    IMUAdapter,
    IRThermometerAdapter,
    ModalitySignal,
    MicrophoneAdapter,
    SkinConductanceAdapter,
    SensorConfig,
    SensorType,
    SensorUnavailableSignal,
)
from gaia.core.d6_engine import D6Engine, EngineProbes
from gaia.core.state import default_state
from gaia.sentinel.body.esb_d6_bridge import (
    ESBProbeResult,
    ESBtoD6Bridge,
    translate_signals_to_probes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_modality_signal(
    sensor_type: str,
    confidence: float = 0.90,
    arousal_estimate=None,
    activity_class=None,
    thermal_stress=None,
    ambient_stress_level=None,
) -> ModalitySignal:
    """Construct a minimal ModalitySignal for testing."""
    return ModalitySignal(
        signal_id="test-signal",
        sensor_type=sensor_type,
        timestamp="2026-06-17T20:00:00Z",
        confidence=confidence,
        prosody_features=None,
        transcript_hint=None,
        ambient_stress_level=ambient_stress_level,
        emotion_estimate=None,
        gesture_label=None,
        personal_space_m=None,
        activity_class=activity_class,
        arousal_estimate=arousal_estimate,
        thermal_stress=thermal_stress,
        raw_ref="test-sensor",
    )


def _make_unavailable(safety_impact: bool = True) -> SensorUnavailableSignal:
    return SensorUnavailableSignal(
        sensor_type=SensorType.SKIN_CONDUCTANCE,
        sensor_id="gsr-01",
        timestamp="2026-06-17T20:00:00Z",
        reason="offline",
        safety_impact=safety_impact,
    )


# ---------------------------------------------------------------------------
# T01 — Calm baseline maps correctly
# ---------------------------------------------------------------------------

def test_T01_calm_baseline_probe_translation():
    """
    T01: A calm sensor set (low arousal, still, no thermal stress) must
    translate to probes with HRV close to 1.0, low movement, no noosphere load.
    """
    signals = [
        _make_modality_signal(
            SensorType.SKIN_CONDUCTANCE,
            arousal_estimate=0.10,   # calm: low arousal → high HRV
        ),
        _make_modality_signal(
            SensorType.IMU,
            activity_class=ActivityClass.STILL.value,
        ),
        _make_modality_signal(
            SensorType.IR_THERMOMETER,
            thermal_stress=0.0,
        ),
    ]
    result = translate_signals_to_probes(signals, [])

    assert result.signals_used == 3
    assert result.unavailable_count == 0
    assert result.safety_gaps == 0

    assert result.probes.heart_rate_variability is not None
    assert result.probes.heart_rate_variability >= 0.85, (
        f"Low arousal should yield high HRV, got {result.probes.heart_rate_variability}"
    )
    assert result.probes.movement_today is not None
    assert result.probes.movement_today <= 0.15, (
        f"STILL should yield low movement, got {result.probes.movement_today}"
    )
    assert result.probes.noosphere_load is not None
    assert result.probes.noosphere_load <= 0.05, (
        f"No thermal/ambient stress should yield ~0 noosphere_load, "
        f"got {result.probes.noosphere_load}"
    )


# ---------------------------------------------------------------------------
# T02 — High arousal inverts to low HRV
# ---------------------------------------------------------------------------

def test_T02_high_arousal_maps_to_low_hrv():
    """
    T02: High arousal (0.90) from skin conductance must map to HRV of ~0.10.
    This is the stress marker the D6Engine uses to recommend REST mode.
    """
    signals = [
        _make_modality_signal(
            SensorType.SKIN_CONDUCTANCE,
            arousal_estimate=0.90,   # high stress
        ),
    ]
    result = translate_signals_to_probes(signals, [])

    assert result.probes.heart_rate_variability is not None
    assert result.probes.heart_rate_variability <= 0.15, (
        f"High arousal should invert to low HRV, got {result.probes.heart_rate_variability}"
    )


# ---------------------------------------------------------------------------
# T03 — Safety-relevant sensor gap adds noosphere_load
# ---------------------------------------------------------------------------

def test_T03_safety_gap_adds_noosphere_load():
    """
    T03: A safety-relevant SensorUnavailableSignal must add 0.15 noosphere_load
    per gap. Two safety gaps must produce 0.30 noosphere_load.
    This is Wire 2's sentinel awareness feature.
    """
    unavailable = [
        _make_unavailable(safety_impact=True),
        _make_unavailable(safety_impact=True),
    ]
    result = translate_signals_to_probes([], unavailable)

    assert result.safety_gaps == 2
    assert result.probes.noosphere_load is not None
    assert abs(result.probes.noosphere_load - 0.30) < 0.01, (
        f"2 safety gaps should yield 0.30 noosphere_load, "
        f"got {result.probes.noosphere_load}"
    )


# ---------------------------------------------------------------------------
# T04 — Low-confidence signals are excluded
# ---------------------------------------------------------------------------

def test_T04_low_confidence_signals_excluded():
    """
    T04: Signals below the confidence threshold (0.60) must not contribute
    to any probe value. signals_used count must reflect exclusion.
    """
    signals = [
        _make_modality_signal(
            SensorType.SKIN_CONDUCTANCE,
            confidence=0.50,          # below threshold
            arousal_estimate=0.95,    # extreme — would corrupt probes if included
        ),
        _make_modality_signal(
            SensorType.IMU,
            confidence=0.90,          # above threshold
            activity_class=ActivityClass.WALKING.value,
        ),
    ]
    result = translate_signals_to_probes(signals, [], confidence_threshold=0.60)

    assert result.low_confidence == 1
    assert result.signals_used == 1   # only the IMU signal was used
    assert result.probes.heart_rate_variability is None, (
        "Low-confidence GSR signal must not populate HRV"
    )
    assert result.probes.movement_today is not None


# ---------------------------------------------------------------------------
# T05 — ESBtoD6Bridge.poll_once() returns correct types
# ---------------------------------------------------------------------------

def test_T05_poll_once_returns_probe_result_and_event():
    """
    T05: ESBtoD6Bridge.poll_once() must return a tuple of
    (ESBProbeResult, InterventionEvent) on every call.
    """
    state = default_state()
    engine = D6Engine(auto_apply=True)

    # Build a minimal ESB with one real adapter
    config = SensorConfig(
        sensor_id="imu-test",
        sensor_type=SensorType.IMU,
        enabled=True,
        display_name="Test IMU",
        safety_relevant=False,
    )
    esb = EmbodiedSensorBridge()
    esb.register(IMUAdapter(config))

    bridge = ESBtoD6Bridge(esb=esb, engine=engine, state=state)
    probe_result, event = bridge.poll_once()

    assert isinstance(probe_result, ESBProbeResult)
    assert probe_result.cycle_count == 0 or bridge.cycle_count == 1
    assert event is not None
    assert hasattr(event, "severity")
    assert hasattr(event, "recommended_mode")


# ---------------------------------------------------------------------------
# T06 — Background thread starts, cycles, and stops cleanly
# ---------------------------------------------------------------------------

def test_T06_background_thread_starts_and_stops():
    """
    T06: ESBtoD6Bridge.start() must launch a daemon thread. After start(),
    is_running must be True. After stop(), is_running must be False.
    cycle_count must increment at least once during a short run.
    """
    state = default_state()
    engine = D6Engine(auto_apply=False)

    config = SensorConfig(
        sensor_id="imu-bg",
        sensor_type=SensorType.IMU,
        enabled=True,
        display_name="BG IMU",
        safety_relevant=False,
    )
    esb = EmbodiedSensorBridge()
    esb.register(IMUAdapter(config))

    bridge = ESBtoD6Bridge(
        esb=esb,
        engine=engine,
        state=state,
        interval_seconds=0.05,  # fast polling for tests
    )
    bridge.start()
    assert bridge.is_running

    # Allow at least 3 cycles
    time.sleep(0.25)
    bridge.stop(timeout=2.0)

    assert not bridge.is_running
    assert bridge.cycle_count >= 1, (
        f"Expected at least 1 cycle, got {bridge.cycle_count}"
    )
    assert bridge.error_count == 0, (
        f"Expected 0 errors, got {bridge.error_count}"
    )


# ---------------------------------------------------------------------------
# T07 — Wire 2 → Wire 1: poll_once fires D6 on_intervention
# ---------------------------------------------------------------------------

def test_T07_poll_once_fires_on_intervention_callback():
    """
    T07: Wire 2 → Wire 1 integration test.

    ESBtoD6Bridge.poll_once() must trigger D6Engine.evaluate() which fires
    the on_intervention callback (Wire 1). This proves the two wires are
    connected end-to-end: sensors → probes → D6 decision → callback → HUD.
    """
    interventions_received = []

    def capture_intervention(event):
        interventions_received.append(event)

    state = default_state()
    engine = D6Engine(
        auto_apply=True,
        on_intervention=capture_intervention,  # Wire 1 callback
    )

    config = SensorConfig(
        sensor_id="gsr-wire",
        sensor_type=SensorType.SKIN_CONDUCTANCE,
        enabled=True,
        display_name="Wire Test GSR",
        safety_relevant=True,
    )
    esb = EmbodiedSensorBridge()
    esb.register(SkinConductanceAdapter(config))

    bridge = ESBtoD6Bridge(esb=esb, engine=engine, state=state)
    bridge.poll_once()

    assert len(interventions_received) >= 1, (
        "Wire 2 → Wire 1: poll_once() must fire on_intervention callback at least once"
    )
    event = interventions_received[0]
    assert hasattr(event, "severity")
    assert hasattr(event, "recommended_mode"), (
        f"InterventionEvent missing recommended_mode. Fields: {dir(event)}"
    )
