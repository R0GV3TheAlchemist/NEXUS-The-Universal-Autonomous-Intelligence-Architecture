"""
core.sentinel.body.esb
======================
Embodied Sensor Bridge (ESB) — translates raw physical robot sensor
streams into normalised ``ModalitySignal`` objects compatible with
GAIA-OS's Multi-Modal Sensory Fusion pipeline.

The intelligence layer (Sentinel) never needs to know whether its sensor
data originates from a wearable, a companion device, or a full humanoid.
The ESB makes every physical platform look identical to the fusion engine.

Canon refs:
  C01  — Sovereignty: Gaian explicitly controls which physical sensors are
         active.  No sensor activates without Gaian consent.

Pipeline
--------
  Physical Sensor Layer
          │
          ▼
  [Embodied Sensor Bridge]   ← this module
          │  translates + normalises
          ▼
  ModalitySignal stream
          │
          ▼
  Multi-Modal Sensory Fusion Engine → PerceptionFrame → Biometric Engine
          │
          ▼
  SynergyParams

Issue: #205
Depends on: #199 (Multi-Modal Sensory Fusion), #204 (Sentinel Body Abstraction Layer)
Enables:   #206 (Sentinel Safety Layer) ✅
"""

from __future__ import annotations

import math
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, TypedDict
import uuid


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SensorType(str, Enum):
    """Canonical sensor type identifiers used across the ESB."""
    MICROPHONE        = "microphone"
    MICROPHONE_AMBIENT = "microphone_ambient"
    CAMERA            = "camera"
    PROXIMITY         = "proximity"
    IMU               = "imu"
    SKIN_CONDUCTANCE  = "skin_conductance"
    IR_THERMOMETER    = "ir_thermometer"


class SensorHealthState(str, Enum):
    """Operational health state of a physical sensor."""
    OK          = "ok"           # Reading within expected parameters
    DEGRADED    = "degraded"     # Reading available but confidence reduced
    UNAVAILABLE = "unavailable"  # Sensor offline / no signal
    CALIBRATING = "calibrating"  # Undergoing calibration — readings held


class ActivityClass(str, Enum):
    """IMU-derived activity classifications."""
    STILL      = "still"
    WALKING    = "walking"
    RUNNING    = "running"
    DISTRESSED = "distressed"   # Sudden jerk / fall / erratic motion
    UNKNOWN    = "unknown"


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

class RawSensorData(TypedDict):
    """
    Raw payload from a physical sensor before any normalisation.
    Each sensor type populates only the fields relevant to its signal.
    """
    sensor_type:  str            # SensorType value
    sensor_id:    str            # Hardware identifier
    timestamp:    str            # ISO 8601 UTC
    # Microphone
    pcm_frames:   Optional[List[float]]   # Normalised PCM samples [-1, 1]
    db_spl:       Optional[float]         # Ambient dB SPL
    # Camera
    image_width:  Optional[int]
    image_height: Optional[int]
    has_depth:    Optional[bool]
    # Proximity
    distance_cm:  Optional[float]
    # IMU
    accel_x:      Optional[float]   # m/s²
    accel_y:      Optional[float]
    accel_z:      Optional[float]
    # Skin conductance
    resistance_ohm: Optional[float]
    # IR thermometer
    temp_celsius: Optional[float]


class ModalitySignal(TypedDict):
    """
    Normalised signal ready for the Multi-Modal Sensory Fusion Engine.
    Mirrors the contract established in Issue #199.
    """
    signal_id:       str    # UUID4
    sensor_type:     str    # SensorType value
    timestamp:       str    # ISO 8601 UTC
    confidence:      float  # [0.0, 1.0]
    # Normalised outputs (only relevant fields populated per sensor type)
    prosody_features:    Optional[Dict[str, float]]  # pitch, rate, energy, etc.
    transcript_hint:     Optional[str]               # lightweight STT hint
    ambient_stress_level: Optional[float]            # [0.0, 1.0]
    emotion_estimate:    Optional[str]               # e.g. "neutral", "distressed"
    gesture_label:       Optional[str]
    personal_space_m:    Optional[float]             # proximity → metres
    activity_class:      Optional[str]               # ActivityClass value
    arousal_estimate:    Optional[float]             # [0.0, 1.0]
    thermal_stress:      Optional[float]             # [0.0, 1.0]
    raw_ref:             Optional[str]               # sensor_id for traceability


