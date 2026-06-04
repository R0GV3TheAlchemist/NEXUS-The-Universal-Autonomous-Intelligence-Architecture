"""
core.sentinel.body
==================
Sentinel physical embodiment layer.

Modules
-------
esb.py   — Embodied Sensor Bridge (Issue #205)
"""

from core.sentinel.body.esb import (
    # Enums
    SensorType,
    SensorHealthState,
    ActivityClass,
    # Data contracts
    RawSensorData,
    ModalitySignal,
    SensorHealthStatus,
    SensorUnavailableSignal,
    SensorCalibrationProfile,
    SensorConfig,
    # Abstract base
    PhysicalSensorAdapter,
    # Reference implementations
    MicrophoneAdapter,
    CameraAdapter,
    ProximityAdapter,
    IMUAdapter,
    SkinConductanceAdapter,
    IRThermometerAdapter,
    # Bridge
    EmbodiedSensorBridge,
)

__all__ = [
    "SensorType",
    "SensorHealthState",
    "ActivityClass",
    "RawSensorData",
    "ModalitySignal",
    "SensorHealthStatus",
    "SensorUnavailableSignal",
    "SensorCalibrationProfile",
    "SensorConfig",
    "PhysicalSensorAdapter",
    "MicrophoneAdapter",
    "CameraAdapter",
    "ProximityAdapter",
    "IMUAdapter",
    "SkinConductanceAdapter",
    "IRThermometerAdapter",
    "EmbodiedSensorBridge",
]
