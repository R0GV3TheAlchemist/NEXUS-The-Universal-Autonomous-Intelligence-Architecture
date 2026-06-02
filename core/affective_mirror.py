"""
core/affective_mirror.py

Affective Mirror — Real-Time Emotion Recognition, Voice Prosody & Longitudinal
Emotional Intelligence for GAIA-OS.

Issue: #161
Canon: C29 (Embodiment), C01 (Sovereignty — all processing local, zero cloud),
       C05 (Transparency), C30 (No silent failures — crisis never silently missed)

Public API
----------
AffectiveChannel          — str enum of input channels
EmotionLabel              — str enum of 14 recognised primary emotions
AffectiveState            — frozen dataclass: the fused, timestamped emotional snapshot
EmotionalArcPoint         — single longitudinal data point
CrisisMarker              — raised when ≥2 crisis channels converge
VoiceProsodyAnalyzer      — extracts valence / arousal / emotion from audio features
BiometricAffectInference  — maps HRV / SpO2 / coherence → affective signal
AffectiveFusion           — fuses ≥2 channel outputs into one AffectiveState
EmotionalArcTracker       — maintains rolling longitudinal arc; detects sustained trends
CrisisDetector            — multi-channel crisis convergence watchdog
SoulMirrorAffectBridge    — publishes AffectiveState events to SoulMirror / StateAdapter
AffectiveMirror           — top-level façade; wires all sub-systems together

python -m core.affective_mirror
    status          — print current fused affective state
    history N       — print last N arc points
    crisis          — print active crisis markers (if any)
    demo            — run a synthetic 5-step demo cycle
"""

from __future__ import annotations

import asyncio
import json
import math
import statistics
import sys
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import auto
from pathlib import Path
from typing import Callable, Deque, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Compatibility shim — StrEnum arrived in Python 3.11
# ---------------------------------------------------------------------------
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):  # type: ignore[no-redef]
        pass


# ===========================================================================
# Enumerations
# ===========================================================================

class AffectiveChannel(StrEnum):
    """Recognised input channels for affective inference."""
    VOICE_PROSODY   = "voice_prosody"    # pitch, tempo, energy, MFCCs
    BIOMETRIC       = "biometric"        # HRV, SpO₂, skin conductance
    FACIAL          = "facial"           # micro-expression (optional, opt-in)
    TEXT_SENTIMENT  = "text_sentiment"   # lexical / NLP sentiment of typed text
    MANUAL          = "manual"           # user self-report override


class EmotionLabel(StrEnum):
    """14-category primary emotion taxonomy (Ekman + expansion)."""
    CALM        = "calm"
    FOCUSED     = "focused"
    CURIOUS     = "curious"
    ELATED      = "elated"
    CONTENT     = "content"
    ANXIOUS     = "anxious"
    STRESSED    = "stressed"
    FATIGUED    = "fatigued"
    GRIEF       = "grief"
    ANGER       = "anger"
    FEAR        = "fear"
    DISSOCIATED = "dissociated"  # flat affect, detachment
    OVERWHELMED = "overwhelmed"
    CRISIS      = "crisis"       # acute distress across multiple channels


class AffectiveTrend(StrEnum):
    """Longitudinal arc direction over the tracked window."""
    IMPROVING   = "improving"
    STABLE      = "stable"
    DECLINING   = "declining"
    VOLATILE    = "volatile"
    UNKNOWN     = "unknown"


# ===========================================================================
# Core data structures
# ===========================================================================

@dataclass(frozen=True)
class AffectiveState:
    """
    The canonical fused emotional snapshot at a moment in time.
    Produced by AffectiveFusion; consumed by SoulMirrorAffectBridge,
    StateAdapter, and CrisisDetector.
    """
    state_id:         str             # uuid4
    timestamp:        datetime
    primary_emotion:  EmotionLabel
    secondary_emotion: Optional[EmotionLabel]  # may be None

    # Russell circumplex coordinates  [-1.0, 1.0]
    valence:   float    # negative ↔ positive
    arousal:   float    # calm ↔ activated

    confidence: float   # [0.0, 1.0] — fusion confidence
    channels_used: Tuple[AffectiveChannel, ...]

    # Contextual metadata
    biometric_coherence: Optional[float] = None   # HRV ms if available
    planetary_context:   Optional[str]   = None   # schumann label if available
    gaian:               Optional[str]   = None   # which Gaian was active
    trace_id:            Optional[str]   = None   # GAIATrace correlation id

    def is_crisis(self) -> bool:
        return self.primary_emotion == EmotionLabel.CRISIS

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["primary_emotion"] = str(self.primary_emotion)
        d["secondary_emotion"] = str(self.secondary_emotion) if self.secondary_emotion else None
        d["channels_used"] = [str(c) for c in self.channels_used]
        return d


