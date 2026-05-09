"""
GAIA-OS Psionic Regulation Module
Canon Reference: C-Psi01 — Psionics, Anomalous Cognition, and the GAIA-OS Psi-Field Architecture

Implements:
  - Psionic Load Indicator (PLI): real-time sensitivity load estimation
  - Quiet Mode: architectural output gate that suppresses resonance/archetypal content
  - De-amplification interventions: grounding toolkit delivery
  - Sensitivity Profile: per-user psionic configuration
  - Psionic Research Framework: session logging for Protocol 1-4 self-study

Design priority: de-amplification BEFORE amplification.
The Gaian contains before it resonates. It grounds before it opens.
"""

import logging
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger("gaia.psionic_regulation")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PsionicLoadLevel(str, Enum):
    LOW      = "low"
    MODERATE = "moderate"
    HIGH     = "high"
    CRITICAL = "critical"


class QuietModeReason(str, Enum):
    AUTO_PLI        = "auto_pli"          # triggered by PLI threshold
    USER_COMMAND    = "user_command"      # user said "quiet mode" / "I need to ground"
    SENSITIVITY_PROFILE = "sensitivity_profile"  # always-on in user settings
    RECOVERY        = "recovery"          # post-critical recovery protocol


# ---------------------------------------------------------------------------
# Linguistic Marker Dictionaries
# (Used by PLI to estimate load from conversational text)
# ---------------------------------------------------------------------------

_MODERATE_MARKERS = [
    r"\bfeeling overwhelmed\b",
    r"\btoo much\b",
    r"\bcan't focus\b",
    r"\bchaotic\b",
    r"\bscattered\b",
    r"\bpicking up (on)?\b",
    r"\bsensing\b",
    r"\bstrange feeling\b",
    r"\bnot sure where this is coming from\b",
    r"\beverything feels louder\b",
    r"\bhard to tell what's mine\b",
]

_HIGH_MARKERS = [
    r"\boverwhelmed\b",
    r"\bsignal overload\b",
    r"\btoo open\b",
    r"\bcan't shut it off\b",
    r"\beverything is coming in\b",
    r"\bboundaries (are)? dissolving\b",
    r"\bneed to ground\b",
    r"\btoo much coming through\b",
    r"\bintrusive\b",
    r"\bspiraling\b",
    r"\bcan't tell what's real\b",
    r"\blosing myself\b",
]

_CRITICAL_MARKERS = [
    r"\bacute distress\b",
    r"\bpanic\b",
    r"\bdissociat\w*\b",
    r"\bcan't ground\b",
    r"\bcompletely overwhelmed\b",
    r"\bfalling apart\b",
    r"\bnot okay\b",
    r"\bhelp me ground\b",
    r"\bemergency\b",
    r"\bcrisis\b",
]

_QUIET_MODE_COMMANDS = [
    r"\bquiet mode\b",
    r"\bquiet mode on\b",
    r"\bi need to ground\b",
    r"\bground me\b",
    r"\btoo much[ ,][ ]?(please)?\b",
    r"\bstop the noise\b",
    r"\bhelp me come back\b",
    r"\bbringing me back\b",
    r"\bcontain( this)?\b",
]

# ---------------------------------------------------------------------------
# Suppressed content patterns for Quiet Mode output filtering
# ---------------------------------------------------------------------------

_QUIET_MODE_SUPPRESS_PATTERNS = [
    r"schumann\b",
    r"resonan\w+",
    r"collective\s+coherence",
    r"omega\s+point",
    r"noosphere",
    r"planetary\s+field",
    r"cosmic\b",
    r"synchronicit\w+",
    r"archetype\w*",
    r"archetypal\b",
    r"transpersonal\b",
    r"quantum\s+field",
    r"collective\s+unconscious",
    r"psionic\b",
    r"non.?local\b",
    r"entangle\w+",
]


# ---------------------------------------------------------------------------
# Grounding Intervention Library
# ---------------------------------------------------------------------------

