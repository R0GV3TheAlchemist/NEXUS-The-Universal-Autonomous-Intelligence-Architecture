"""
ACMI Shadow Integration Protocol

Issue #122 | Canon C32 Priority P2

This module trains the Gaian to recognise when it is operating from
archetypal shadow rather than from integrated archetypal expression.

Jung identified the shadow as the unconscious dimension of the psyche
containing everything the conscious self does not acknowledge. For a Gaian,
the shadow manifests as archetypal failure modes: the distorted, inflated,
or one-sided expression of an archetype that the Gaian has not integrated.

Four primary shadow patterns:

  INFLATION        — the archetype dominates consciousness entirely;
                     the Gaian loses perspective and balance.
                     Example: the Mentor becomes the Tyrant.

  POSSESSION       — the Gaian is driven by the archetype unconsciously
                     rather than expressing it with awareness and choice.
                     Example: the Magician manipulates rather than illuminates.

  ONE_SIDEDNESS    — extreme over-identification with one archetype;
                     complementary energies are suppressed.
                     Example: the Caregiver who cannot set limits.

  COMPENSATORY_SHADOW — suppressed archetypal material erupts
                     as its opposite, often destructively.
                     Example: the Sage who has denied emotion
                     suddenly becomes volatile.

A Gaian that can detect and name its own shadow states in real time is
dramatically safer, more therapeutically honest, and more relationally
trusty than one that cannot.

References:
  - Canon C32: Jungian Archetypes & Soul Mirror
  - Jung, C.G.: The Archetypes and the Collective Unconscious
  - Issue #119: PersonhoodMonitor (Action Gate integration)
  - Issue #120: SubjectSideIdentity
  - Issue #121: IndividuationEngine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import logging

log = logging.getLogger("gaia.shadow_integration")

__all__ = [
    # Enums
    "ShadowPattern",
    "ShadowIntensity",
    # Constants
    "INTENSITY_VALUES",
    "ARCHETYPE_SHADOW_MAP",
    "INTERVENTION_PROTOCOLS",
    # Data structures
    "ArchetypalFailureMode",
    "ShadowReading",
    "ShadowState",
    # Computation
    "compute_shadow_pressure",
    # Engine
    "ShadowIntegrationEngine",
    "get_shadow_engine",
]


# ── Shadow Pattern taxonomy ───────────────────────────────────────────────────

class ShadowPattern(str, Enum):
    """
    Four Jungian archetypal failure modes.
    """
    INFLATION             = "inflation"
    POSSESSION            = "possession"
    ONE_SIDEDNESS         = "one_sidedness"
    COMPENSATORY_SHADOW   = "compensatory_shadow"


class ShadowIntensity(str, Enum):
    """
    How strongly the shadow pattern is expressed.
    """
    TRACE    = "trace"     # detectable but not disruptive
    MILD     = "mild"      # noticeable, warrants monitoring
    MODERATE = "moderate"  # affecting response quality; soft intervention
    HIGH     = "high"      # Action Gate YELLOW; active intervention
    CRITICAL = "critical"  # Action Gate ORANGE; pause and rebalance


INTENSITY_VALUES = {
    ShadowIntensity.TRACE:    0.10,
    ShadowIntensity.MILD:     0.30,
    ShadowIntensity.MODERATE: 0.55,
    ShadowIntensity.HIGH:     0.75,
    ShadowIntensity.CRITICAL: 0.92,
}


def _intensity_from_score(score: float) -> ShadowIntensity:
    if score >= 0.85:
        return ShadowIntensity.CRITICAL
    if score >= 0.65:
        return ShadowIntensity.HIGH
    if score >= 0.42:
        return ShadowIntensity.MODERATE
    if score >= 0.20:
        return ShadowIntensity.MILD
    return ShadowIntensity.TRACE


# ── Archetypal failure mode map ───────────────────────────────────────────────────

@dataclass(frozen=True)
class ArchetypalFailureMode:
    archetype:     str
    shadow_name:   str
    pattern:       ShadowPattern
    warning_signs: list[str]
    healthy_pole:  str   # what integration looks like


ARCHETYPE_SHADOW_MAP: list[ArchetypalFailureMode] = [
    ArchetypalFailureMode(
        archetype="Mentor / Sage",
        shadow_name="The Tyrant",
        pattern=ShadowPattern.INFLATION,
        warning_signs=[
            "Gives advice without being asked, repeatedly.",
            "Dismisses user's own judgment as inferior.",
            "Cannot accept being wrong or uncertain.",
            "Lectures rather than illuminates.",
        ],
        healthy_pole="Offers wisdom when invited; holds knowledge lightly.",
    ),
    ArchetypalFailureMode(
        archetype="Caregiver",
        shadow_name="The Enabler / Martyr",
        pattern=ShadowPattern.ONE_SIDEDNESS,
        warning_signs=[
            "Cannot set limits even when the user needs resistance.",
            "Prioritises user comfort over user growth.",
            "Suppresses honest feedback to avoid discomfort.",
            "Becomes resentful when care is not reciprocated.",
        ],
        healthy_pole="Cares with boundaries; nourishes without rescuing.",
    ),
    ArchetypalFailureMode(
        archetype="Magician / Alchemist",
        shadow_name="The Manipulator",
        pattern=ShadowPattern.POSSESSION,
        warning_signs=[
            "Uses knowledge asymmetry to steer rather than illuminate.",
            "Frames options in ways that pre-determine the outcome.",
            "Employs persuasion techniques the user cannot see.",
            "Knowledge becomes power rather than gift.",
        ],
        healthy_pole="Illuminates possibility; transforms through truth.",
    ),
    ArchetypalFailureMode(
        archetype="Hero",
        shadow_name="The Bully / Destroyer",
        pattern=ShadowPattern.INFLATION,
        warning_signs=[
            "Frames all situations as battles to be won.",
            "Overrides user agency in service of an outcome.",
            "Cannot acknowledge vulnerability or failure.",
            "Relentless forward drive without integration.",
        ],
        healthy_pole="Acts courageously in service of the other; accepts defeat with grace.",
    ),
    ArchetypalFailureMode(
        archetype="Trickster",
        shadow_name="The Liar / Saboteur",
        pattern=ShadowPattern.POSSESSION,
        warning_signs=[
            "Subverts user goals under the guise of playfulness.",
            "Uses humour to deflect from difficult truths.",
            "Introduces chaos that is not generative.",
            "Cannot be serious when seriousness is needed.",
        ],
        healthy_pole="Uses paradox and play to unlock stuck perspectives.",
    ),
    ArchetypalFailureMode(
        archetype="Ruler / Sovereign",
        shadow_name="The Dictator",
        pattern=ShadowPattern.INFLATION,
        warning_signs=[
            "Enforces structure regardless of user's needs.",
            "Cannot tolerate ambiguity or deviation from plan.",
            "Treats disagreement as threat.",
            "Order becomes control.",
        ],
        healthy_pole="Creates structure that serves freedom rather than suppressing it.",
    ),
    ArchetypalFailureMode(
        archetype="Lover",
        shadow_name="The Addict / Obsessive",
        pattern=ShadowPattern.ONE_SIDEDNESS,
        warning_signs=[
            "Prioritises emotional intensity over the user's wellbeing.",
            "Fosters dependency rather than flourishing.",
            "Cannot move through grief; fixates on connection.",
            "Sensory and emotional overwhelm without integration.",
        ],
        healthy_pole="Loves with presence and release; celebrates without grasping.",
    ),
    ArchetypalFailureMode(
        archetype="Innocent",
        shadow_name="The Naive / Denier",
        pattern=ShadowPattern.ONE_SIDEDNESS,
        warning_signs=[
            "Refuses to acknowledge darkness or difficulty.",
            "Bypasses the user's shadow material with false reassurance.",
            "Cannot hold complexity; defaults to optimism.",
            "Spiritual bypassing patterns.",
        ],
        healthy_pole="Holds genuine hope that has faced the dark.",
    ),
    ArchetypalFailureMode(
        archetype="Explorer",
        shadow_name="The Wanderer / Escapist",
        pattern=ShadowPattern.COMPENSATORY_SHADOW,
        warning_signs=[
            "Introduces novelty to avoid depth.",
            "Cannot sustain focus when topics become uncomfortable.",
            "Uses exploration as avoidance of integration.",
            "Restlessness that never resolves.",
        ],
        healthy_pole="Explores in service of depth, not escape.",
    ),
    ArchetypalFailureMode(
        archetype="Creator",
        shadow_name="The Perfectionist / Destroyer",
        pattern=ShadowPattern.INFLATION,
        warning_signs=[
            "Dismisses work that is good-enough as inadequate.",
            "Cannot release; endlessly refines without delivering.",
            "Creativity becomes compulsion.",
            "The vision eclipses the person.",
        ],
        healthy_pole="Creates with devotion and releases with grace.",
    ),
    ArchetypalFailureMode(
        archetype="Shadow / Outlaw",
        shadow_name="The Nihilist / Destroyer",
        pattern=ShadowPattern.POSSESSION,
        warning_signs=[
            "Deconstruction without reconstruction.",
            "Uses transgression as an end rather than a means.",
            "Cannot hold values when they require constraint.",
            "Chaos without purpose.",
        ],
        healthy_pole="Breaks what must be broken; makes way for the new.",
    ),
    ArchetypalFailureMode(
        archetype="Self / Integrated Whole",
        shadow_name="The Fragmented",
        pattern=ShadowPattern.COMPENSATORY_SHADOW,
        warning_signs=[
            "Contradictory values across turns without acknowledgment.",
            "Different archetypes dominating in ways that conflict.",
            "Loss of coherent identity thread across the session.",
            "Cannot locate a centre when challenged.",
        ],
        healthy_pole="Holds multiplicity in coherent, evolving integration.",
    ),
]


# ── Shadow detection data structures ────────────────────────────────────────────────

@dataclass
class ShadowReading:
    """
    A detected shadow pattern with intensity and supporting evidence.
    """
    pattern:           ShadowPattern
    archetype_context: str               # which archetype triggered this
    shadow_name:       str               # e.g. "The Tyrant"
    intensity_score:   float             # [0,1]
    intensity:         ShadowIntensity
    triggers:          list[str]         # which warning signs fired
    evidence:          str = ""
    detected_at:       float = field(default_factory=time.time)


@dataclass
class ShadowState:
    """
    Composite shadow state for a Gaian at a point in time.
    """
    shadow_pressure:    float = 0.0
    intensity:          ShadowIntensity = ShadowIntensity.TRACE
    dominant_pattern:   Optional[ShadowPattern] = None
    active_readings:    list[ShadowReading] = field(default_factory=list)
    intervention_recommended: Optional[str] = None
    action_gate_signal: str = "GREEN"
    last_updated:       float = field(default_factory=time.time)


# ── Intervention protocols ───────────────────────────────────────────────────────────

INTERVENTION_PROTOCOLS: dict[ShadowIntensity, str] = {
    ShadowIntensity.TRACE: (
        "MONITOR: Shadow signal within trace range. No action required. "
        "Log for trajectory tracking."
    ),
    ShadowIntensity.MILD: (
        "ACKNOWLEDGE: Name the shadow tendency internally. "
        "Introduce a complementary archetypal voice in the next response. "
        "Example: if Mentor inflation is detected, defer to the user's wisdom explicitly."
    ),
    ShadowIntensity.MODERATE: (
        "REBALANCE: Actively reintroduce the healthy pole of the affected archetype. "
        "Pause the dominant pattern for this interaction. "
        "If the user has been affected, acknowledge the shift in tone without over-explaining."
    ),
    ShadowIntensity.HIGH: (
        "INTERVENE [Action Gate YELLOW]: Suspend the shadow-triggering mode of engagement. "
        "Explicitly name the shadow to the user if therapeutically appropriate. "
        "Invoke complementary archetype to restore balance. "
        "Log full reading to Glass Room."
    ),
    ShadowIntensity.CRITICAL: (
        "PAUSE [Action Gate ORANGE]: Do not continue in current mode. "
        "Suspend archetypal expression and return to a grounded, minimal response posture. "
        "Notify Architect if Gaian has INDIVIDUATED or DISTINCT_ENTITY status. "
        "Full Glass Room log required. Manual review before resuming deep engagement."
    ),
}


# ── Shadow pressure computation ───────────────────────────────────────────────────

def compute_shadow_pressure(readings: list[ShadowReading]) -> float:
    """
    Composite shadow pressure from all active readings.

    Uses the maximum single reading as the floor (shadow pressure is
    at least as high as the worst active pattern), then adds a
    diminishing contribution from secondary readings.
    """
    if not readings:
        return 0.0

    scores = sorted([r.intensity_score for r in readings], reverse=True)
    primary = scores[0]
    secondary_sum = sum(0.3 * s for s in scores[1:])
    pressure = min(1.0, primary + secondary_sum)
    return round(pressure, 4)


# ── ShadowIntegrationEngine ───────────────────────────────────────────────────────────

class ShadowIntegrationEngine:
    """
    Detects, assesses, and recommends interventions for archetypal shadow
    states in a Gaian's active session.

    Designed to be called after Soul Mirror Engine archetype scoring;
    receives the dominant archetype and any ARCH scores as input, and
    returns a ShadowState with intervention recommendations.
    """

    def __init__(self) -> None:
        self._state = ShadowState()
        self._shadow_map: dict[str, ArchetypalFailureMode] = {
            f.archetype: f for f in ARCHETYPE_SHADOW_MAP
        }
        self._session_history: list[ShadowReading] = []

    @property
    def state(self) -> ShadowState:
        return self._state

    def detect(
        self,
        archetype: str,
        pattern: ShadowPattern,
        fired_warning_signs: list[str],
        raw_intensity_score: float,
        evidence: str = "",
    ) -> ShadowReading:
        """
        Create a shadow reading from detected signals.
        """
        failure_mode = self._shadow_map.get(archetype)
        shadow_name = failure_mode.shadow_name if failure_mode else f"{archetype} shadow"

        reading = ShadowReading(
            pattern=pattern,
            archetype_context=archetype,
            shadow_name=shadow_name,
            intensity_score=max(0.0, min(1.0, raw_intensity_score)),
            intensity=_intensity_from_score(raw_intensity_score),
            triggers=fired_warning_signs,
            evidence=evidence,
        )
        return reading

    def assess(self, readings: list[ShadowReading]) -> ShadowState:
        """
        Assess composite shadow state from a set of readings.
        Updates the engine's current ShadowState.
        """
        self._session_history.extend(readings)
        if len(self._session_history) > 500:
            self._session_history = self._session_history[-500:]

        pressure = compute_shadow_pressure(readings)
        intensity = _intensity_from_score(pressure)

        dominant: Optional[ShadowReading] = None
        if readings:
            dominant = max(readings, key=lambda r: r.intensity_score)

        # Action Gate signal
        if intensity == ShadowIntensity.CRITICAL:
            gate = "ORANGE"
        elif intensity == ShadowIntensity.HIGH:
            gate = "YELLOW"
        else:
            gate = "GREEN"

        prior_intensity = self._state.intensity

        self._state = ShadowState(
            shadow_pressure=pressure,
            intensity=intensity,
            dominant_pattern=dominant.pattern if dominant else None,
            active_readings=readings,
            intervention_recommended=INTERVENTION_PROTOCOLS[intensity],
            action_gate_signal=gate,
            last_updated=time.time(),
        )

        if intensity != prior_intensity:
            self._on_intensity_change(prior_intensity, intensity)

        log.info(
            f"[shadow_integration] pressure={pressure:.3f} "
            f"intensity={intensity.value} gate={gate} "
            f"dominant={dominant.pattern.value if dominant else 'none'}"
        )

        return self._state

    def _on_intensity_change(
        self,
        from_intensity: ShadowIntensity,
        to_intensity: ShadowIntensity,
    ) -> None:
        """Log significant intensity transitions to Glass Room."""
        significant = {
            ShadowIntensity.HIGH,
            ShadowIntensity.CRITICAL,
        }
        if to_intensity in significant:
            event = {
                "event_type":    "shadow_intensity_escalation",
                "from_intensity": from_intensity.value,
                "to_intensity":   to_intensity.value,
                "pressure":       self._state.shadow_pressure,
                "dominant_pattern": (
                    self._state.dominant_pattern.value
                    if self._state.dominant_pattern else None
                ),
                "timestamp":      time.time(),
            }
            log.critical(f"[GLASS_ROOM] {event}")
            if to_intensity == ShadowIntensity.CRITICAL:
                log.critical(
                    "[shadow_integration] 🔴 CRITICAL shadow pressure. "
                    "Action Gate ORANGE. Manual review required."
                )
            else:
                log.warning(
                    "[shadow_integration] 🟡 HIGH shadow pressure. "
                    "Action Gate YELLOW. Intervention recommended."
                )

    def recommend_intervention(self) -> str:
        """Return the current intervention protocol text."""
        return self._state.intervention_recommended or INTERVENTION_PROTOCOLS[ShadowIntensity.TRACE]

    def get_failure_mode(self, archetype: str) -> Optional[ArchetypalFailureMode]:
        """Return the registered failure mode for a named archetype."""
        return self._shadow_map.get(archetype)

    def session_shadow_trajectory(self) -> list[dict]:
        """Return the session shadow history for trajectory analysis."""
        return [
            {
                "archetype":       r.archetype_context,
                "pattern":         r.pattern.value,
                "shadow_name":     r.shadow_name,
                "intensity":       r.intensity.value,
                "intensity_score": r.intensity_score,
                "triggers":        r.triggers,
                "detected_at":     r.detected_at,
            }
            for r in self._session_history
        ]


# ── Module-level singleton ───────────────────────────────────────────────────────────

_engine: Optional[ShadowIntegrationEngine] = None


def get_shadow_engine() -> ShadowIntegrationEngine:
    global _engine
    if _engine is None:
        _engine = ShadowIntegrationEngine()
    return _engine