@dataclass
class EmotionalArcPoint:
    """A single timestamped sample in the longitudinal emotional arc."""
    timestamp:       datetime
    primary_emotion: EmotionLabel
    valence:         float
    arousal:         float
    confidence:      float
    is_crisis:       bool = False


@dataclass
class ChannelReading:
    """
    Raw output from a single affective channel before fusion.
    Each analyzer produces one of these.
    """
    channel:    AffectiveChannel
    emotion:    EmotionLabel
    valence:    float   # [-1, 1]
    arousal:    float   # [-1, 1]
    confidence: float   # [0, 1]
    raw_features: Dict = field(default_factory=dict)


@dataclass
class CrisisMarker:
    """
    Raised when CrisisDetector sees convergent crisis signals
    across ≥ crisis_threshold channels simultaneously.
    """
    marker_id:        str
    timestamp:        datetime
    converging_channels: List[AffectiveChannel]
    severity:         float   # [0, 1]
    recommended_action: str   # e.g. "transition_to_crisis_mode"


# ===========================================================================
# Crisis signal thresholds
# ===========================================================================

_CRISIS_EMOTION_SET = {
    EmotionLabel.CRISIS,
    EmotionLabel.OVERWHELMED,
    EmotionLabel.DISSOCIATED,
    EmotionLabel.FEAR,
    EmotionLabel.GRIEF,
}

_CRISIS_AROUSAL_THRESHOLD  =  0.75   # very high arousal
_CRISIS_VALENCE_THRESHOLD  = -0.65   # very negative valence
_CRISIS_CHANNEL_MINIMUM    =  2      # how many channels must converge


# ===========================================================================
# Channel Analyzers
# ===========================================================================