@dataclass
class SensorHealthStatus:
    """
    Health snapshot for a single physical sensor.
    Emitted by every PhysicalSensorAdapter.health_check() call.
    """
    sensor_id:      str
    sensor_type:    str                # SensorType value
    state:          SensorHealthState
    last_reading_at: Optional[str]     # ISO 8601 UTC timestamp of last valid read
    confidence:     float              # Current signal confidence [0.0, 1.0]
    message:        str = ""           # Human-readable status note

    @property
    def is_healthy(self) -> bool:
        return self.state == SensorHealthState.OK


@dataclass
class SensorUnavailableSignal:
    """
    Emitted by the ESB when a sensor cannot produce a ModalitySignal.
    The Fusion Engine treats this as a missing modality and degrades
    gracefully — it does NOT crash the pipeline.
    """
    sensor_type:  str    # SensorType value
    sensor_id:    str
    timestamp:    str    # ISO 8601 UTC
    reason:       str    # "offline" | "calibrating" | "degraded" | "permission_denied"
    safety_impact: bool  # True if this sensor supports safety monitoring


@dataclass
class SensorCalibrationProfile:
    """
    Per-sensor calibration data stored in SentinelIdentityRecord.
    Created on first body activation; updated after body migration.
    """
    sensor_id:        str
    sensor_type:      str      # SensorType value
    calibrated_at:    str      # ISO 8601 UTC
    baseline_values:  Dict[str, float]  # Sensor-specific baseline readings
    drift_threshold:  float    # How far readings can drift before recalibration
    recalibration_due: bool = False


@dataclass
class SensorConfig:
    """
    Configuration for a physical sensor attached to a Sentinel body.
    Stored in SentinelIdentityRecord under ``sensor_configs``.
    """
    sensor_id:          str
    sensor_type:        str       # SensorType value
    enabled:            bool      # C01: Gaian controls this flag
    display_name:       str
    safety_relevant:    bool      # True → degradation triggers Gaian notification
    calibration:        Optional[SensorCalibrationProfile] = None
    hardware_meta:      Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract base: PhysicalSensorAdapter
# ---------------------------------------------------------------------------

