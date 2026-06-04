"""
tests.sentinel.test_esb
=======================
Unit + integration tests for the Embodied Sensor Bridge (Issue #205).

Coverage
--------
- Normalisation for all 6 sensor types
- SensorHealthStatus reporting
- Graceful degradation → SensorUnavailableSignal
- Calibration flow
- EmbodiedSensorBridge acquire_all() / health_report()
- C01: disabled sensor never produces a ModalitySignal
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from core.sentinel.body.esb import (
    ActivityClass,
    CameraAdapter,
    EmbodiedSensorBridge,
    IMUAdapter,
    IRThermometerAdapter,
    MicrophoneAdapter,
    ModalitySignal,
    PhysicalSensorAdapter,
    ProximityAdapter,
    RawSensorData,
    SensorCalibrationProfile,
    SensorConfig,
    SensorHealthState,
    SensorHealthStatus,
    SensorType,
    SensorUnavailableSignal,
    SkinConductanceAdapter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _config(
    sensor_type: str = SensorType.MICROPHONE,
    sensor_id: str = "sensor-001",
    enabled: bool = True,
    safety_relevant: bool = False,
) -> SensorConfig:
    return SensorConfig(
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        enabled=enabled,
        display_name=f"{sensor_type}-test",
        safety_relevant=safety_relevant,
    )


# ---------------------------------------------------------------------------
# MicrophoneAdapter
# ---------------------------------------------------------------------------

class TestMicrophoneAdapter:
    def test_normalize_returns_modality_signal(self):
        adapter = MicrophoneAdapter(_config(SensorType.MICROPHONE))
        raw = adapter.read_raw()
        signal = adapter.normalize(raw)
        assert isinstance(signal, dict)
        assert signal["sensor_type"] == SensorType.MICROPHONE
        assert signal["prosody_features"] is not None
        assert "energy" in signal["prosody_features"]
        assert 0.0 <= signal["confidence"] <= 1.0

    def test_ambient_mic_produces_ambient_stress(self):
        adapter = MicrophoneAdapter(_config(SensorType.MICROPHONE_AMBIENT))
        raw = adapter.read_raw()
        signal = adapter.normalize(raw)
        assert signal["ambient_stress_level"] is not None
        assert signal["prosody_features"] is None

    def test_health_check_ok(self):
        adapter = MicrophoneAdapter(_config())
        status = adapter.health_check()
        assert status.state == SensorHealthState.OK
        assert status.is_healthy

    def test_acquire_returns_signal_when_enabled(self):
        adapter = MicrophoneAdapter(_config(enabled=True))
        result = adapter.acquire()
        assert isinstance(result, dict)  # ModalitySignal is a TypedDict (dict)

    def test_acquire_returns_unavailable_when_disabled(self):
        adapter = MicrophoneAdapter(_config(enabled=False))
        result = adapter.acquire()
        assert isinstance(result, SensorUnavailableSignal)
        assert result.reason == "permission_denied"


# ---------------------------------------------------------------------------
# CameraAdapter
# ---------------------------------------------------------------------------

class TestCameraAdapter:
    def test_normalize_produces_emotion_and_proximity(self):
        adapter = CameraAdapter(_config(SensorType.CAMERA))
        raw = adapter.read_raw()
        signal = adapter.normalize(raw)
        assert signal["emotion_estimate"] is not None
        assert signal["personal_space_m"] is not None
        assert signal["personal_space_m"] == pytest.approx(0.75, abs=0.01)

    def test_confidence_higher_with_depth(self):
        adapter = CameraAdapter(_config(SensorType.CAMERA))
        raw = adapter.read_raw()
        raw["has_depth"] = True
        signal_with_depth = adapter.normalize(raw)
        raw["has_depth"] = False
        signal_no_depth = adapter.normalize(raw)
        assert signal_with_depth["confidence"] > signal_no_depth["confidence"]

    def test_health_check_ok(self):
        adapter = CameraAdapter(_config(SensorType.CAMERA))
        assert adapter.health_check().is_healthy


# ---------------------------------------------------------------------------
# ProximityAdapter
# ---------------------------------------------------------------------------

class TestProximityAdapter:
    def test_normalize_distance_conversion(self):
        adapter = ProximityAdapter(_config(SensorType.PROXIMITY))
        raw = adapter.read_raw()
        signal = adapter.normalize(raw)
        assert signal["personal_space_m"] == pytest.approx(0.80, abs=0.01)

    def test_low_confidence_for_extreme_distances(self):
        adapter = ProximityAdapter(_config(SensorType.PROXIMITY))
        raw = adapter.read_raw()
        raw["distance_cm"] = 2.0   # Too close — out of reliable range
        signal = adapter.normalize(raw)
        assert signal["confidence"] < 0.90

    def test_missing_distance_raises(self):
        adapter = ProximityAdapter(_config(SensorType.PROXIMITY))
        raw = adapter.read_raw()
        raw["distance_cm"] = None
        with pytest.raises(ValueError, match="distance_cm"):
            adapter.normalize(raw)


# ---------------------------------------------------------------------------
# IMUAdapter
# ---------------------------------------------------------------------------

class TestIMUAdapter:
    def test_still_classification(self):
        adapter = IMUAdapter(_config(SensorType.IMU))
        raw = adapter.read_raw()  # stub is still/standing
        signal = adapter.normalize(raw)
        assert signal["activity_class"] == ActivityClass.STILL

    def test_distressed_classification_high_accel(self):
        adapter = IMUAdapter(_config(SensorType.IMU))
        raw = adapter.read_raw()
        raw["accel_x"] = 15.0
        raw["accel_y"] = 12.0
        signal = adapter.normalize(raw)
        assert signal["activity_class"] == ActivityClass.DISTRESSED

    def test_walking_classification(self):
        adapter = IMUAdapter(_config(SensorType.IMU))
        raw = adapter.read_raw()
        raw["accel_x"] = 1.5
        raw["accel_y"] = 1.0
        signal = adapter.normalize(raw)
        assert signal["activity_class"] == ActivityClass.WALKING


# ---------------------------------------------------------------------------
# SkinConductanceAdapter
# ---------------------------------------------------------------------------

class TestSkinConductanceAdapter:
    def test_high_resistance_low_arousal(self):
        adapter = SkinConductanceAdapter(_config(SensorType.SKIN_CONDUCTANCE))
        raw = adapter.read_raw()
        raw["resistance_ohm"] = 4_000_000.0   # Very high resistance = very calm
        signal = adapter.normalize(raw)
        assert signal["arousal_estimate"] is not None
        assert signal["arousal_estimate"] < 0.2

    def test_low_resistance_high_arousal(self):
        adapter = SkinConductanceAdapter(_config(SensorType.SKIN_CONDUCTANCE))
        raw = adapter.read_raw()
        raw["resistance_ohm"] = 10_000.0   # Low resistance = high arousal
        signal = adapter.normalize(raw)
        assert signal["arousal_estimate"] >= 0.99

    def test_arousal_bounded(self):
        adapter = SkinConductanceAdapter(_config(SensorType.SKIN_CONDUCTANCE))
        raw = adapter.read_raw()
        for ohms in [100, 10_000, 500_000, 2_000_000, 10_000_000]:
            raw["resistance_ohm"] = float(ohms)
            signal = adapter.normalize(raw)
            assert 0.0 <= signal["arousal_estimate"] <= 1.0


# ---------------------------------------------------------------------------
# IRThermometerAdapter
# ---------------------------------------------------------------------------

class TestIRThermometerAdapter:
    def test_normal_temp_zero_stress(self):
        adapter = IRThermometerAdapter(_config(SensorType.IR_THERMOMETER))
        raw = adapter.read_raw()  # stub = 36.8°C
        signal = adapter.normalize(raw)
        assert signal["thermal_stress"] == 0.0

    def test_fever_produces_stress(self):
        adapter = IRThermometerAdapter(_config(SensorType.IR_THERMOMETER))
        raw = adapter.read_raw()
        raw["temp_celsius"] = 39.5
        signal = adapter.normalize(raw)
        assert signal["thermal_stress"] > 0.5

    def test_hypothermia_produces_stress(self):
        adapter = IRThermometerAdapter(_config(SensorType.IR_THERMOMETER))
        raw = adapter.read_raw()
        raw["temp_celsius"] = 34.0
        signal = adapter.normalize(raw)
        assert signal["thermal_stress"] > 0.0

    def test_stress_bounded(self):
        adapter = IRThermometerAdapter(_config(SensorType.IR_THERMOMETER))
        raw = adapter.read_raw()
        for temp in [30.0, 36.5, 37.0, 38.5, 42.0]:
            raw["temp_celsius"] = temp
            signal = adapter.normalize(raw)
            assert 0.0 <= signal["thermal_stress"] <= 1.0


# ---------------------------------------------------------------------------
# EmbodiedSensorBridge — orchestrator
# ---------------------------------------------------------------------------

class TestEmbodiedSensorBridge:
    def _build_bridge(self, notify_cb=None) -> EmbodiedSensorBridge:
        bridge = EmbodiedSensorBridge(gaian_notification_callback=notify_cb)
        bridge.register(MicrophoneAdapter(_config(SensorType.MICROPHONE, "mic-01")))
        bridge.register(CameraAdapter(_config(SensorType.CAMERA, "cam-01")))
        bridge.register(ProximityAdapter(_config(SensorType.PROXIMITY, "prox-01")))
        bridge.register(IMUAdapter(_config(SensorType.IMU, "imu-01")))
        return bridge

    def test_acquire_all_returns_signals_for_all_enabled(self):
        bridge = self._build_bridge()
        signals, unavailable = bridge.acquire_all()
        assert len(signals) == 4
        assert len(unavailable) == 0

    def test_disabled_sensor_produces_unavailable(self):
        bridge = EmbodiedSensorBridge()
        bridge.register(
            MicrophoneAdapter(_config(SensorType.MICROPHONE, "mic-off", enabled=False))
        )
        signals, unavailable = bridge.acquire_all()
        assert len(signals) == 0
        assert len(unavailable) == 1
        assert unavailable[0].reason == "permission_denied"

    def test_health_report_all_ok(self):
        bridge = self._build_bridge()
        report = bridge.health_report()
        assert len(report) == 4
        assert all(s.is_healthy for s in report)

    def test_all_healthy(self):
        bridge = self._build_bridge()
        assert bridge.all_healthy() is True

    def test_safety_relevant_degradation_triggers_callback(self):
        notified = []
        bridge = EmbodiedSensorBridge(gaian_notification_callback=notified.append)

        # Register a sensor that is disabled AND safety-relevant
        cfg = _config(SensorType.PROXIMITY, "prox-safety",
                      enabled=False, safety_relevant=True)
        bridge.register(ProximityAdapter(cfg))

        bridge.acquire_all()
        assert len(notified) == 1
        assert notified[0].safety_impact is True

    def test_calibrate_returns_profile(self):
        bridge = EmbodiedSensorBridge()
        bridge.register(ProximityAdapter(_config(SensorType.PROXIMITY, "prox-cal")))
        profile = bridge.calibrate("prox-cal")
        assert isinstance(profile, SensorCalibrationProfile)
        assert "distance_cm" in profile.baseline_values
        assert profile.sensor_id == "prox-cal"

    def test_calibrate_unknown_sensor_raises(self):
        bridge = EmbodiedSensorBridge()
        with pytest.raises(KeyError):
            bridge.calibrate("nonexistent")

    def test_unregister_removes_sensor(self):
        bridge = self._build_bridge()
        bridge.unregister("mic-01")
        signals, _ = bridge.acquire_all()
        sensor_types = [s["sensor_type"] for s in signals]
        assert SensorType.MICROPHONE not in sensor_types


# ---------------------------------------------------------------------------
# Pipeline integration test
# physical sensor → ESB → ModalitySignal → ready for PerceptionFrame
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    def test_full_pipeline_produces_valid_modality_signals(self):
        """Verify every signal exiting the ESB satisfies the ModalitySignal contract."""
        bridge = EmbodiedSensorBridge()
        for sensor_type, adapter_cls, sid in [
            (SensorType.MICROPHONE,       MicrophoneAdapter,       "mic"),
            (SensorType.CAMERA,           CameraAdapter,           "cam"),
            (SensorType.PROXIMITY,        ProximityAdapter,        "prox"),
            (SensorType.IMU,              IMUAdapter,              "imu"),
            (SensorType.SKIN_CONDUCTANCE, SkinConductanceAdapter,  "gsr"),
            (SensorType.IR_THERMOMETER,   IRThermometerAdapter,    "ir"),
        ]:
            cfg = _config(sensor_type, sid)
            bridge.register(adapter_cls(cfg))

        signals, unavailable = bridge.acquire_all()
        assert len(unavailable) == 0, f"Unexpected unavailable signals: {unavailable}"
        assert len(signals) == 6

        required_keys = {
            "signal_id", "sensor_type", "timestamp", "confidence"
        }
        for sig in signals:
            assert required_keys.issubset(sig.keys()), \
                f"Signal missing required keys: {sig}"
            assert sig["signal_id"]   # non-empty UUID
            assert sig["timestamp"]   # non-empty ISO string
            assert 0.0 <= sig["confidence"] <= 1.0