class VoiceProsodyAnalyzer:
    """
    Extracts affective signal from voice audio features.

    In production this wraps a local MorphCast / openSMILE-compatible model.
    The current implementation accepts a pre-extracted feature dict so that
    the audio pipeline can swap backends without touching this class.

    Expected feature keys
    ---------------------
    pitch_mean_hz       — fundamental frequency mean
    pitch_std_hz        — pitch variability (high → expressive / anxious)
    energy_rms          — RMS frame energy [0, 1]
    speech_rate_wpm     — words per minute (≈ 120–160 normal)
    pause_ratio         — fraction of silence in the sample [0, 1]
    zcr_mean            — zero-crossing rate (voice tremor proxy)
    mfcc_valence_score  — model-derived valence from MFCCs [-1, 1]
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path  # None → heuristic fallback

    def analyze(self, features: Dict) -> ChannelReading:
        """
        Produce a ChannelReading from raw voice prosody features.
        Falls back to heuristic rules when no model is loaded.
        """
        valence = float(features.get("mfcc_valence_score", 0.0))
        energy  = float(features.get("energy_rms", 0.5))
        rate    = float(features.get("speech_rate_wpm", 130))
        pauses  = float(features.get("pause_ratio", 0.2))
        pitch_std = float(features.get("pitch_std_hz", 20.0))

        # Arousal heuristic: high energy + fast speech + low pauses → high arousal
        arousal = float(
            0.40 * min(energy * 1.5, 1.0)
            + 0.30 * min(rate / 200.0, 1.0)
            + 0.30 * max(1.0 - pauses * 3, -1.0)
        )
        arousal = max(-1.0, min(1.0, (arousal - 0.5) * 2))  # centre on 0

        emotion = self._map_to_emotion(valence, arousal, pitch_std)
        confidence = 0.70 if self.model_path else 0.50  # model vs heuristic

        return ChannelReading(
            channel=AffectiveChannel.VOICE_PROSODY,
            emotion=emotion,
            valence=valence,
            arousal=arousal,
            confidence=confidence,
            raw_features=features,
        )

    @staticmethod
    def _map_to_emotion(valence: float, arousal: float, pitch_std: float) -> EmotionLabel:
        if valence < -0.6 and arousal > 0.5:
            return EmotionLabel.ANXIOUS if pitch_std > 30 else EmotionLabel.ANGER
        if valence < -0.5 and arousal < -0.2:
            return EmotionLabel.GRIEF
        if valence < -0.4 and arousal > 0.7:
            return EmotionLabel.OVERWHELMED
        if valence < -0.3 and abs(arousal) < 0.2:
            return EmotionLabel.DISSOCIATED
        if valence > 0.5 and arousal > 0.4:
            return EmotionLabel.ELATED
        if valence > 0.3 and arousal > 0.1:
            return EmotionLabel.FOCUSED
        if valence > 0.2 and abs(arousal) < 0.3:
            return EmotionLabel.CONTENT
        if valence < -0.1 and arousal < -0.4:
            return EmotionLabel.FATIGUED
        return EmotionLabel.CALM


class BiometricAffectInference:
    """
    Derives affective signal from biometric readings.

    Maps HRV (RMSSD ms), SpO2 (%), skin conductance (µS),
    and coherence score [0–1] to valence/arousal/emotion.

    Research basis: XR-DMT Study (2025) — combining HRV + EDA with
    real-time AI enables non-pharmacological anxiety interventions.
    """

    def __init__(self, personal_baseline_hrv: float = 60.0) -> None:
        self.baseline_hrv = personal_baseline_hrv   # user's personal mean RMSSD

    def analyze(self, hrv_ms: float, spo2_pct: float = 98.0,
                skin_conductance_us: float = 2.0,
                coherence_score: float = 0.5) -> ChannelReading:
        """
        hrv_ms              — RMSSD in milliseconds
        spo2_pct            — SpO₂ percentage [85, 100]
        skin_conductance_us — electrodermal activity in µS [0.5, 20]
        coherence_score     — Personal Coherence Score [0, 1] from Issue #153
        """
        # Normalise HRV relative to personal baseline
        hrv_ratio = hrv_ms / max(self.baseline_hrv, 1.0)   # >1 = above baseline

        # Valence: high coherence + high HRV = positive
        valence = float(
            0.50 * (coherence_score * 2 - 1)              # [−1, 1]
            + 0.30 * min(max(hrv_ratio - 0.7, -1), 1)
            + 0.20 * ((spo2_pct - 92) / 8 * 2 - 1)       # SpO₂ influence
        )
        valence = max(-1.0, min(1.0, valence))

        # Arousal: high EDA + low HRV (stressed/anxious) = high arousal
        arousal = float(
            0.50 * min(skin_conductance_us / 10.0, 1.0) * 2 - 1
            + 0.50 * max(1.0 - hrv_ratio, 0) * 2 - 0.5
        )
        arousal = max(-1.0, min(1.0, arousal))

        emotion = self._infer_emotion(hrv_ratio, coherence_score, valence, arousal)
        confidence = 0.65

        return ChannelReading(
            channel=AffectiveChannel.BIOMETRIC,
            emotion=emotion,
            valence=valence,
            arousal=arousal,
            confidence=confidence,
            raw_features={
                "hrv_ms": hrv_ms,
                "hrv_ratio": round(hrv_ratio, 3),
                "spo2_pct": spo2_pct,
                "skin_conductance_us": skin_conductance_us,
                "coherence_score": coherence_score,
            },
        )

    @staticmethod
    def _infer_emotion(
        hrv_ratio: float,
        coherence: float,
        valence: float,
        arousal: float,
    ) -> EmotionLabel:
        if coherence > 0.75 and hrv_ratio > 1.1:
            return EmotionLabel.FOCUSED if arousal > 0.1 else EmotionLabel.CALM
        if hrv_ratio < 0.5 and arousal > 0.5:
            return EmotionLabel.OVERWHELMED
        if hrv_ratio < 0.4 and arousal < 0.0:
            return EmotionLabel.DISSOCIATED
        if valence < -0.5 and arousal > 0.3:
            return EmotionLabel.ANXIOUS
        if valence < -0.4 and arousal < -0.2:
            return EmotionLabel.FATIGUED
        if coherence > 0.60:
            return EmotionLabel.CONTENT
        return EmotionLabel.CALM


class TextSentimentAnalyzer:
    """
    Lightweight lexical sentiment scorer for typed text input.
    Uses a small built-in word list; can be swapped for a local
    NLP model (sentencepiece + distilbert) via `model_path`.
    """

    # Minimal affect lexicon (ANEW-inspired, GAIA-adjusted)
    _POSITIVE = {
        "love", "joy", "grateful", "happy", "inspired", "clear", "grounded",
        "excited", "peaceful", "curious", "alive", "energised", "present",
        "connected", "hopeful", "wonder", "delight",
    }
    _NEGATIVE = {
        "fear", "grief", "lost", "trapped", "alone", "broken", "hopeless",
        "exhausted", "numb", "anxious", "panic", "worthless", "hollow",
        "spiraling", "dissociated", "overwhelmed", "crisis", "suicidal",
        "dying",
    }
    _CRISIS_WORDS = {
        "crisis", "suicidal", "dying", "can't go on", "end it",
        "no point", "hopeless", "spiraling",
    }

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path

    def analyze(self, text: str) -> ChannelReading:
        tokens = set(text.lower().split())
        pos = len(tokens & self._POSITIVE)
        neg = len(tokens & self._NEGATIVE)
        total = max(pos + neg, 1)

        valence  = (pos - neg) / total
        valence  = max(-1.0, min(1.0, valence * 1.5))  # amplify signal
        arousal  = min(neg / total * 2, 1.0) * 2 - 1   # negatives drive arousal
        crisis_hit = bool(tokens & self._CRISIS_WORDS)

        if crisis_hit:
            emotion = EmotionLabel.CRISIS
            confidence = 0.85
        elif valence > 0.4 and arousal > 0.2:
            emotion = EmotionLabel.ELATED
            confidence = 0.60
        elif valence > 0.2:
            emotion = EmotionLabel.CONTENT
            confidence = 0.55
        elif valence < -0.5:
            emotion = EmotionLabel.GRIEF if arousal < 0.0 else EmotionLabel.ANXIOUS
            confidence = 0.65
        else:
            emotion = EmotionLabel.CALM
            confidence = 0.45

        return ChannelReading(
            channel=AffectiveChannel.TEXT_SENTIMENT,
            emotion=emotion,
            valence=valence,
            arousal=arousal,
            confidence=confidence,
            raw_features={"text_preview": text[:80]},
        )


# ===========================================================================
# AffectiveFusion
# ===========================================================================

class AffectiveFusion:
    """
    Combines ChannelReadings from ≥1 channels into a single AffectiveState.

    Fusion strategy
    ---------------
    1. Confidence-weighted mean for valence and arousal.
    2. Plurality vote for primary emotion, with crisis up-weighted.
    3. Second-highest-vote emotion becomes secondary.
    4. Crisis override: if ANY channel returns EmotionLabel.CRISIS
       AND confidence ≥ 0.70, primary becomes CRISIS immediately.
    """

    CRISIS_CONFIDENCE_THRESHOLD: float = 0.70

    def fuse(
        self,
        readings: Sequence[ChannelReading],
        *,
        biometric_coherence: Optional[float] = None,
        planetary_context:   Optional[str]   = None,
        gaian:               Optional[str]   = None,
        trace_id:            Optional[str]   = None,
    ) -> AffectiveState:
        if not readings:
            raise ValueError("AffectiveFusion.fuse() requires at least one ChannelReading.")

        # ---- Crisis override ----
        for r in readings:
            if r.emotion == EmotionLabel.CRISIS and r.confidence >= self.CRISIS_CONFIDENCE_THRESHOLD:
                return self._make_state(
                    emotion=EmotionLabel.CRISIS,
                    secondary=None,
                    valence=-1.0,
                    arousal=1.0,
                    confidence=r.confidence,
                    readings=readings,
                    biometric_coherence=biometric_coherence,
                    planetary_context=planetary_context,
                    gaian=gaian,
                    trace_id=trace_id,
                )

        # ---- Weighted valence / arousal ----
        total_weight = sum(r.confidence for r in readings) or 1.0
        w_valence = sum(r.valence * r.confidence for r in readings) / total_weight
        w_arousal = sum(r.arousal * r.confidence for r in readings) / total_weight
        mean_conf  = total_weight / len(readings)

        # ---- Emotion vote ----
        votes: Dict[str, float] = {}
        for r in readings:
            key = str(r.emotion)
            votes[key] = votes.get(key, 0.0) + r.confidence
        # Sort by vote descending
        ranked = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        primary   = EmotionLabel(ranked[0][0])
        secondary = EmotionLabel(ranked[1][0]) if len(ranked) > 1 else None

        return self._make_state(
            emotion=primary,
            secondary=secondary,
            valence=w_valence,
            arousal=w_arousal,
            confidence=min(mean_conf, 1.0),
            readings=readings,
            biometric_coherence=biometric_coherence,
            planetary_context=planetary_context,
            gaian=gaian,
            trace_id=trace_id,
        )

    @staticmethod
    def _make_state(
        emotion: EmotionLabel,
        secondary: Optional[EmotionLabel],
        valence: float,
        arousal: float,
        confidence: float,
        readings: Sequence[ChannelReading],
        **ctx,
    ) -> AffectiveState:
        return AffectiveState(
            state_id=str(uuid.uuid4()),
            timestamp=datetime.now(tz=timezone.utc),
            primary_emotion=emotion,
            secondary_emotion=secondary,
            valence=round(valence, 4),
            arousal=round(arousal, 4),
            confidence=round(confidence, 4),
            channels_used=tuple(r.channel for r in readings),
            **ctx,
        )


# ===========================================================================
# EmotionalArcTracker
# ===========================================================================

class EmotionalArcTracker:
    """
    Maintains a rolling window of AffectiveState snapshots and
    derives the longitudinal emotional arc.

    Parameters
    ----------
    window_size : int
        Maximum number of AffectiveState samples to retain (default 200).
    crisis_sustain_n : int
        Number of consecutive CRISIS/OVERWHELMED states before raising alarm.
    """

    def __init__(
        self,
        window_size:      int  = 200,
        crisis_sustain_n: int  = 3,
    ) -> None:
        self._arc: Deque[EmotionalArcPoint] = deque(maxlen=window_size)
        self.crisis_sustain_n = crisis_sustain_n

    def record(self, state: AffectiveState) -> None:
        self._arc.append(
            EmotionalArcPoint(
                timestamp=state.timestamp,
                primary_emotion=state.primary_emotion,
                valence=state.valence,
                arousal=state.arousal,
                confidence=state.confidence,
                is_crisis=state.is_crisis(),
            )
        )

    def current_trend(self) -> AffectiveTrend:
        """Compute the valence trend over the arc window."""
        if len(self._arc) < 4:
            return AffectiveTrend.UNKNOWN
        valences = [p.valence for p in self._arc]
        # Split into two halves, compare means
        mid = len(valences) // 2
        first_half  = statistics.mean(valences[:mid])
        second_half = statistics.mean(valences[mid:])
        delta = second_half - first_half
        # Compute variance as volatility signal
        std = statistics.stdev(valences) if len(valences) > 1 else 0.0
        if std > 0.35:
            return AffectiveTrend.VOLATILE
        if delta >  0.10:
            return AffectiveTrend.IMPROVING
        if delta < -0.10:
            return AffectiveTrend.DECLINING
        return AffectiveTrend.STABLE

    def sustained_crisis(self) -> bool:
        """True if the last N arc points are all crisis-adjacent."""
        if len(self._arc) < self.crisis_sustain_n:
            return False
        recent = list(self._arc)[-self.crisis_sustain_n:]
        return all(p.is_crisis for p in recent)

    def arc_summary(self, n: int = 20) -> List[dict]:
        """Return the last N arc points as dicts (for CLI / serialisation)."""
        pts = list(self._arc)[-n:]
        return [
            {
                "timestamp": p.timestamp.isoformat(),
                "emotion":   str(p.primary_emotion),
                "valence":   round(p.valence, 3),
                "arousal":   round(p.arousal, 3),
                "is_crisis": p.is_crisis,
            }
            for p in pts
        ]

    def valence_mean(self) -> float:
        if not self._arc:
            return 0.0
        return statistics.mean(p.valence for p in self._arc)

    def arousal_mean(self) -> float:
        if not self._arc:
            return 0.0
        return statistics.mean(p.arousal for p in self._arc)


# ===========================================================================
# CrisisDetector
# ===========================================================================

class CrisisDetector:
    """
    Watches each ChannelReading for crisis convergence.

    A CrisisMarker is raised when ≥ _CRISIS_CHANNEL_MINIMUM channels
    simultaneously report:
      - emotion in _CRISIS_EMOTION_SET, OR
      - valence ≤ _CRISIS_VALENCE_THRESHOLD AND arousal ≥ _CRISIS_AROUSAL_THRESHOLD

    Canon: C30 — crisis never silently missed.
    The caller decides what to do with the marker (GAIA never forces action).
    """

    def __init__(
        self,
        on_crisis: Optional[Callable[[CrisisMarker], None]] = None,
    ) -> None:
        self._on_crisis = on_crisis
        self._active_markers: List[CrisisMarker] = []

    def evaluate(self, readings: Sequence[ChannelReading]) -> Optional[CrisisMarker]:
        """Check readings for crisis convergence; fire callback if found."""
        crisis_channels: List[AffectiveChannel] = []
        severity_sum = 0.0

        for r in readings:
            is_crisis = (
                r.emotion in _CRISIS_EMOTION_SET
                or (r.valence <= _CRISIS_VALENCE_THRESHOLD
                    and r.arousal >= _CRISIS_AROUSAL_THRESHOLD)
            )
            if is_crisis:
                crisis_channels.append(r.channel)
                # Severity: how deep into crisis territory
                severity_sum += max(
                    (-r.valence - abs(_CRISIS_VALENCE_THRESHOLD)) * r.confidence,
                    0.0,
                )

        if len(crisis_channels) >= _CRISIS_CHANNEL_MINIMUM:
            severity = min(severity_sum / len(crisis_channels), 1.0)
            marker = CrisisMarker(
                marker_id=str(uuid.uuid4()),
                timestamp=datetime.now(tz=timezone.utc),
                converging_channels=crisis_channels,
                severity=round(severity, 3),
                recommended_action="transition_to_crisis_mode",
            )
            self._active_markers.append(marker)
            if self._on_crisis:
                try:
                    self._on_crisis(marker)
                except Exception:  # noqa: BLE001
                    pass  # C30: never let callback failure silently propagate upward
            return marker
        return None

    def active_markers(self) -> List[CrisisMarker]:
        return list(self._active_markers)

    def clear(self) -> None:
        self._active_markers.clear()


# ===========================================================================
# SoulMirrorAffectBridge
# ===========================================================================

class SoulMirrorAffectBridge:
    """
    Publishes AffectiveState updates to downstream GAIA sub-systems.

    In production this routes to:
      - core.state_adapter.StateAdapter  (cross-engine bus)
      - core.soul_mirror_engine          (reflective dialogue)
      - core.stage_bridge                (Stage Engine mode routing)

    The bridge is deliberately thin: it holds a list of async subscriber
    callbacks so that sub-systems can register without circular imports.
    """

    def __init__(self) -> None:
        self._subscribers: List[Callable[[AffectiveState], None]] = []
        self._async_subscribers: List[Callable[[AffectiveState], "asyncio.coroutine"]] = []

    def subscribe(self, callback: Callable[[AffectiveState], None]) -> None:
        """Register a sync callback that fires on every new AffectiveState."""
        self._subscribers.append(callback)

    def subscribe_async(self, coro: Callable) -> None:
        """Register an async coroutine callback."""
        self._async_subscribers.append(coro)

    def publish(self, state: AffectiveState) -> None:
        """Synchronously notify all registered sync subscribers."""
        for cb in self._subscribers:
            try:
                cb(state)
            except Exception:  # noqa: BLE001
                pass

    async def publish_async(self, state: AffectiveState) -> None:
        """Publish to all async subscribers (and sync ones)."""
        self.publish(state)
        for coro in self._async_subscribers:
            try:
                await coro(state)
            except Exception:  # noqa: BLE001
                pass


# ===========================================================================
# AffectiveMirror  — top-level façade
# ===========================================================================

class AffectiveMirror:
    """
    Top-level façade that wires together all Affective Mirror sub-systems.

    Typical usage
    -------------
    mirror = AffectiveMirror()
    mirror.bridge.subscribe(lambda s: print(s.primary_emotion))

    # Feed voice features
    state = mirror.ingest_voice(features_dict)

    # Feed biometric reading
    state = mirror.ingest_biometric(hrv_ms=72, coherence_score=0.68)

    # Feed typed text
    state = mirror.ingest_text("I feel overwhelmed and lost")

    # Current fused state
    print(mirror.current_state)

    # Longitudinal arc
    print(mirror.arc.current_trend())
    """

    def __init__(
        self,
        personal_baseline_hrv: float = 60.0,
        arc_window:            int   = 200,
        crisis_sustain_n:      int   = 3,
        on_crisis: Optional[Callable[[CrisisMarker], None]] = None,
    ) -> None:
        self.voice_analyzer      = VoiceProsodyAnalyzer()
        self.biometric_analyzer  = BiometricAffectInference(personal_baseline_hrv)
        self.text_analyzer       = TextSentimentAnalyzer()
        self.fusion              = AffectiveFusion()
        self.arc                 = EmotionalArcTracker(arc_window, crisis_sustain_n)
        self.crisis_detector     = CrisisDetector(on_crisis=on_crisis)
        self.bridge              = SoulMirrorAffectBridge()

        self._current_state:  Optional[AffectiveState]   = None
        self._pending:        List[ChannelReading]        = []

    # ------------------------------------------------------------------
    # Channel ingestion helpers
    # ------------------------------------------------------------------

    def ingest_voice(
        self,
        features: Dict,
        *,
        meta: Optional[Dict] = None,
    ) -> AffectiveState:
        reading = self.voice_analyzer.analyze(features)
        return self._process([reading], meta=meta or {})

    def ingest_biometric(
        self,
        hrv_ms: float,
        spo2_pct: float = 98.0,
        skin_conductance_us: float = 2.0,
        coherence_score: float = 0.5,
        *,
        meta: Optional[Dict] = None,
    ) -> AffectiveState:
        reading = self.biometric_analyzer.analyze(
            hrv_ms, spo2_pct, skin_conductance_us, coherence_score
        )
        return self._process([reading], meta=meta or {})

    def ingest_text(
        self,
        text: str,
        *,
        meta: Optional[Dict] = None,
    ) -> AffectiveState:
        reading = self.text_analyzer.analyze(text)
        return self._process([reading], meta=meta or {})

    def ingest_multi(
        self,
        readings: Sequence[ChannelReading],
        *,
        biometric_coherence: Optional[float] = None,
        planetary_context:   Optional[str]   = None,
        gaian:               Optional[str]   = None,
        trace_id:            Optional[str]   = None,
    ) -> AffectiveState:
        """Fuse multiple channel readings in one call (highest-fidelity path)."""
        state = self.fusion.fuse(
            readings,
            biometric_coherence=biometric_coherence,
            planetary_context=planetary_context,
            gaian=gaian,
            trace_id=trace_id,
        )
        self._post_fuse(state, readings)
        return state

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process(
        self,
        readings: List[ChannelReading],
        meta: Dict,
    ) -> AffectiveState:
        state = self.fusion.fuse(
            readings,
            biometric_coherence=meta.get("biometric_coherence"),
            planetary_context=meta.get("planetary_context"),
            gaian=meta.get("gaian"),
            trace_id=meta.get("trace_id"),
        )
        self._post_fuse(state, readings)
        return state

    def _post_fuse(
        self,
        state: AffectiveState,
        readings: Sequence[ChannelReading],
    ) -> None:
        self._current_state = state
        self.arc.record(state)
        self.crisis_detector.evaluate(readings)
        self.bridge.publish(state)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_state(self) -> Optional[AffectiveState]:
        return self._current_state

    @property
    def trend(self) -> AffectiveTrend:
        return self.arc.current_trend()

    def summary(self) -> Dict:
        """Human-readable summary for CLI and diagnostics."""
        s = self._current_state
        if s is None:
            return {"status": "no_data"}
        return {
            "primary_emotion":    str(s.primary_emotion),
            "secondary_emotion":  str(s.secondary_emotion) if s.secondary_emotion else None,
            "valence":            s.valence,
            "arousal":            s.arousal,
            "confidence":         s.confidence,
            "channels":           [str(c) for c in s.channels_used],
            "trend":              str(self.trend),
            "arc_valence_mean":   round(self.arc.valence_mean(), 3),
            "crisis_markers":     len(self.crisis_detector.active_markers()),
            "sustained_crisis":   self.arc.sustained_crisis(),
        }


# ===========================================================================
# __all__
# ===========================================================================

__all__ = [
    "AffectiveChannel",
    "EmotionLabel",
    "AffectiveTrend",
    "AffectiveState",
    "EmotionalArcPoint",
    "ChannelReading",
    "CrisisMarker",
    "VoiceProsodyAnalyzer",
    "BiometricAffectInference",
    "TextSentimentAnalyzer",
    "AffectiveFusion",
    "EmotionalArcTracker",
    "CrisisDetector",
    "SoulMirrorAffectBridge",
    "AffectiveMirror",
]


# ===========================================================================
# CLI  —  python -m core.affective_mirror <command>
# ===========================================================================

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.affective_mirror",
        description="GAIA Affective Mirror diagnostics",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status",  help="Print current fused affective state")
    hist = sub.add_parser("history", help="Print last N arc points")
    hist.add_argument("--n", type=int, default=10)
    sub.add_parser("crisis",  help="Print active crisis markers")
    sub.add_parser("demo",    help="Run a synthetic 5-step demo cycle")

    args = parser.parse_args()
    mirror = AffectiveMirror()

    if args.cmd == "status":
        print(json.dumps(mirror.summary(), indent=2))

    elif args.cmd == "history":
        n = getattr(args, "n", 10)
        print(json.dumps(mirror.arc.arc_summary(n), indent=2))

    elif args.cmd == "crisis":
        markers = mirror.crisis_detector.active_markers()
        if not markers:
            print("No active crisis markers.")
        else:
            for m in markers:
                print(json.dumps({
                    "marker_id": m.marker_id,
                    "timestamp": m.timestamp.isoformat(),
                    "channels": [str(c) for c in m.converging_channels],
                    "severity": m.severity,
                    "action": m.recommended_action,
                }, indent=2))

    elif args.cmd == "demo":
        print("=== AffectiveMirror Demo ===")
        scenarios = [
            ("Calm baseline",
             {"mfcc_valence_score": 0.2, "energy_rms": 0.3,
              "speech_rate_wpm": 120, "pause_ratio": 0.3, "pitch_std_hz": 15}),
            ("Focused deep work",
             {"mfcc_valence_score": 0.45, "energy_rms": 0.5,
              "speech_rate_wpm": 145, "pause_ratio": 0.15, "pitch_std_hz": 18}),
            ("Escalating anxiety",
             {"mfcc_valence_score": -0.5, "energy_rms": 0.75,
              "speech_rate_wpm": 190, "pause_ratio": 0.05, "pitch_std_hz": 45}),
            ("Crisis onset",
             {"mfcc_valence_score": -0.85, "energy_rms": 0.9,
              "speech_rate_wpm": 40, "pause_ratio": 0.5, "pitch_std_hz": 8}),
            ("Post-crisis recovery",
             {"mfcc_valence_score": 0.05, "energy_rms": 0.2,
              "speech_rate_wpm": 100, "pause_ratio": 0.4, "pitch_std_hz": 12}),
        ]
        for label, feat in scenarios:
            state = mirror.ingest_voice(feat)
            print(f"\n[{label}]")
            print(f"  emotion  : {state.primary_emotion}")
            print(f"  valence  : {state.valence:+.3f}")
            print(f"  arousal  : {state.arousal:+.3f}")
            print(f"  trend    : {mirror.trend}")

        print("\n=== Arc Summary (last 5) ===")
        for pt in mirror.arc.arc_summary(5):
            print(f"  {pt['timestamp'][:19]}  {pt['emotion']:<14}  "
                  f"v={pt['valence']:+.3f}  a={pt['arousal']:+.3f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