class PhysicalSensorAdapter(ABC):
    """
    Abstract base for all physical sensor adapters.

    Extends the ModalityAdapter contract (Issue #199) with hardware-level
    sensor ingestion: raw reads, normalisation, and health reporting.

    Subclasses must implement:
      - read_raw()   → RawSensorData
      - normalize()  → ModalitySignal
      - health_check() → SensorHealthStatus
    """

    def __init__(self, config: SensorConfig) -> None:
        self._config    = config
        self._lock      = threading.Lock()
        self._last_read: Optional[str] = None

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def read_raw(self) -> RawSensorData:
        """Pull raw signal from hardware. Raises SensorReadError on failure."""
        ...

    @abstractmethod
    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        """Convert raw hardware data to a GAIA-compatible ModalitySignal."""
        ...

    @abstractmethod
    def health_check(self) -> SensorHealthStatus:
        """Return current sensor health status."""
        ...

    # ------------------------------------------------------------------
    # Concrete helpers
    # ------------------------------------------------------------------

    @property
    def sensor_id(self) -> str:
        return self._config.sensor_id

    @property
    def sensor_type(self) -> str:
        return self._config.sensor_type

    @property
    def enabled(self) -> bool:
        """C01: Gaian-controlled enable flag."""
        return self._config.enabled

    def acquire(self) -> ModalitySignal | SensorUnavailableSignal:
        """
        Full acquire cycle: check enabled → read_raw → normalize.
        Returns SensorUnavailableSignal on any failure or when disabled.
        """
        if not self.enabled:
            return self._unavailable("permission_denied")

        health = self.health_check()
        if health.state == SensorHealthState.UNAVAILABLE:
            return self._unavailable("offline")
        if health.state == SensorHealthState.CALIBRATING:
            return self._unavailable("calibrating")

        try:
            raw = self.read_raw()
            with self._lock:
                self._last_read = raw["timestamp"]
            return self.normalize(raw)
        except Exception as exc:  # noqa: BLE001
            return self._unavailable(f"read_error: {exc}")

    def _unavailable(self, reason: str) -> SensorUnavailableSignal:
        return SensorUnavailableSignal(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            safety_impact=self._config.safety_relevant,
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _new_signal_id() -> str:
        return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Reference implementation 1: MicrophoneAdapter
# ---------------------------------------------------------------------------

class MicrophoneAdapter(PhysicalSensorAdapter):
    """
    Adapter for a microphone array on a physical Sentinel body.

    Normalised output:
      - ``prosody_features``  — pitch variance, speech rate, energy level
      - ``transcript_hint``   — lightweight phoneme-level STT hint (stub)
      - ``ambient_stress_level`` — for MICROPHONE_AMBIENT type

    In production, ``read_raw`` would be wired to the audio HAL / driver.
    The stub implementation generates deterministic test data.
    """

    # Prosody feature extraction constants
    _SPEECH_RATE_NORMAL   = 130.0   # words/min baseline
    _PITCH_BASELINE_HZ    = 120.0   # fundamental frequency baseline

    def read_raw(self) -> RawSensorData:
        """Stub: returns a synthetic PCM burst."""
        return RawSensorData(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=self._now_iso(),
            pcm_frames=[0.1, -0.2, 0.3, -0.1, 0.05] * 20,   # 100-sample stub
            db_spl=None,
            image_width=None, image_height=None, has_depth=None,
            distance_cm=None,
            accel_x=None, accel_y=None, accel_z=None,
            resistance_ohm=None,
            temp_celsius=None,
        )

    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        """
        Extract prosody features from PCM frames.
        Production version would run a local prosody model.
        """
        pcm = raw.get("pcm_frames") or []
        db  = raw.get("db_spl")

        if self.sensor_type == SensorType.MICROPHONE_AMBIENT:
            # Ambient mic: map dB SPL to [0, 1] stress proxy
            spl = db if db is not None else (20.0 if not pcm else
                  20.0 * math.log10(max(abs(s) for s in pcm) + 1e-9) + 94)
            ambient_stress = min(1.0, max(0.0, (spl - 40.0) / 60.0))
            return ModalitySignal(
                signal_id=self._new_signal_id(),
                sensor_type=self.sensor_type,
                timestamp=raw["timestamp"],
                confidence=0.80,
                prosody_features=None,
                transcript_hint=None,
                ambient_stress_level=round(ambient_stress, 3),
                emotion_estimate=None,
                gesture_label=None,
                personal_space_m=None,
                activity_class=None,
                arousal_estimate=None,
                thermal_stress=None,
                raw_ref=raw["sensor_id"],
            )

        # Standard microphone: extract simplified prosody features
        energy = math.sqrt(sum(s ** 2 for s in pcm) / len(pcm)) if pcm else 0.0
        pitch_var = float(max(pcm) - min(pcm)) if pcm else 0.0
        # Stub speech rate: scale energy → estimated words/min proxy
        speech_rate = self._SPEECH_RATE_NORMAL * (0.8 + energy * 2.0)

        prosody = {
            "energy":       round(energy, 4),
            "pitch_variance": round(pitch_var, 4),
            "speech_rate":  round(speech_rate, 2),
        }
        confidence = 0.75 if energy < 0.01 else 0.90

        return ModalitySignal(
            signal_id=self._new_signal_id(),
            sensor_type=self.sensor_type,
            timestamp=raw["timestamp"],
            confidence=confidence,
            prosody_features=prosody,
            transcript_hint="[stub-transcript]",
            ambient_stress_level=None,
            emotion_estimate=None,
            gesture_label=None,
            personal_space_m=None,
            activity_class=None,
            arousal_estimate=None,
            thermal_stress=None,
            raw_ref=raw["sensor_id"],
        )

    def health_check(self) -> SensorHealthStatus:
        return SensorHealthStatus(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            state=SensorHealthState.OK,
            last_reading_at=self._last_read,
            confidence=0.90,
            message="Microphone array nominal.",
        )


# ---------------------------------------------------------------------------
# Reference implementation 2: CameraAdapter
# ---------------------------------------------------------------------------

class CameraAdapter(PhysicalSensorAdapter):
    """
    Adapter for an RGB/depth camera on a physical Sentinel body.

    Normalised output:
      - ``emotion_estimate``   — simple emotion label from frame analysis
      - ``gesture_label``      — gesture classification stub
      - ``personal_space_m``   — depth-derived proximity in metres

    In production, ``read_raw`` receives frames from the camera driver and
    ``normalize`` runs a local vision model (e.g. MorphCast or equivalent).
    """

    _EMOTION_LABELS = ["neutral", "calm", "curious", "stressed", "happy"]

    def read_raw(self) -> RawSensorData:
        """Stub: returns synthetic camera frame metadata."""
        return RawSensorData(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=self._now_iso(),
            image_width=640,
            image_height=480,
            has_depth=True,
            distance_cm=75.0,   # Stub: 75cm — within personal space
            pcm_frames=None, db_spl=None,
            accel_x=None, accel_y=None, accel_z=None,
            resistance_ohm=None,
            temp_celsius=None,
        )

    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        """
        Extract emotion estimate, gesture, and proximity from camera frame.
        """
        distance_cm = raw.get("distance_cm") or 100.0
        personal_space_m = round(distance_cm / 100.0, 3)

        # In production: run vision model on raw frames
        # Stub: deterministic outputs
        emotion = "neutral"
        gesture = "idle"
        confidence = 0.70 if not raw.get("has_depth") else 0.85

        return ModalitySignal(
            signal_id=self._new_signal_id(),
            sensor_type=self.sensor_type,
            timestamp=raw["timestamp"],
            confidence=confidence,
            prosody_features=None,
            transcript_hint=None,
            ambient_stress_level=None,
            emotion_estimate=emotion,
            gesture_label=gesture,
            personal_space_m=personal_space_m,
            activity_class=None,
            arousal_estimate=None,
            thermal_stress=None,
            raw_ref=raw["sensor_id"],
        )

    def health_check(self) -> SensorHealthStatus:
        return SensorHealthStatus(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            state=SensorHealthState.OK,
            last_reading_at=self._last_read,
            confidence=0.85,
            message="Camera nominal.",
        )


# ---------------------------------------------------------------------------
# Reference implementation 3: ProximityAdapter
# ---------------------------------------------------------------------------

class ProximityAdapter(PhysicalSensorAdapter):
    """
    Adapter for an IR/ultrasonic proximity sensor.

    Normalised output:
      - ``personal_space_m``  — distance in metres

    Personal space thresholds (Hall's proxemics):
      < 0.45m  — intimate zone  (high alert for safety layer)
      0.45–1.2m — personal zone
      > 1.2m   — social/public zone
    """

    def read_raw(self) -> RawSensorData:
        """Stub: 80cm distance reading."""
        return RawSensorData(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=self._now_iso(),
            distance_cm=80.0,
            pcm_frames=None, db_spl=None,
            image_width=None, image_height=None, has_depth=None,
            accel_x=None, accel_y=None, accel_z=None,
            resistance_ohm=None,
            temp_celsius=None,
        )

    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        distance_cm = raw.get("distance_cm")
        if distance_cm is None:
            raise ValueError("ProximityAdapter: distance_cm missing from raw data.")

        personal_space_m = round(distance_cm / 100.0, 3)
        # Confidence degrades for very short or very long distances
        confidence = 0.95 if 5.0 <= distance_cm <= 300.0 else 0.60

        return ModalitySignal(
            signal_id=self._new_signal_id(),
            sensor_type=self.sensor_type,
            timestamp=raw["timestamp"],
            confidence=confidence,
            prosody_features=None,
            transcript_hint=None,
            ambient_stress_level=None,
            emotion_estimate=None,
            gesture_label=None,
            personal_space_m=personal_space_m,
            activity_class=None,
            arousal_estimate=None,
            thermal_stress=None,
            raw_ref=raw["sensor_id"],
        )

    def health_check(self) -> SensorHealthStatus:
        return SensorHealthStatus(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            state=SensorHealthState.OK,
            last_reading_at=self._last_read,
            confidence=0.95,
            message="Proximity sensor nominal.",
        )


# ---------------------------------------------------------------------------
# Additional adapters: IMU, SkinConductanceAdapter, IRThermometerAdapter
# ---------------------------------------------------------------------------

class IMUAdapter(PhysicalSensorAdapter):
    """
    Adapter for an IMU / accelerometer (3-axis).
    Produces activity classification: still / walking / running / distressed.
    """

    # Magnitude thresholds (m/s²)
    _STILL_MAX    = 0.5
    _WALKING_MAX  = 3.0
    _RUNNING_MAX  = 8.0

    def read_raw(self) -> RawSensorData:
        """Stub: gentle upright standing."""
        return RawSensorData(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=self._now_iso(),
            accel_x=0.05, accel_y=0.02, accel_z=9.81,
            pcm_frames=None, db_spl=None,
            image_width=None, image_height=None, has_depth=None,
            distance_cm=None,
            resistance_ohm=None, temp_celsius=None,
        )

    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        ax = raw.get("accel_x") or 0.0
        ay = raw.get("accel_y") or 0.0
        az = raw.get("accel_z") or 0.0

        # Subtract gravity component (assumes z-axis aligned with gravity)
        lateral_mag = math.sqrt(ax ** 2 + ay ** 2 + max(0.0, abs(az) - 9.81) ** 2)

        if lateral_mag <= self._STILL_MAX:
            activity = ActivityClass.STILL
        elif lateral_mag <= self._WALKING_MAX:
            activity = ActivityClass.WALKING
        elif lateral_mag <= self._RUNNING_MAX:
            activity = ActivityClass.RUNNING
        else:
            activity = ActivityClass.DISTRESSED

        return ModalitySignal(
            signal_id=self._new_signal_id(),
            sensor_type=self.sensor_type,
            timestamp=raw["timestamp"],
            confidence=0.88,
            prosody_features=None,
            transcript_hint=None,
            ambient_stress_level=None,
            emotion_estimate=None,
            gesture_label=None,
            personal_space_m=None,
            activity_class=activity.value,
            arousal_estimate=None,
            thermal_stress=None,
            raw_ref=raw["sensor_id"],
        )

    def health_check(self) -> SensorHealthStatus:
        return SensorHealthStatus(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            state=SensorHealthState.OK,
            last_reading_at=self._last_read,
            confidence=0.88,
            message="IMU nominal.",
        )


class SkinConductanceAdapter(PhysicalSensorAdapter):
    """
    Adapter for a galvanic skin response (GSR) / EDA sensor.
    Maps resistance (Ω) → arousal estimate [0.0, 1.0].

    Lower resistance = higher conductance = higher arousal.
    Typical range: 10kΩ (high arousal) to 4MΩ (baseline calm).
    """

    _BASELINE_OHMS  = 1_000_000.0   # 1MΩ — resting baseline
    _HIGH_AROUSAL   = 10_000.0      # 10kΩ — high arousal floor

    def read_raw(self) -> RawSensorData:
        """Stub: calm baseline reading."""
        return RawSensorData(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=self._now_iso(),
            resistance_ohm=800_000.0,   # Slightly below baseline — mild activation
            pcm_frames=None, db_spl=None,
            image_width=None, image_height=None, has_depth=None,
            distance_cm=None,
            accel_x=None, accel_y=None, accel_z=None,
            temp_celsius=None,
        )

    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        ohms = raw.get("resistance_ohm") or self._BASELINE_OHMS
        ohms = max(self._HIGH_AROUSAL, ohms)  # clamp to valid range

        # Invert and normalise: high resistance → low arousal
        arousal = 1.0 - min(1.0, (ohms - self._HIGH_AROUSAL) /
                             (self._BASELINE_OHMS - self._HIGH_AROUSAL))
        arousal = round(arousal, 3)

        return ModalitySignal(
            signal_id=self._new_signal_id(),
            sensor_type=self.sensor_type,
            timestamp=raw["timestamp"],
            confidence=0.82,
            prosody_features=None,
            transcript_hint=None,
            ambient_stress_level=None,
            emotion_estimate=None,
            gesture_label=None,
            personal_space_m=None,
            activity_class=None,
            arousal_estimate=arousal,
            thermal_stress=None,
            raw_ref=raw["sensor_id"],
        )

    def health_check(self) -> SensorHealthStatus:
        return SensorHealthStatus(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            state=SensorHealthState.OK,
            last_reading_at=self._last_read,
            confidence=0.82,
            message="Skin conductance sensor nominal.",
        )


class IRThermometerAdapter(PhysicalSensorAdapter):
    """
    Adapter for an IR / contact thermometer.
    Maps body temperature (°C) → thermal_stress [0.0, 1.0].

    Thresholds:
      < 36.1°C  — hypothermia risk
      36.1–37.2°C — normal
      37.3–38.0°C — low fever
      > 38.0°C  — high fever / stress
    """

    _NORMAL_LOW  = 36.1
    _NORMAL_HIGH = 37.2
    _FEVER_HIGH  = 40.0

    def read_raw(self) -> RawSensorData:
        """Stub: normal body temperature."""
        return RawSensorData(
            sensor_type=self.sensor_type,
            sensor_id=self.sensor_id,
            timestamp=self._now_iso(),
            temp_celsius=36.8,
            pcm_frames=None, db_spl=None,
            image_width=None, image_height=None, has_depth=None,
            distance_cm=None,
            accel_x=None, accel_y=None, accel_z=None,
            resistance_ohm=None,
        )

    def normalize(self, raw: RawSensorData) -> ModalitySignal:
        temp = raw.get("temp_celsius") or 37.0

        if temp < self._NORMAL_LOW:
            thermal_stress = min(1.0, (self._NORMAL_LOW - temp) / 2.0)
        elif temp <= self._NORMAL_HIGH:
            thermal_stress = 0.0
        else:
            thermal_stress = min(1.0, (temp - self._NORMAL_HIGH) /
                                  (self._FEVER_HIGH - self._NORMAL_HIGH))

        return ModalitySignal(
            signal_id=self._new_signal_id(),
            sensor_type=self.sensor_type,
            timestamp=raw["timestamp"],
            confidence=0.93,
            prosody_features=None,
            transcript_hint=None,
            ambient_stress_level=None,
            emotion_estimate=None,
            gesture_label=None,
            personal_space_m=None,
            activity_class=None,
            arousal_estimate=None,
            thermal_stress=round(thermal_stress, 3),
            raw_ref=raw["sensor_id"],
        )

    def health_check(self) -> SensorHealthStatus:
        return SensorHealthStatus(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            state=SensorHealthState.OK,
            last_reading_at=self._last_read,
            confidence=0.93,
            message="IR thermometer nominal.",
        )


# ---------------------------------------------------------------------------
# Embodied Sensor Bridge — orchestrator
# ---------------------------------------------------------------------------

class EmbodiedSensorBridge:
    """
    Top-level orchestrator for all physical sensor adapters on a Sentinel body.

    Responsibilities
    ----------------
    - Register sensor adapters (one per physical sensor)
    - Acquire a full set of ModalitySignals in one call
    - Report sensor health and surface degradation events
    - Notify the Gaian (via callback) when a safety-relevant sensor degrades

    Canon C01: Gaian controls the ``enabled`` flag on each SensorConfig.
    The ESB never activates a sensor the Gaian has disabled.
    """

    def __init__(
        self,
        gaian_notification_callback: Optional[object] = None,
    ) -> None:
        """
        Parameters
        ----------
        gaian_notification_callback:
            Optional callable(SensorUnavailableSignal) that is invoked
            when a safety-relevant sensor becomes unavailable.  In
            production this wires to the Sentinel notification layer.
        """
        self._adapters: Dict[str, PhysicalSensorAdapter] = {}
        self._lock     = threading.RLock()
        self._notify   = gaian_notification_callback

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, adapter: PhysicalSensorAdapter) -> None:
        """Register a sensor adapter. Replaces any existing adapter with the same sensor_id."""
        with self._lock:
            self._adapters[adapter.sensor_id] = adapter

    def unregister(self, sensor_id: str) -> None:
        """Remove a sensor adapter."""
        with self._lock:
            self._adapters.pop(sensor_id, None)

    # ------------------------------------------------------------------
    # Acquisition
    # ------------------------------------------------------------------

    def acquire_all(
        self,
    ) -> tuple[List[ModalitySignal], List[SensorUnavailableSignal]]:
        """
        Acquire a ModalitySignal from every registered, enabled sensor.

        Returns
        -------
        (signals, unavailable)
            signals      — list of successfully normalised ModalitySignals
            unavailable  — list of SensorUnavailableSignals for failed sensors
        """
        signals: List[ModalitySignal] = []
        unavailable: List[SensorUnavailableSignal] = []

        with self._lock:
            adapters = list(self._adapters.values())

        for adapter in adapters:
            result = adapter.acquire()
            if isinstance(result, SensorUnavailableSignal):
                unavailable.append(result)
                self._handle_degradation(result)
            else:
                signals.append(result)

        return signals, unavailable

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_report(self) -> List[SensorHealthStatus]:
        """Return health status for every registered sensor."""
        with self._lock:
            adapters = list(self._adapters.values())
        return [adapter.health_check() for adapter in adapters]

    def all_healthy(self) -> bool:
        """True iff every registered, enabled sensor is in OK state."""
        return all(
            s.state == SensorHealthState.OK
            for s in self.health_report()
            if self._adapters[s.sensor_id].enabled
        )

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate(self, sensor_id: str) -> SensorCalibrationProfile:
        """
        Trigger calibration for a specific sensor.
        Returns the updated SensorCalibrationProfile.

        In production this initiates a hardware calibration sequence.
        The stub captures a baseline reading as the calibration profile.
        """
        with self._lock:
            if sensor_id not in self._adapters:
                raise KeyError(f"Sensor {sensor_id!r} not registered.")
            adapter = self._adapters[sensor_id]

        raw = adapter.read_raw()
        baseline: Dict[str, float] = {}

        # Extract the primary numeric field as the baseline
        for key in ("distance_cm", "resistance_ohm", "temp_celsius", "db_spl"):
            val = raw.get(key)
            if val is not None:
                baseline[key] = float(val)

        profile = SensorCalibrationProfile(
            sensor_id=sensor_id,
            sensor_type=adapter.sensor_type,
            calibrated_at=datetime.now(timezone.utc).isoformat(),
            baseline_values=baseline,
            drift_threshold=0.15,
        )

        # Store calibration back into the adapter's config
        adapter._config.calibration = profile  # noqa: SLF001
        return profile

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_degradation(self, signal: SensorUnavailableSignal) -> None:
        """Log degradation and notify Gaian if the sensor is safety-relevant."""
        if signal.safety_impact and self._notify is not None:
            try:
                self._notify(signal)
            except Exception:  # noqa: BLE001
                pass  # Notification failure must never crash the ESB