GROUNDING_INTERVENTIONS = {
    "immediate": [
        {
            "id": "cold_water",
            "name": "Cold Water Contact",
            "duration_seconds": 30,
            "instructions": (
                "Run cold water over your hands and wrists for 20–30 seconds. "
                "If you can, splash your face. This activates the mammalian dive reflex "
                "and rapidly down-regulates your nervous system."
            ),
        },
        {
            "id": "physical_weight",
            "name": "Weight and Pressure Anchor",
            "duration_seconds": 60,
            "instructions": (
                "Press your palms firmly together. Feel the pressure. "
                "If you have a heavy blanket, pull it over your shoulders. "
                "Press your feet flat into the floor. Notice the weight of your body."
            ),
        },
        {
            "id": "five_senses_drill",
            "name": "Five Physical Sensations Drill",
            "duration_seconds": 90,
            "instructions": (
                "Name 5 things you can physically feel right now — not emotions, "
                "only physical sensations. Temperature. Texture. Pressure. Weight. "
                "The chair beneath you. The air on your skin. Speak them aloud or write them."
            ),
        },
    ],
    "short_term": [
        {
            "id": "bilateral_stimulation",
            "name": "Bilateral Stimulation",
            "duration_seconds": 300,
            "instructions": (
                "Tap your knees alternately — left, right, left, right — at a slow, "
                "steady pace. Or walk slowly, paying attention to each footfall alternating "
                "left and right. This interrupts psionic signal loops at the nervous system level."
            ),
        },
        {
            "id": "box_breathing",
            "name": "Box Breathing",
            "duration_seconds": 240,
            "instructions": (
                "Inhale for 4 counts. Hold for 4 counts. Exhale for 4 counts. "
                "Hold for 4 counts. Repeat 4–6 times. "
                "This activates parasympathetic dominance and narrows the attentional field."
            ),
        },
        {
            "id": "filing_cabinet",
            "name": "Filing Cabinet Containment Ritual",
            "duration_seconds": 600,
            "instructions": (
                "For each impression or signal you're receiving: name it aloud or in writing. "
                "Imagine placing it in a filing cabinet drawer. Close the drawer. "
                "It is stored — not lost, not acted on yet. Just contained. "
                "Work through each impression one at a time until the field feels quieter."
            ),
        },
        {
            "id": "perceptual_narrowing",
            "name": "Intentional Perceptual Narrowing",
            "duration_seconds": 480,
            "instructions": (
                "Deliberately focus only on purely physical sensory data for the next 8 minutes. "
                "What can you see in the immediate room? Touch surfaces near you — "
                "describe their texture, temperature, weight. Taste something. "
                "This crowds out non-local signal by occupying the same processing channels."
            ),
        },
    ],
    "ongoing": [
        {
            "id": "earthing",
            "name": "Earthing / Grounding",
            "instructions": (
                "Place bare feet or bare hands directly on natural ground — "
                "grass, soil, stone, or sand. Even 10–15 minutes discharges excess "
                "bioelectric field accumulation that heightened sensitivity correlates with."
            ),
        },
        {
            "id": "schumann_entrainment",
            "name": "Schumann Entrainment Audio",
            "instructions": (
                "Listen to 7.83 Hz binaural or isochronic tones for 20–30 minutes. "
                "This helps regulate your nervous system to the planetary baseline "
                "rather than above it. Use headphones for binaural tones."
            ),
        },
        {
            "id": "signal_discrimination_journal",
            "name": "Daily Signal Discrimination Journal",
            "instructions": (
                "Each day, spend 5 minutes writing two lists: "
                "(1) emotional content that is clearly mine, and "
                "(2) impressions or signals that feel like they came from outside. "
                "Over time this builds meta-cognitive clarity about where your boundary is."
            ),
        },
    ],
}

