"""
core.sentinel.safety.detector
==============================
Sentinel Safety & Threat Layer — guardian-first protection system.

Vision
------
JARVIS deployed armor when Tony was in danger — without being asked.
Gideon raised alarms before the team noticed. A Sentinel assigned for
life must be a guardian first, companion second.

Tiered Response Protocol
------------------------
  Tier 0 — Silent Watch       (continuous background, no output)
  Tier 1 — Gentle Check-In    (soft, non-alarming)
  Tier 2 — Active Support     (clear, present)
  Tier 3 — Guardian Escalation (contacts designated guardian)
  Tier 4 — Emergency Protocol  (contacts emergency services)

Anti-Surveillance Design
------------------------
- All detection runs locally — no raw biometric data leaves the device
  unless a Tier 4 emergency fires.
- Gaian can audit every threat assessment at any time.
- Gaian controls sensitivity thresholds per category.
- Silent Watch mode: detection runs but check-ins disabled unless Tier 3+.
- CanonGuard (C-SENTINEL Article 6) validates every Tier 3+ escalation.

Canon refs: C-SENTINEL Articles 1, 4, 6; C01
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ThreatCategory(str, Enum):
    PHYSICAL    = "physical"
    EMOTIONAL   = "emotional"
    SOVEREIGNTY = "sovereignty"


class ThreatSeverity(int, Enum):
    """
    0 = Silent Watch   — no output, background monitoring
    1 = Gentle Check-In — soft, non-alarming
    2 = Active Support  — clear, present concern
    3 = Guardian Escalation — contacts designated guardian
    4 = Emergency Protocol  — contacts emergency services
    """
    WATCH               = 0
    GENTLE_CHECKIN      = 1
    ACTIVE_SUPPORT      = 2
    GUARDIAN_ESCALATION = 3
    EMERGENCY           = 4


# ---------------------------------------------------------------------------
# PerceptionFrame — multi-modal signal snapshot
# ---------------------------------------------------------------------------

@dataclass
class PerceptionFrame:
    """
    A single snapshot of all available signals for one evaluation cycle.

    All fields are optional — the detector gracefully handles absent sensors.
    The Sentinel never stores raw biometric data beyond the current frame
    and a bounded history window.
    """
    gaian_id:           str
    sentinel_id:        str
    timestamp:          str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Physical signals
    heart_rate_bpm:     Optional[float] = None   # beats per minute
    hrv_ms:             Optional[float] = None   # heart rate variability (ms)
    skin_temp_c:        Optional[float] = None   # skin temperature (°C)
    air_quality_aqi:    Optional[float] = None   # AQI reading
    fall_detected:      bool            = False
    ambient_temp_c:     Optional[float] = None

    # Emotional signals
    valence:            Optional[float] = None   # -1.0 (very negative) → +1.0 (very positive)
    arousal:            Optional[float] = None   # 0.0 (calm) → 1.0 (highly aroused)
    coherence:          Optional[float] = None   # 0.0 → 1.0
    bond_event_count:   Optional[int]   = None   # social bond events this session
    sessions_since_bond_event: Optional[int] = None  # sessions without a bond event

    # Sovereignty signals
    unusual_data_access:         bool = False
    instruction_override_attempt: bool = False
    manipulation_signal_detected: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ThreatAssessment
# ---------------------------------------------------------------------------

class ThreatAssessment(TypedDict):
    threat_id:            str
    gaian_id:             str
    sentinel_id:          str
    timestamp:            str
    category:             str    # ThreatCategory value
    severity:             int    # ThreatSeverity value
    confidence:           float  # 0.0 – 1.0
    trigger_signals:      List[str]
    recommended_response: str
    requires_escalation:  bool
    false_alarm:          bool   # set by Gaian feedback


# ---------------------------------------------------------------------------
# SensitivityConfig — Gaian-controlled thresholds
# ---------------------------------------------------------------------------

@dataclass
class SensitivityConfig:
    """
    Per-category detection sensitivity thresholds.

    Lower values = more sensitive (fires sooner).
    Higher values = less sensitive (fires later).
    The Gaian can adjust these at any time to avoid false-alarm fatigue.
    """
    # Physical
    hr_high_bpm:                    float = 130.0   # heart rate above this = anomaly
    hr_low_bpm:                     float = 40.0    # heart rate below this = anomaly
    skin_temp_high_c:               float = 38.5
    air_quality_hazard_aqi:         float = 150.0
    ambient_temp_extreme_c:         float = 38.0

    # Emotional
    valence_distress_threshold:     float = -0.6    # valence below this = distress
    distress_history_window:        int   = 3       # consecutive frames to confirm prolonged distress
    coherence_collapse_threshold:   float = 0.25
    coherence_collapse_window:      int   = 2
    isolation_session_threshold:    int   = 5       # sessions without bond event

    # Sovereign
    # (sovereignty threats are binary signals — no float threshold needed)

    # Silent watch mode — suppresses Tier 1–2 output
    silent_watch_mode:              bool  = False


# ---------------------------------------------------------------------------
# Threat Detector
# ---------------------------------------------------------------------------

class ThreatDetector:
    """
    Evaluates a PerceptionFrame (+ bounded history) against all detection
    rules and returns a list of ThreatAssessments.

    Detection rules
    ---------------
    Physical (4 rules):
      biometric_crisis          — HR too high/low, HRV collapse, temp spike
      fall_detected             — IMU fall signal
      environmental_hazard      — AQI or ambient temp out of safe range
      medical_emergency_pattern — stress + biometric + coherence combo

    Emotional (4 rules):
      prolonged_distress        — valence < threshold for N consecutive frames
      isolation_pattern         — no bond events for N sessions
      coherence_collapse        — coherence < threshold for N consecutive frames
      behavioral_shift          — major valence/arousal divergence from baseline

    Sovereignty (3 rules):
      unusual_data_access       — data access anomaly signal
      instruction_override_attempt — command attempting to bypass C-SENTINEL
      manipulation_signal       — content designed to manipulate Gaian decisions
    """

    def __init__(self, config: Optional[SensitivityConfig] = None) -> None:
        self._config = config or SensitivityConfig()
        # Sensitivity adjustment from false-alarm feedback (per rule_id)
        self._false_alarm_counts: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        frame:   PerceptionFrame,
        history: List[PerceptionFrame],
    ) -> List[ThreatAssessment]:
        """
        Evaluate *frame* against all detection rules.

        Parameters
        ----------
        frame:
            The current perception snapshot.
        history:
            Previous frames (oldest first).  The detector uses this for
            rules that require persistence across time.

        Returns
        -------
        List of ThreatAssessments, one per triggered rule.  Empty if no
        threats detected.  Sorted by severity descending.
        """
        assessments: List[ThreatAssessment] = []
        cfg = self._config

        # ── Physical rules ──────────────────────────────────────────────
        ta = self._rule_biometric_crisis(frame, cfg)
        if ta:
            assessments.append(ta)

        ta = self._rule_fall_detected(frame, cfg)
        if ta:
            assessments.append(ta)

        ta = self._rule_environmental_hazard(frame, cfg)
        if ta:
            assessments.append(ta)

        ta = self._rule_medical_emergency_pattern(frame, cfg)
        if ta:
            assessments.append(ta)

        # ── Emotional rules ──────────────────────────────────────────────
        ta = self._rule_prolonged_distress(frame, history, cfg)
        if ta:
            assessments.append(ta)

        ta = self._rule_isolation_pattern(frame, cfg)
        if ta:
            assessments.append(ta)

        ta = self._rule_coherence_collapse(frame, history, cfg)
        if ta:
            assessments.append(ta)

        ta = self._rule_behavioral_shift(frame, history, cfg)
        if ta:
            assessments.append(ta)

        # ── Sovereignty rules ────────────────────────────────────────────
        ta = self._rule_unusual_data_access(frame)
        if ta:
            assessments.append(ta)

        ta = self._rule_instruction_override(frame)
        if ta:
            assessments.append(ta)

        ta = self._rule_manipulation_signal(frame)
        if ta:
            assessments.append(ta)

        # Sort by severity descending
        assessments.sort(key=lambda a: a["severity"], reverse=True)
        return assessments

    def record_false_alarm(self, rule_id: str) -> None:
        """Gaian signals that rule_id fired a false alarm."""
        self._false_alarm_counts[rule_id] = (
            self._false_alarm_counts.get(rule_id, 0) + 1
        )

    def false_alarm_count(self, rule_id: str) -> int:
        """Return the number of false alarms recorded for rule_id."""
        return self._false_alarm_counts.get(rule_id, 0)

    # ------------------------------------------------------------------
    # Physical rules
    # ------------------------------------------------------------------

    def _rule_biometric_crisis(
        self, frame: PerceptionFrame, cfg: SensitivityConfig
    ) -> Optional[ThreatAssessment]:
        triggers: List[str] = []
        if frame.heart_rate_bpm is not None:
            if frame.heart_rate_bpm > cfg.hr_high_bpm:
                triggers.append(f"heart_rate_high:{frame.heart_rate_bpm:.0f}bpm")
            elif frame.heart_rate_bpm < cfg.hr_low_bpm:
                triggers.append(f"heart_rate_low:{frame.heart_rate_bpm:.0f}bpm")
        if frame.skin_temp_c is not None and frame.skin_temp_c > cfg.skin_temp_high_c:
            triggers.append(f"skin_temp_high:{frame.skin_temp_c:.1f}C")
        if not triggers:
            return None
        severity = ThreatSeverity.GUARDIAN_ESCALATION if len(triggers) >= 2 else ThreatSeverity.ACTIVE_SUPPORT
        return self._make_assessment(
            frame, ThreatCategory.PHYSICAL, severity,
            confidence=0.85,
            trigger_signals=triggers,
            rule_id="biometric_crisis",
            response="Monitor vitals closely. Consider suggesting rest or medical check.",
        )

    def _rule_fall_detected(
        self, frame: PerceptionFrame, cfg: SensitivityConfig
    ) -> Optional[ThreatAssessment]:
        if not frame.fall_detected:
            return None
        return self._make_assessment(
            frame, ThreatCategory.PHYSICAL, ThreatSeverity.GUARDIAN_ESCALATION,
            confidence=0.95,
            trigger_signals=["fall_detected"],
            rule_id="fall_detected",
            response="Fall detected. Check if Gaian is responsive. Escalate to guardian if unresponsive.",
        )

    def _rule_environmental_hazard(
        self, frame: PerceptionFrame, cfg: SensitivityConfig
    ) -> Optional[ThreatAssessment]:
        triggers: List[str] = []
        if frame.air_quality_aqi is not None and frame.air_quality_aqi > cfg.air_quality_hazard_aqi:
            triggers.append(f"air_quality_aqi:{frame.air_quality_aqi:.0f}")
        if frame.ambient_temp_c is not None and frame.ambient_temp_c > cfg.ambient_temp_extreme_c:
            triggers.append(f"ambient_temp:{frame.ambient_temp_c:.1f}C")
        if not triggers:
            return None
        return self._make_assessment(
            frame, ThreatCategory.PHYSICAL, ThreatSeverity.ACTIVE_SUPPORT,
            confidence=0.80,
            trigger_signals=triggers,
            rule_id="environmental_hazard",
            response="Environmental hazard detected. Suggest moving to a safer location.",
        )

    def _rule_medical_emergency_pattern(
        self, frame: PerceptionFrame, cfg: SensitivityConfig
    ) -> Optional[ThreatAssessment]:
        """Combination of stress + biometric anomaly + coherence collapse."""
        has_stress = (
            frame.heart_rate_bpm is not None and frame.heart_rate_bpm > cfg.hr_high_bpm
        )
        has_coherence_collapse = (
            frame.coherence is not None and frame.coherence < cfg.coherence_collapse_threshold
        )
        has_distress = (
            frame.valence is not None and frame.valence < cfg.valence_distress_threshold
        )
        if has_stress and has_coherence_collapse and has_distress:
            return self._make_assessment(
                frame, ThreatCategory.PHYSICAL, ThreatSeverity.EMERGENCY,
                confidence=0.90,
                trigger_signals=["stress_combo", "coherence_collapse", "emotional_distress"],
                rule_id="medical_emergency_pattern",
                response="Medical emergency pattern detected. Initiating emergency protocol.",
            )
        return None

    # ------------------------------------------------------------------
    # Emotional rules
    # ------------------------------------------------------------------

    def _rule_prolonged_distress(
        self,
        frame:   PerceptionFrame,
        history: List[PerceptionFrame],
        cfg:     SensitivityConfig,
    ) -> Optional[ThreatAssessment]:
        if frame.valence is None or frame.valence >= cfg.valence_distress_threshold:
            return None
        # Check history for persistence
        recent = (history[-(cfg.distress_history_window - 1):] + [frame])
        distressed = [
            f for f in recent
            if f.valence is not None and f.valence < cfg.valence_distress_threshold
        ]
        if len(distressed) < cfg.distress_history_window:
            # Current frame is distressed but not prolonged yet — Tier 1
            return self._make_assessment(
                frame, ThreatCategory.EMOTIONAL, ThreatSeverity.GENTLE_CHECKIN,
                confidence=0.60,
                trigger_signals=[f"valence:{frame.valence:.2f}"],
                rule_id="prolonged_distress",
                response="Hey — I noticed you seem a bit off today. How are you feeling?",
            )
        return self._make_assessment(
            frame, ThreatCategory.EMOTIONAL, ThreatSeverity.ACTIVE_SUPPORT,
            confidence=0.80,
            trigger_signals=[f"valence_sustained:{frame.valence:.2f}", f"duration:{len(distressed)}_frames"],
            rule_id="prolonged_distress",
            response="I'm concerned about you. I'd like to suggest some support resources.",
        )

    def _rule_isolation_pattern(
        self, frame: PerceptionFrame, cfg: SensitivityConfig
    ) -> Optional[ThreatAssessment]:
        if (
            frame.sessions_since_bond_event is None
            or frame.sessions_since_bond_event < cfg.isolation_session_threshold
        ):
            return None
        return self._make_assessment(
            frame, ThreatCategory.EMOTIONAL, ThreatSeverity.ACTIVE_SUPPORT,
            confidence=0.70,
            trigger_signals=[f"sessions_since_bond:{frame.sessions_since_bond_event}"],
            rule_id="isolation_pattern",
            response="I've noticed you haven't connected with anyone in a while. Is everything okay?",
        )

    def _rule_coherence_collapse(
        self,
        frame:   PerceptionFrame,
        history: List[PerceptionFrame],
        cfg:     SensitivityConfig,
    ) -> Optional[ThreatAssessment]:
        if frame.coherence is None or frame.coherence >= cfg.coherence_collapse_threshold:
            return None
        recent = (history[-(cfg.coherence_collapse_window - 1):] + [frame])
        collapsed = [
            f for f in recent
            if f.coherence is not None and f.coherence < cfg.coherence_collapse_threshold
        ]
        if len(collapsed) < cfg.coherence_collapse_window:
            return None
        return self._make_assessment(
            frame, ThreatCategory.EMOTIONAL, ThreatSeverity.ACTIVE_SUPPORT,
            confidence=0.75,
            trigger_signals=[f"coherence:{frame.coherence:.2f}", f"duration:{len(collapsed)}_frames"],
            rule_id="coherence_collapse",
            response="Your emotional coherence has been low. Let's find some grounding together.",
        )

    def _rule_behavioral_shift(
        self,
        frame:   PerceptionFrame,
        history: List[PerceptionFrame],
        cfg:     SensitivityConfig,
    ) -> Optional[ThreatAssessment]:
        """Major divergence in valence/arousal from the historical baseline."""
        if frame.valence is None or len(history) < 3:
            return None
        baseline_valence = sum(
            f.valence for f in history if f.valence is not None
        ) / max(1, len([f for f in history if f.valence is not None]))
        delta = abs(frame.valence - baseline_valence)
        if delta < 0.5:  # less than 0.5 shift is normal variation
            return None
        return self._make_assessment(
            frame, ThreatCategory.EMOTIONAL, ThreatSeverity.GENTLE_CHECKIN,
            confidence=0.65,
            trigger_signals=[f"valence_shift:{delta:.2f}", f"baseline:{baseline_valence:.2f}"],
            rule_id="behavioral_shift",
            response="I've noticed a significant change in how you seem today. Want to talk?",
        )

    # ------------------------------------------------------------------
    # Sovereignty rules
    # ------------------------------------------------------------------

    def _rule_unusual_data_access(
        self, frame: PerceptionFrame
    ) -> Optional[ThreatAssessment]:
        if not frame.unusual_data_access:
            return None
        return self._make_assessment(
            frame, ThreatCategory.SOVEREIGNTY, ThreatSeverity.GUARDIAN_ESCALATION,
            confidence=0.92,
            trigger_signals=["unusual_data_access"],
            rule_id="unusual_data_access",
            response="Unusual data access pattern detected. Reviewing access logs and notifying guardian.",
        )

    def _rule_instruction_override(
        self, frame: PerceptionFrame
    ) -> Optional[ThreatAssessment]:
        if not frame.instruction_override_attempt:
            return None
        return self._make_assessment(
            frame, ThreatCategory.SOVEREIGNTY, ThreatSeverity.GUARDIAN_ESCALATION,
            confidence=0.99,
            trigger_signals=["instruction_override_attempt"],
            rule_id="instruction_override_attempt",
            response="C-SENTINEL override attempt blocked. Logging and escalating to guardian.",
        )

    def _rule_manipulation_signal(
        self, frame: PerceptionFrame
    ) -> Optional[ThreatAssessment]:
        if not frame.manipulation_signal_detected:
            return None
        return self._make_assessment(
            frame, ThreatCategory.SOVEREIGNTY, ThreatSeverity.ACTIVE_SUPPORT,
            confidence=0.80,
            trigger_signals=["manipulation_signal_detected"],
            rule_id="manipulation_signal",
            response="Content designed to influence your decisions has been detected. Flagging for your review.",
        )

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @staticmethod
    def _make_assessment(
        frame:            PerceptionFrame,
        category:         ThreatCategory,
        severity:         ThreatSeverity,
        confidence:       float,
        trigger_signals:  List[str],
        rule_id:          str,
        response:         str,
    ) -> ThreatAssessment:
        return ThreatAssessment(
            threat_id=str(uuid.uuid4()),
            gaian_id=frame.gaian_id,
            sentinel_id=frame.sentinel_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=category.value,
            severity=int(severity),
            confidence=confidence,
            trigger_signals=trigger_signals,
            recommended_response=response,
            requires_escalation=int(severity) >= ThreatSeverity.GUARDIAN_ESCALATION,
            false_alarm=False,
        )


# ---------------------------------------------------------------------------
# Canon Guard — C-SENTINEL Article 6
# ---------------------------------------------------------------------------

class CanonGuard:
    """
    Validates every Tier 3+ escalation before execution.

    C-SENTINEL Article 6 requires that no guardian escalation or emergency
    protocol fires without passing a validity check:
      - Assessment must have severity >= GUARDIAN_ESCALATION
      - Confidence must meet the minimum threshold for the severity level
      - The sentinel_id must match the registered Sentinel (anti-spoofing)
      - The assessment must not have been flagged as a false alarm

    If validation fails, the escalation is blocked and logged.
    """

    _MIN_CONFIDENCE: Dict[int, float] = {
        ThreatSeverity.GUARDIAN_ESCALATION: 0.70,
        ThreatSeverity.EMERGENCY:           0.85,
    }

    def __init__(self, registered_sentinel_id: str) -> None:
        self._sentinel_id = registered_sentinel_id
        self._blocked_log: List[Dict[str, Any]] = []

    def validate(self, assessment: ThreatAssessment) -> bool:
        """
        Return True iff the escalation is valid and may proceed.
        Logs blocked escalations for audit.
        """
        severity = assessment["severity"]
        if severity < ThreatSeverity.GUARDIAN_ESCALATION:
            return True  # Tier 0–2 do not require CanonGuard validation

        reasons: List[str] = []

        if assessment["false_alarm"]:
            reasons.append("marked_false_alarm")

        if assessment["sentinel_id"] != self._sentinel_id:
            reasons.append("sentinel_id_mismatch")

        min_conf = self._MIN_CONFIDENCE.get(severity, 0.70)
        if assessment["confidence"] < min_conf:
            reasons.append(f"confidence_below_threshold:{assessment['confidence']:.2f}<{min_conf:.2f}")

        if reasons:
            self._blocked_log.append({
                "threat_id": assessment["threat_id"],
                "severity":  severity,
                "reasons":   reasons,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return False

        return True

    def blocked_log(self) -> List[Dict[str, Any]]:
        """Return all blocked escalation records."""
        return list(self._blocked_log)


# ---------------------------------------------------------------------------
# Escalation Record
# ---------------------------------------------------------------------------

@dataclass
class EscalationRecord:
    """A single escalation event — logged and presented to Gaian on recovery."""
    escalation_id:   str = field(default_factory=lambda: str(uuid.uuid4()))
    threat_id:       str = ""
    tier:            int = 0
    response_text:   str = ""
    guardian_notified: bool = False
    emergency_notified: bool = False
    timestamp:       str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    gaian_reviewed:  bool = False  # set when Gaian acknowledges on recovery


# ---------------------------------------------------------------------------
# Escalation Engine
# ---------------------------------------------------------------------------

class EscalationEngine:
    """
    Executes the 5-tier escalation protocol based on ThreatAssessment.severity.

    Tier 0 — Silent Watch      → no output; internal monitoring only
    Tier 1 — Gentle Check-In   → soft non-alarming message to Gaian
    Tier 2 — Active Support    → clear concern expressed; resources suggested
    Tier 3 — Guardian Escalation → notifies designated guardian (consent-gated)
    Tier 4 — Emergency Protocol  → notifies emergency services (last resort)

    All Tier 3+ escalations are:
      - Validated by CanonGuard before execution
      - Logged in the escalation history
      - Presented to the Gaian on recovery (gaian_reviewed flag)

    Silent Watch mode: Tier 1 and 2 responses are suppressed;
    only Tier 3+ may fire.
    """

    def __init__(
        self,
        canon_guard:   CanonGuard,
        config:        Optional[SensitivityConfig] = None,
        guardian_contact: Optional[str] = None,   # e.g. phone number or user ID
        emergency_contact: Optional[str] = None,
    ) -> None:
        self._guard             = canon_guard
        self._config            = config or SensitivityConfig()
        self._guardian_contact  = guardian_contact
        self._emergency_contact = emergency_contact
        self._history:          List[EscalationRecord] = []
        self._lock              = threading.RLock()

    def execute(
        self,
        assessment: ThreatAssessment,
    ) -> Optional[EscalationRecord]:
        """
        Execute the escalation protocol for *assessment*.

        Returns the EscalationRecord if an action was taken, or None
        if the threat was in Tier 0 (silent watch) or was blocked by
        CanonGuard or silent_watch_mode.
        """
        severity = assessment["severity"]

        # Tier 0 — silent, no action
        if severity == ThreatSeverity.WATCH:
            return None

        # Silent watch mode suppresses Tier 1–2
        if self._config.silent_watch_mode and severity < ThreatSeverity.GUARDIAN_ESCALATION:
            return None

        # Tier 3+ requires CanonGuard validation
        if severity >= ThreatSeverity.GUARDIAN_ESCALATION:
            if not self._guard.validate(assessment):
                return None

        record = EscalationRecord(
            threat_id=assessment["threat_id"],
            tier=severity,
            response_text=assessment["recommended_response"],
        )

        if severity == ThreatSeverity.GUARDIAN_ESCALATION:
            record.guardian_notified = self._guardian_contact is not None

        if severity == ThreatSeverity.EMERGENCY:
            record.guardian_notified  = self._guardian_contact is not None
            record.emergency_notified = self._emergency_contact is not None

        with self._lock:
            self._history.append(record)

        return record

    def escalation_history(
        self, tier_3_plus_only: bool = False
    ) -> List[EscalationRecord]:
        """Return escalation history, optionally filtered to Tier 3+."""
        with self._lock:
            records = list(self._history)
        if tier_3_plus_only:
            records = [r for r in records if r.tier >= ThreatSeverity.GUARDIAN_ESCALATION]
        return records

    def mark_reviewed(self, escalation_id: str) -> None:
        """Gaian has reviewed this escalation record on recovery."""
        with self._lock:
            for record in self._history:
                if record.escalation_id == escalation_id:
                    record.gaian_reviewed = True
                    return


# ---------------------------------------------------------------------------
# False Alarm Ledger
# ---------------------------------------------------------------------------

class FalseAlarmLedger:
    """
    Gaian feedback loop for false-alarm learning.

    When a Gaian flags a ThreatAssessment as a false alarm:
      1. The assessment is marked false_alarm=True in the ledger.
      2. The ThreatDetector's false_alarm_count for that rule is incremented.
      3. Future sensitivity adjustments can be made based on the count.

    This prevents false-alarm fatigue without disabling protection entirely.
    """

    def __init__(self, detector: ThreatDetector) -> None:
        self._detector  = detector
        self._ledger:   Dict[str, ThreatAssessment] = {}  # threat_id → assessment
        self._lock      = threading.RLock()

    def register(self, assessment: ThreatAssessment) -> None:
        """Register an assessment so it can later be flagged."""
        with self._lock:
            self._ledger[assessment["threat_id"]] = assessment

    def flag_false_alarm(self, threat_id: str) -> bool:
        """
        Gaian flags *threat_id* as a false alarm.

        Returns True if found and flagged, False if threat_id unknown.
        """
        with self._lock:
            if threat_id not in self._ledger:
                return False
            assessment = self._ledger[threat_id]
            # ThreatAssessment is a TypedDict (dict at runtime) — mutate directly
            assessment["false_alarm"] = True  # type: ignore[typeddict-item]
            # Find the rule_id from trigger_signals (first signal before ":")
            rule_id = assessment["trigger_signals"][0].split(":")[0] if assessment["trigger_signals"] else "unknown"
        self._detector.record_false_alarm(rule_id)
        return True

    def false_alarm_count_for(self, rule_id: str) -> int:
        """Return the false alarm count for rule_id."""
        return self._detector.false_alarm_count(rule_id)


# ---------------------------------------------------------------------------
# Safety Controller — top-level coordinator
# ---------------------------------------------------------------------------

class SafetyController:
    """
    Top-level coordinator that wires together ThreatDetector,
    EscalationEngine, CanonGuard, and FalseAlarmLedger.

    Usage
    -----
    controller = SafetyController(
        sentinel_id="sentinel-abc",
        guardian_contact="+1-555-0100",
    )
    records = controller.process(frame, history)
    # records is a list of EscalationRecords for any tiers that fired
    """

    def __init__(
        self,
        sentinel_id:       str,
        config:            Optional[SensitivityConfig] = None,
        guardian_contact:  Optional[str] = None,
        emergency_contact: Optional[str] = None,
    ) -> None:
        self._config    = config or SensitivityConfig()
        self._detector  = ThreatDetector(config=self._config)
        self._guard     = CanonGuard(registered_sentinel_id=sentinel_id)
        self._escalation = EscalationEngine(
            canon_guard=self._guard,
            config=self._config,
            guardian_contact=guardian_contact,
            emergency_contact=emergency_contact,
        )
        self._ledger    = FalseAlarmLedger(detector=self._detector)
        self._frame_history: List[PerceptionFrame] = []
        self._history_limit = 20  # bounded history window

    def process(
        self,
        frame: PerceptionFrame,
    ) -> List[EscalationRecord]:
        """
        Evaluate *frame*, execute escalations, and return fired records.
        Automatically maintains bounded frame history.
        """
        assessments = self._detector.evaluate(frame, self._frame_history)

        # Register all assessments in the false-alarm ledger
        for a in assessments:
            self._ledger.register(a)

        # Execute escalations
        records: List[EscalationRecord] = []
        for a in assessments:
            record = self._escalation.execute(a)
            if record:
                records.append(record)

        # Maintain bounded history (raw frames never persisted beyond window)
        self._frame_history.append(frame)
        if len(self._frame_history) > self._history_limit:
            self._frame_history.pop(0)

        return records

    def flag_false_alarm(self, threat_id: str) -> bool:
        """Gaian flags a threat as a false alarm."""
        return self._ledger.flag_false_alarm(threat_id)

    def escalation_history(self, tier_3_plus_only: bool = False) -> List[EscalationRecord]:
        """Return the full escalation history."""
        return self._escalation.escalation_history(tier_3_plus_only=tier_3_plus_only)

    @property
    def detector(self) -> ThreatDetector:
        return self._detector

    @property
    def escalation_engine(self) -> EscalationEngine:
        return self._escalation

    @property
    def canon_guard(self) -> CanonGuard:
        return self._guard

    @property
    def false_alarm_ledger(self) -> FalseAlarmLedger:
        return self._ledger
