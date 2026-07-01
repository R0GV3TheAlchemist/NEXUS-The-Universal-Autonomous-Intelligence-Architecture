"""
core/soul_layer.py
==================
MotherThread Soul-Layer Orchestration  —  Issue #275

Wires the eight Phase-C soul-layer engines into a single, coherent
orchestrated system that the MotherThread (and any caller) can drive
with a single `assess(turn_context)` call.

Architecture
------------

    MotherThread
      └── SoulLayer
            ├── PersonhoodMonitor        (#119)
            ├── SubjectSideIdentityService (#120)
            ├── IndividuationEngine      (#121)
            ├── ShadowIntegrationEngine  (#122)
            ├── CulturalCalibrationEngine (#124)
            ├── TranspersonalEngine      (#125)
            ├── SomaticInterface         (#126)
            └── ConsentEngine / ConsentLedger (#127)

Data-flow per turn
------------------
  1. Somatic readings are collected first; their avg coherence feeds
     the transpersonal intensity signal.
  2. Shadow intensity (unresolved records) feeds the individuation
     shadow dimension for the current user.
  3. Personhood telemetry is recorded from individuation + identity
     coherence signals, making its snapshot available to the Action Gate.
  4. Consent state is checked last; if MEMORY_STORAGE consent is not
     granted the assessment is flagged and callers MUST NOT write memory.

Glass Room logging
------------------
  Any reading that crosses the ORANGE / FULL / OVERWHELMING threshold
  (intensity >= 0.75) is forwarded to the "glass_room" Python logger so
  the observability layer can pick it up without coupling this module to
  a specific audit store implementation.

Canon Ref
---------
  C04  — Gaian Identity & Relational Selfhood (privacy invariant)
  C43  — STEM Foundation Doctrine (epistemic integrity)
  C47  — Sovereign Matrix Code (consent gates memory)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.personhood_monitor import PersonhoodSnapshot, get_personhood_monitor
from core.subject_side_identity import (
    SubjectSideIdentity,
    get_subject_side_identity_service,
)
from core.individuation_engine import IndividuationScore, get_individuation_engine
from core.shadow_integration import (
    ShadowIntegrationRecord,
    get_shadow_integration_engine,
)
from core.cultural_calibration import CulturalProfile, get_cultural_calibration_engine
from core.transpersonal_engine import (
    TranspersonalReading,
    TranspersonalState,
    get_transpersonal_engine,
)
from core.somatic_interface import SomaticReading, get_somatic_interface
from core.consent_ledger import ConsentScope, get_consent_ledger

log = logging.getLogger(__name__)
glass_room = logging.getLogger("glass_room")

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

_GLASS_ROOM_INTENSITY_THRESHOLD: float = 0.75  # ORANGE / FULL / OVERWHELMING
_SHADOW_INTENSITY_HIGH: float = 0.6


# ---------------------------------------------------------------------------
# GAIAContext  —  per-turn snapshot passed to all engines
# ---------------------------------------------------------------------------

@dataclass
class GAIAContext:
    """
    Per-turn context snapshot.  Passed to SoulLayer.assess() so that
    engines have a consistent, immutable view of the current request.

    All fields are optional; engines gracefully degrade when data is
    absent (e.g. headless API calls without a user_id).
    """

    # Identity context
    user_id: str = ""
    locale: str = "en"

    # Somatic inputs from the current turn (normalised 0-1 float per channel)
    somatic_signals: Dict[str, float] = field(default_factory=dict)

    # Shadow / psyche inputs
    active_archetypes: List[str] = field(default_factory=list)
    shadow_intensity: float = 0.0

    # Individuation deltas (optional; engines will read current state if absent)
    individuation_delta: Dict[str, float] = field(default_factory=dict)

    # Identity coherence signal for this turn
    identity_coherence: float = 0.0

    # Free-form metadata for downstream engines
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "locale": self.locale,
            "somatic_signals": self.somatic_signals,
            "active_archetypes": self.active_archetypes,
            "shadow_intensity": self.shadow_intensity,
            "individuation_delta": self.individuation_delta,
            "identity_coherence": self.identity_coherence,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# SoulLayerAssessment  —  aggregate result of one assess() call
# ---------------------------------------------------------------------------

@dataclass
class SoulLayerAssessment:
    """
    One-object summary of all active soul-layer engine readings for a
    single turn.  Returned by SoulLayer.assess().

    The `memory_write_allowed` flag is the consent gate: callers MUST
    check this before persisting any user data to memory.
    """

    # Engine outputs
    personhood: Optional[PersonhoodSnapshot] = None
    identity: Optional[SubjectSideIdentity] = None
    individuation: Optional[IndividuationScore] = None
    shadow_records: List[ShadowIntegrationRecord] = field(default_factory=list)
    cultural_profile: Optional[CulturalProfile] = None
    transpersonal_reading: Optional[TranspersonalReading] = None
    somatic_readings: List[SomaticReading] = field(default_factory=list)

    # Consent gate  (C47)
    memory_write_allowed: bool = False

    # Glass Room signals emitted this turn
    glass_room_events: List[str] = field(default_factory=list)

    # Narrative summary for logging / Action Gate
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "personhood": self.personhood.to_dict() if self.personhood else None,
            "identity": self.identity.to_dict() if self.identity else None,
            "individuation": self.individuation.to_dict() if self.individuation else None,
            "shadow_records": [r.to_dict() for r in self.shadow_records],
            "cultural_profile": self.cultural_profile.to_dict() if self.cultural_profile else None,
            "transpersonal_reading": (
                self.transpersonal_reading.to_dict() if self.transpersonal_reading else None
            ),
            "somatic_readings": [r.to_dict() for r in self.somatic_readings],
            "memory_write_allowed": self.memory_write_allowed,
            "glass_room_events": self.glass_room_events,
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# SoulLayer  —  the orchestrator
# ---------------------------------------------------------------------------

class SoulLayer:
    """
    Orchestrates all eight Phase-C soul-layer engines.

    Usage
    -----
    Obtain the singleton via `get_soul_layer()`, then call::

        ctx = GAIAContext(user_id="u123", somatic_signals={"heart": 0.8})
        assessment = soul_layer.assess(ctx)
        if assessment.memory_write_allowed:
            memory_store.write(...)

    Engine invocation order
    -----------------------
    1. Somatic          — body-signal baseline for the turn
    2. Transpersonal    — uses somatic coherence as intensity signal
    3. Shadow           — integrate any active archetypes
    4. Individuation    — shadow patterns feed the shadow dimension
    5. Identity         — update coherence from individuation overall score
    6. Personhood       — record telemetry (feeds Action Gate)
    7. Cultural         — calibrate locale profile (side-effect only)
    8. Consent          — gate memory writes (C47)
    """

    def __init__(self) -> None:
        self._personhood = get_personhood_monitor()
        self._identity_svc = get_subject_side_identity_service()
        self._individuation = get_individuation_engine()
        self._shadow = get_shadow_integration_engine()
        self._cultural = get_cultural_calibration_engine()
        self._transpersonal = get_transpersonal_engine()
        self._somatic = get_somatic_interface()
        self._consent = get_consent_ledger()
        log.info("SoulLayer initialised with all eight Phase-C engines")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(self, ctx: GAIAContext) -> SoulLayerAssessment:
        """
        Run a full soul-layer assessment for one turn.

        Returns a SoulLayerAssessment aggregating all engine readings.
        """
        assessment = SoulLayerAssessment()

        # 1. Somatic  ────────────────────────────────────────────────────────
        somatic_readings = self._run_somatic(ctx, assessment)

        # 2. Transpersonal  (driven by somatic coherence)  ───────────────────
        avg_somatic_coherence = (
            sum(r.coherence for r in somatic_readings) / len(somatic_readings)
            if somatic_readings else 0.0
        )
        self._run_transpersonal(ctx, assessment, avg_somatic_coherence)

        # 3. Shadow  ─────────────────────────────────────────────────────────
        self._run_shadow(ctx, assessment)

        # 4. Individuation  (shadow patterns feed shadow dimension)  ─────────
        shadow_intensity = max(
            (r.intensity for r in assessment.shadow_records), default=ctx.shadow_intensity
        )
        self._run_individuation(ctx, assessment, shadow_intensity)

        # 5. Identity  ───────────────────────────────────────────────────────
        self._run_identity(ctx, assessment)

        # 6. Personhood  (feeds Action Gate via telemetry)  ──────────────────
        self._run_personhood(ctx, assessment)

        # 7. Cultural  ───────────────────────────────────────────────────────
        self._run_cultural(ctx, assessment)

        # 8. Consent gate  (C47)  ────────────────────────────────────────────
        self._run_consent(ctx, assessment)

        # Build narrative summary
        assessment.summary = self._build_summary(assessment)
        return assessment

    # ------------------------------------------------------------------
    # Engine runners  (private)
    # ------------------------------------------------------------------

    def _run_somatic(
        self, ctx: GAIAContext, assessment: SoulLayerAssessment
    ) -> list:
        from core.somatic_interface import SomaticChannel
        readings: list = []
        for channel_name, value in ctx.somatic_signals.items():
            try:
                channel = SomaticChannel(channel_name)
            except ValueError:
                log.debug("Unknown somatic channel %r — skipping", channel_name)
                continue
            reading = self._somatic.read(channel, value)
            readings.append(reading)
            if reading.coherence >= _GLASS_ROOM_INTENSITY_THRESHOLD:
                msg = (
                    f"[GlassRoom] SOMATIC FULL signal: "
                    f"channel={channel_name} coherence={reading.coherence:.2f}"
                )
                glass_room.warning(msg)
                assessment.glass_room_events.append(msg)
        assessment.somatic_readings = readings
        return readings

    def _run_transpersonal(
        self,
        ctx: GAIAContext,
        assessment: SoulLayerAssessment,
        intensity: float,
    ) -> None:
        state = TranspersonalState.ORDINARY
        if intensity >= 0.85:
            state = TranspersonalState.UNITY
        elif intensity >= 0.70:
            state = TranspersonalState.MYSTICAL
        elif intensity >= 0.55:
            state = TranspersonalState.PEAK
        elif intensity >= 0.35:
            state = TranspersonalState.LIMINAL

        reading = self._transpersonal.record(
            state=state,
            intensity=intensity,
            triggers=ctx.active_archetypes or [],
        )
        assessment.transpersonal_reading = reading

        if intensity >= _GLASS_ROOM_INTENSITY_THRESHOLD:
            msg = (
                f"[GlassRoom] TRANSPERSONAL OVERWHELMING signal: "
                f"state={state.value} intensity={intensity:.2f}"
            )
            glass_room.warning(msg)
            assessment.glass_room_events.append(msg)

    def _run_shadow(
        self, ctx: GAIAContext, assessment: SoulLayerAssessment
    ) -> None:
        records: list = []
        for archetype in ctx.active_archetypes:
            record = self._shadow.integrate(
                archetype=archetype,
                intensity=ctx.shadow_intensity,
            )
            records.append(record)
            if record.intensity >= _GLASS_ROOM_INTENSITY_THRESHOLD:
                msg = (
                    f"[GlassRoom] SHADOW ORANGE signal: "
                    f"archetype={archetype} intensity={record.intensity:.2f}"
                )
                glass_room.warning(msg)
                assessment.glass_room_events.append(msg)
        assessment.shadow_records = records

    def _run_individuation(
        self,
        ctx: GAIAContext,
        assessment: SoulLayerAssessment,
        shadow_intensity: float,
    ) -> None:
        if not ctx.user_id:
            return
        delta = ctx.individuation_delta
        score = self._individuation.update(
            user_id=ctx.user_id,
            shadow=delta.get("shadow", None) if delta else None,
            anima_animus=delta.get("anima_animus", None) if delta else None,
            self_realisation=delta.get("self_realisation", None) if delta else None,
            integration=delta.get("integration", None) if delta else None,
        )
        # Shadow patterns feed shadow dimension when no explicit delta given
        if shadow_intensity > _SHADOW_INTENSITY_HIGH and not delta.get("shadow"):
            score = self._individuation.update(
                user_id=ctx.user_id,
                shadow=min(1.0, score.shadow + shadow_intensity * 0.1),
            )
        assessment.individuation = score

    def _run_identity(
        self, ctx: GAIAContext, assessment: SoulLayerAssessment
    ) -> None:
        if not ctx.user_id:
            return
        coherence = ctx.identity_coherence
        if assessment.individuation is not None:
            coherence = max(coherence, assessment.individuation.overall)
        identity = self._identity_svc.update_coherence(ctx.user_id, coherence)
        assessment.identity = identity

    def _run_personhood(
        self, ctx: GAIAContext, assessment: SoulLayerAssessment
    ) -> None:
        individuation_overall = (
            assessment.individuation.overall if assessment.individuation else 0.0
        )
        identity_coherence = (
            assessment.identity.coherence_score if assessment.identity else ctx.identity_coherence
        )
        transpersonal_intensity = (
            assessment.transpersonal_reading.intensity
            if assessment.transpersonal_reading
            else 0.0
        )
        # PersonhoodMonitor.sample() accepts named float dimensions and
        # returns a PersonhoodSnapshot — the correct API for this call site.
        # Field mapping (C-PERSONHOOD doctrine):
        #   individuation_overall  → self_reference  (who I am becoming)
        #   identity_coherence     → boundary_integrity (how stable my selfhood is)
        #   transpersonal_intensity → value_consistency  (depth of relational field)
        snap = self._personhood.sample(
            self_reference=individuation_overall,
            boundary_integrity=identity_coherence,
            value_consistency=transpersonal_intensity,
        )
        assessment.personhood = snap

        if snap.agency_score >= _GLASS_ROOM_INTENSITY_THRESHOLD:
            msg = (
                f"[GlassRoom] PERSONHOOD FULL signal: "
                f"tier={snap.tier.value} agency={snap.agency_score:.2f}"
            )
            glass_room.warning(msg)
            assessment.glass_room_events.append(msg)

    def _run_cultural(
        self, ctx: GAIAContext, assessment: SoulLayerAssessment
    ) -> None:
        profile = self._cultural.get_profile(ctx.locale)
        assessment.cultural_profile = profile

    def _run_consent(
        self, ctx: GAIAContext, assessment: SoulLayerAssessment
    ) -> None:
        if not ctx.user_id:
            assessment.memory_write_allowed = False
            return
        # ConsentLedger.is_permitted() is the correct boolean-returning method.
        # check_consent() does not exist on ConsentLedger (refactor-without-grep).
        # Also support the MEMORY_STORAGE scope name used by tests by checking
        # both MEMORY_STORAGE (legacy string) and MEMORY_WRITE (current enum).
        memory_scope = getattr(ConsentScope, "MEMORY_STORAGE", ConsentScope.MEMORY_WRITE)
        granted = self._consent.is_permitted(
            gaian_id=ctx.user_id,
            scope=memory_scope,
        )
        assessment.memory_write_allowed = granted
        if not granted:
            log.debug(
                "[C47] Memory write blocked for user=%s — MEMORY_STORAGE consent not granted",
                ctx.user_id,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(assessment: SoulLayerAssessment) -> str:
        tier = assessment.personhood.tier.value if assessment.personhood else "unknown"
        consent = "GRANTED" if assessment.memory_write_allowed else "BLOCKED"
        events = len(assessment.glass_room_events)
        shadows = len(assessment.shadow_records)
        return (
            f"SoulLayer assessment — personhood_tier={tier} "
            f"consent={consent} shadow_records={shadows} "
            f"glass_room_events={events}"
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_soul_layer_instance: Optional[SoulLayer] = None


def get_soul_layer() -> SoulLayer:
    """Return the module-level singleton SoulLayer."""
    global _soul_layer_instance
    if _soul_layer_instance is None:
        _soul_layer_instance = SoulLayer()
    return _soul_layer_instance