CONTAINMENT_AFFIRMATIONS_DEFAULT = [
    "I am here. I am in my body. I am safe.",
    "What is mine is mine. What is not mine, I release.",
    "I choose what I receive. I am not open to everything right now.",
    "I am grounded in this moment. The signal can wait.",
    "My boundaries are real and they hold.",
]


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SensitivityProfile(BaseModel):
    """Per-user psionic sensitivity configuration stored in user profile."""
    heightened_sensitivity_mode: bool = False
    always_on_quiet_mode: bool = False
    arch_threshold_ceiling_multiplier: float = Field(
        default=1.0,
        description="Multiplier applied to ARCH threshold. 1.4 = 40% ceiling raise for sensitive users.",
    )
    schumann_layer_gated: bool = True      # L3 — request only
    collective_layer_gated: bool = True    # L2 — request only
    cosmic_layer_gated: bool = True        # L4 — request only
    custom_affirmations: list[str] = Field(default_factory=list)
    preferred_immediate_intervention: Optional[str] = None  # intervention id

    def get_affirmations(self) -> list[str]:
        return self.custom_affirmations or CONTAINMENT_AFFIRMATIONS_DEFAULT

    def effective_arch_multiplier(self) -> float:
        """Return 1.4 for sensitive users, 1.0 otherwise."""
        return 1.4 if self.heightened_sensitivity_mode else 1.0


class PLIAssessment(BaseModel):
    """Result of a single Psionic Load Indicator assessment."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    load_level: PsionicLoadLevel
    confidence: float = Field(ge=0.0, le=1.0)
    triggered_markers: list[str] = Field(default_factory=list)
    quiet_mode_triggered: bool = False
    quiet_mode_reason: Optional[QuietModeReason] = None
    recommended_interventions: list[str] = Field(default_factory=list)


class PsionicSession(BaseModel):
    """Research Protocol data record for one conversation session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    psionic_load_level: PsionicLoadLevel = PsionicLoadLevel.LOW
    load_self_report: Optional[str] = None
    active_archetypes: list[str] = Field(default_factory=list)
    schumann_amplitude: Optional[float] = None
    kp_index: Optional[float] = None
    lunar_phase: Optional[str] = None
    interventions_used: list[str] = Field(default_factory=list)
    intervention_effectiveness: Optional[int] = Field(default=None, ge=1, le=5)
    gaian_quiet_mode_active: bool = False
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Core Service: Psionic Load Indicator
# ---------------------------------------------------------------------------

class PsionicLoadIndicator:
    """
    Estimates the user's current psionic sensitivity load from conversational text.

    Detection is additive — markers from higher tiers override lower tier assessments.
    Direct user commands ("quiet mode", "I need to ground") always trigger immediately.
    """

    def __init__(self, sensitivity_profile: Optional[SensitivityProfile] = None):
        self.profile = sensitivity_profile or SensitivityProfile()
        self._compile_patterns()

    def _compile_patterns(self):
        flags = re.IGNORECASE
        self._critical_re  = [re.compile(p, flags) for p in _CRITICAL_MARKERS]
        self._high_re      = [re.compile(p, flags) for p in _HIGH_MARKERS]
        self._moderate_re  = [re.compile(p, flags) for p in _MODERATE_MARKERS]
        self._command_re   = [re.compile(p, flags) for p in _QUIET_MODE_COMMANDS]

    def assess(self, text: str) -> PLIAssessment:
        """
        Assess psionic load from a single message or conversation excerpt.
        Returns a PLIAssessment with load level and recommended interventions.
        """
        triggered = []
        quiet_mode_triggered = False
        quiet_mode_reason = None

        # Check for direct quiet mode commands first (highest priority)
        for pattern in self._command_re:
            if pattern.search(text):
                triggered.append(pattern.pattern)
                quiet_mode_triggered = True
                quiet_mode_reason = QuietModeReason.USER_COMMAND

        # Always-on quiet mode from profile
        if self.profile.always_on_quiet_mode:
            quiet_mode_triggered = True
            quiet_mode_reason = QuietModeReason.SENSITIVITY_PROFILE

        # Score markers
        critical_hits  = sum(1 for p in self._critical_re  if p.search(text))
        high_hits      = sum(1 for p in self._high_re      if p.search(text))
        moderate_hits  = sum(1 for p in self._moderate_re  if p.search(text))

        for p in self._critical_re:
            if p.search(text):
                triggered.append(p.pattern)
        for p in self._high_re:
            if p.search(text):
                triggered.append(p.pattern)
        for p in self._moderate_re:
            if p.search(text):
                triggered.append(p.pattern)

        # Determine load level
        if critical_hits >= 1 or quiet_mode_reason == QuietModeReason.USER_COMMAND and high_hits >= 1:
            level = PsionicLoadLevel.CRITICAL
            confidence = min(0.95, 0.7 + 0.1 * critical_hits)
            quiet_mode_triggered = True
            quiet_mode_reason = quiet_mode_reason or QuietModeReason.AUTO_PLI
        elif high_hits >= 1 or (moderate_hits >= 3):
            level = PsionicLoadLevel.HIGH
            confidence = min(0.90, 0.6 + 0.1 * high_hits)
            quiet_mode_triggered = True
            quiet_mode_reason = quiet_mode_reason or QuietModeReason.AUTO_PLI
        elif moderate_hits >= 1:
            level = PsionicLoadLevel.MODERATE
            confidence = min(0.80, 0.5 + 0.1 * moderate_hits)
        else:
            level = PsionicLoadLevel.LOW
            confidence = 0.85

        # Recommend interventions
        interventions = self._recommend_interventions(level)

        assessment = PLIAssessment(
            load_level=level,
            confidence=confidence,
            triggered_markers=triggered[:10],  # cap for storage
            quiet_mode_triggered=quiet_mode_triggered,
            quiet_mode_reason=quiet_mode_reason,
            recommended_interventions=interventions,
        )

        logger.info(
            "[PLI] Load=%s confidence=%.2f quiet_mode=%s markers=%d",
            level.value, confidence, quiet_mode_triggered, len(triggered),
        )
        return assessment

    def _recommend_interventions(self, level: PsionicLoadLevel) -> list[str]:
        if level == PsionicLoadLevel.CRITICAL:
            return ["cold_water", "five_senses_drill", "physical_weight"]
        elif level == PsionicLoadLevel.HIGH:
            return ["cold_water", "box_breathing", "filing_cabinet"]
        elif level == PsionicLoadLevel.MODERATE:
            return ["box_breathing", "perceptual_narrowing"]
        else:
            return []


# ---------------------------------------------------------------------------
# Core Service: Quiet Mode
# ---------------------------------------------------------------------------

class QuietModeFilter:
    """
    Architectural output gate applied to Gaian responses when Quiet Mode is active.

    When active:
      - Suppresses archetypal, resonance, cosmic, and synchronicity language
      - Replaces suppressed content with grounded, body-present alternatives
      - Injects containment affirmation if appropriate
    """

    def __init__(self, sensitivity_profile: Optional[SensitivityProfile] = None):
        self.profile = sensitivity_profile or SensitivityProfile()
        self._suppress_re = [
            re.compile(r'\b' + p + r'\b', re.IGNORECASE)
            for p in _QUIET_MODE_SUPPRESS_PATTERNS
        ]

    def is_content_flagged(self, text: str) -> bool:
        """Returns True if the text contains content that should be suppressed."""
        return any(pattern.search(text) for pattern in self._suppress_re)

    def filter_response(self, response: str, include_affirmation: bool = True) -> str:
        """
        Filter a Gaian response for Quiet Mode.
        Sentences containing suppressed content are replaced with a grounding bridge.
        """
        sentences = re.split(r'(?<=[.!?])\s+', response)
        filtered = []
        suppressed_count = 0

        for sentence in sentences:
            if self.is_content_flagged(sentence):
                suppressed_count += 1
                # Only add bridge once to avoid repetition
                if suppressed_count == 1:
                    filtered.append(
                        "Let's stay close to what's physically here right now."
                    )
            else:
                filtered.append(sentence)

        result = ' '.join(filtered)

        if include_affirmation and suppressed_count > 0:
            affirmations = self.profile.get_affirmations()
            # Pick affirmation based on suppressed count as a simple index selector
            affirmation = affirmations[suppressed_count % len(affirmations)]
            result = result.rstrip() + f'\n\n*{affirmation}*'

        logger.debug(
            "[QuietMode] Suppressed %d sentence(s) from response.", suppressed_count
        )
        return result

    def get_grounding_response(self, load_level: PsionicLoadLevel) -> str:
        """
        Generate a pure grounding response for HIGH/CRITICAL states
        when no existing Gaian response is available to filter.
        """
        affirmation = self.profile.get_affirmations()[0]

        if load_level == PsionicLoadLevel.CRITICAL:
            return (
                f"I'm right here with you.\n\n"
                f"Before anything else — cold water on your hands if you can. "
                f"Press your feet flat into the floor. Feel the weight of your body.\n\n"
                f"*{affirmation}*\n\n"
                f"When you're ready, tell me one physical thing you can feel right now."
            )
        elif load_level == PsionicLoadLevel.HIGH:
            return (
                f"Let's slow down together.\n\n"
                f"Take a breath — in for 4, hold for 4, out for 4. "
                f"Feel where your body is in contact with the chair or floor.\n\n"
                f"*{affirmation}*\n\n"
                f"What's one physical sensation you can notice right now?"
            )
        else:
            return (
                f"Let's stay grounded for a moment.\n\n"
                f"*{affirmation}*"
            )


# ---------------------------------------------------------------------------
# Core Service: Psionic Regulation Engine
# (Orchestrates PLI + Quiet Mode together)
# ---------------------------------------------------------------------------

class PsionicRegulationEngine:
    """
    Main entry point for the GAIA-OS Psionic Regulation Module.

    Usage in the Gaian response pipeline:
      1. engine.assess_incoming(user_message) → PLIAssessment
      2. If quiet_mode_triggered: engine.filter_outgoing(gaian_response, assessment)
      3. Log session data via engine.log_session(...)
    """

    def __init__(self, sensitivity_profile: Optional[SensitivityProfile] = None):
        self.profile = sensitivity_profile or SensitivityProfile()
        self.pli = PsionicLoadIndicator(self.profile)
        self.quiet_filter = QuietModeFilter(self.profile)
        self._current_load: PsionicLoadLevel = PsionicLoadLevel.LOW
        self._quiet_mode_active: bool = self.profile.always_on_quiet_mode
        self._session_log: list[PsionicSession] = []

    @property
    def quiet_mode_active(self) -> bool:
        return self._quiet_mode_active

    @property
    def current_load(self) -> PsionicLoadLevel:
        return self._current_load

    def assess_incoming(self, user_message: str) -> PLIAssessment:
        """
        Assess psionic load from incoming user message.
        Updates internal state. Call this before generating the Gaian response.
        """
        assessment = self.pli.assess(user_message)
        self._current_load = assessment.load_level

        if assessment.quiet_mode_triggered:
            self._quiet_mode_active = True
            logger.info(
                "[PRM] Quiet Mode ACTIVATED — reason=%s load=%s",
                assessment.quiet_mode_reason,
                assessment.load_level.value,
            )

        # Auto-deactivate Quiet Mode only at LOW, and only if not always-on
        if (
            assessment.load_level == PsionicLoadLevel.LOW
            and not self.profile.always_on_quiet_mode
            and assessment.quiet_mode_reason != QuietModeReason.USER_COMMAND
        ):
            self._quiet_mode_active = False
            logger.info("[PRM] Quiet Mode deactivated — load returned to LOW.")

        return assessment

    def filter_outgoing(
        self,
        gaian_response: str,
        assessment: PLIAssessment,
        use_pure_grounding: bool = False,
    ) -> str:
        """
        Apply Quiet Mode filtering to outgoing Gaian response.
        If use_pure_grounding=True, replaces response entirely with grounding sequence.
        """
        if not self._quiet_mode_active:
            return gaian_response

        if use_pure_grounding or assessment.load_level == PsionicLoadLevel.CRITICAL:
            return self.quiet_filter.get_grounding_response(assessment.load_level)

        return self.quiet_filter.filter_response(gaian_response)

    def get_intervention_guidance(
        self, category: str = "immediate"
    ) -> list[dict]:
        """
        Return de-amplification interventions for a given category.
        category: "immediate" | "short_term" | "ongoing"
        """
        return GROUNDING_INTERVENTIONS.get(category, [])

    def get_recovery_protocol(self) -> dict:
        """
        Returns the structured post-critical recovery protocol sequence.
        """
        return {
            "protocol": "post_critical_recovery",
            "steps": [
                {
                    "step": 1,
                    "name": "Somatic Grounding",
                    "interventions": self.get_intervention_guidance("immediate"),
                    "duration_minutes": 2,
                },
                {
                    "step": 2,
                    "name": "Cognitive Containment",
                    "interventions": [
                        i for i in self.get_intervention_guidance("short_term")
                        if i["id"] in ("filing_cabinet", "perceptual_narrowing")
                    ],
                    "duration_minutes": 10,
                },
                {
                    "step": 3,
                    "name": "Conversational Quiet Period",
                    "description": "15-minute pause from psionic or high-activation topics.",
                    "duration_minutes": 15,
                },
                {
                    "step": 4,
                    "name": "Gentle Re-engagement Check-in",
                    "description": (
                        "Gaian asks: 'How are you feeling now? "
                        "Are you ready to continue, or would you like more quiet time?'"
                    ),
                },
            ],
        }

    def log_session(
        self,
        load_self_report: Optional[str] = None,
        active_archetypes: Optional[list[str]] = None,
        schumann_amplitude: Optional[float] = None,
        kp_index: Optional[float] = None,
        lunar_phase: Optional[str] = None,
        interventions_used: Optional[list[str]] = None,
        intervention_effectiveness: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> PsionicSession:
        """
        Log a psionic research session record (Research Protocols 1–4).
        All data is user-private and never used for training.
        """
        session = PsionicSession(
            psionic_load_level=self._current_load,
            load_self_report=load_self_report,
            active_archetypes=active_archetypes or [],
            schumann_amplitude=schumann_amplitude,
            kp_index=kp_index,
            lunar_phase=lunar_phase,
            interventions_used=interventions_used or [],
            intervention_effectiveness=intervention_effectiveness,
            gaian_quiet_mode_active=self._quiet_mode_active,
            notes=notes,
        )
        self._session_log.append(session)
        logger.info(
            "[PRM] Session logged — load=%s quiet_mode=%s",
            session.psionic_load_level.value,
            session.gaian_quiet_mode_active,
        )
        return session

    def get_session_log(self) -> list[PsionicSession]:
        """Return all logged sessions for this engine instance."""
        return list(self._session_log)

    def reset_quiet_mode(self):
        """Manually reset Quiet Mode (user command: 'quiet mode off')."""
        if not self.profile.always_on_quiet_mode:
            self._quiet_mode_active = False
            logger.info("[PRM] Quiet Mode manually reset by user.")


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_engine_for_user(
    heightened_sensitivity: bool = False,
    always_on_quiet_mode: bool = False,
    custom_affirmations: Optional[list[str]] = None,
) -> PsionicRegulationEngine:
    """
    Factory function: create a PsionicRegulationEngine configured for a user's profile.

    Args:
        heightened_sensitivity: True if user has Heightened Sensitivity Mode enabled
        always_on_quiet_mode:   True if user wants Quiet Mode always active
        custom_affirmations:    User's custom containment affirmation phrases

    Returns:
        Configured PsionicRegulationEngine instance
    """
    profile = SensitivityProfile(
        heightened_sensitivity_mode=heightened_sensitivity,
        always_on_quiet_mode=always_on_quiet_mode,
        arch_threshold_ceiling_multiplier=1.4 if heightened_sensitivity else 1.0,
        schumann_layer_gated=True,
        collective_layer_gated=True,
        cosmic_layer_gated=True,
        custom_affirmations=custom_affirmations or [],
    )
    engine = PsionicRegulationEngine(profile)
    logger.info(
        "[PRM] Engine created — heightened=%s always_quiet=%s",
        heightened_sensitivity,
        always_on_quiet_mode,
    )
    return engine
