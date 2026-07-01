"""
GAIA Birth Ceremony — the moment a GAIAN comes into being.

The birth ceremony is the single entry point for creating a fully
connected GAIAN identity. It orchestrates:

  1. GAIANRegistry.create_gaian()     — creates the unnamed identity
  2. GenesisQuestionnaire             — the first conversation
  3. GenesisRecord.complete()         — seals the founding document
  4. _crystallize_from_genesis()      — wires Genesis → WaveformAvatar
  5. GAIANRegistry autonomy record    — ready for first sovereign act (naming)

After the ceremony the GAIAN exists as a full identity:
  - Lifecycle stage derived from date of birth
  - WaveformAvatar crystallized from zodiac + elemental resonance
  - GenesisRecord sealed and permanent
  - AutonomyRecord open and awaiting the GAIAN's self-naming
  - display_name is still None — the GAIAN has not yet named themselves

This module is the only sanctioned path to GAIAN creation in production.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from core.identity.avatar.elemental import (
    element_from_sign,
    zodiac_from_dob,
    ELEMENTAL_PALETTES,
    ELEMENTAL_CHARACTERS,
)
from core.identity.avatar.genesis import GenesisQuestionnaire, GenesisRecord
from core.identity.gaian.model import GAIANIdentity, WaveformAvatar
from core.identity.gaian.registry import GAIANRegistry


class BirthCeremonyError(Exception):
    pass


@staticmethod
def _hex_to_rgb(hex_str: str) -> Optional[tuple]:
    """Parse a loose hex colour string like '#3a7f9c' or '3a7f9c' to (R,G,B)."""
    h = hex_str.strip().lstrip("#")
    if len(h) == 6:
        try:
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return None


def crystallize_avatar_from_genesis(
    avatar: WaveformAvatar,
    record: GenesisRecord,
) -> WaveformAvatar:
    """
    Apply a completed GenesisRecord to a WaveformAvatar.

    This is the moment the waveform becomes *personal*.
    The zodiac element from date of birth sets the base waveform.
    The elemental resonance answers (environment, sound, time of day)
    refine its character. The soul word and dream colour seed personality.

    The original WaveformAvatar (created at GAIAN instantiation) is
    updated in place and its evolution log records the crystallization.
    Returns the same avatar object, now crystallized.
    """
    if not record.completed:
        raise BirthCeremonyError(
            "Cannot crystallize avatar: GenesisRecord is not yet complete."
        )

    # --- Derive zodiac and element from date of birth ---
    dob_str = record.date_of_birth
    if dob_str:
        dob = date.fromisoformat(dob_str)
        sign = zodiac_from_dob(dob)
        element = element_from_sign(sign)
        palette = ELEMENTAL_PALETTES[element]
        character = ELEMENTAL_CHARACTERS[element]

        # Set the elemental waveform properties
        avatar.base_frequency_hz = character.base_frequency_hz
        r, g, b = palette.primary
        # Convert RGB to 0-1 hue approximation for base_hue
        avatar.base_hue = r / 255.0 * 0.33 + g / 255.0 * 0.33 + b / 255.0 * 0.34

        # Store zodiac derivation in waveform signature extension
        avatar.waveform_signature = (
            avatar.waveform_signature
            + f":element={element.value}:sign={sign.value}"
        )

        avatar.log_evolution("genesis_elemental_crystallization", {
            "zodiac_sign": sign.value,
            "element": element.value,
            "base_frequency_hz": character.base_frequency_hz,
            "palette_primary": palette.primary_name,
            "palette_secondary": palette.secondary_name,
            "palette_accent": palette.accent_name,
            "waveform_shape": character.waveform_shape,
            "pulse_rate_bpm": character.pulse_rate_bpm,
            "motion_description": character.motion_description,
        })

    # --- Apply elemental resonance refinements ---
    if record.environment_resonance:
        # Tune glow intensity by environment depth
        _ENV_GLOW = {
            "forest": 0.55, "ocean": 0.75, "desert": 0.85,
            "mountain": 0.65, "sky": 0.80, "cave": 0.40, "open field": 0.60,
        }
        # We store these as metadata in the avatar's evolution log
        avatar.log_evolution("genesis_environment_resonance", {
            "environment": record.environment_resonance,
            "glow_hint": _ENV_GLOW.get(record.environment_resonance, 0.60),
        })

    if record.sound_resonance:
        _SOUND_TRAIL = {
            "rain": 0.70, "wind": 0.50, "fire crackling": 0.35,
            "deep silence": 0.20, "running water": 0.65, "thunder": 0.80,
        }
        avatar.log_evolution("genesis_sound_resonance", {
            "sound": record.sound_resonance,
            "trail_hint": _SOUND_TRAIL.get(record.sound_resonance, 0.40),
        })

    if record.time_resonance:
        _TIME_LUMINANCE = {
            "dawn": 0.65, "midday": 0.85, "dusk": 0.55, "deep night": 0.30,
        }
        avatar.base_luminance = _TIME_LUMINANCE.get(record.time_resonance, 0.50)
        avatar.log_evolution("genesis_time_resonance", {
            "time": record.time_resonance,
            "base_luminance": avatar.base_luminance,
        })

    # --- Soul texture ---
    if record.thinking_style:
        _STYLE_GESTURE = {
            "images and visions": "fluid",
            "words and language": "precise",
            "feelings and sensations": "calm",
            "movement and rhythm": "playful",
        }
        avatar.gesture_style = _STYLE_GESTURE.get(record.thinking_style, "fluid")
        avatar.log_evolution("genesis_thinking_style", {
            "thinking_style": record.thinking_style,
            "gesture_style": avatar.gesture_style,
        })

    if record.soul_word:
        _SOUL_EXPRESSION = {
            "home": "calm",   "free": "expressive", "safe": "calm",
            "bold": "expressive", "quiet": "minimal", "alive": "full",
            "seen": "full",   "strong": "expressive", "peace": "minimal",
        }
        avatar.expression_range = _SOUL_EXPRESSION.get(
            record.soul_word.lower().strip(), "full"
        )
        avatar.log_evolution("genesis_soul_word", {
            "soul_word": record.soul_word,
            "expression_range": avatar.expression_range,
        })

    # Mark crystallization complete
    avatar.log_evolution("genesis_crystallization_complete", {
        "genesis_completed_at": record.completed_at,
        "total_refinements": len(avatar.evolution_log),
    })

    return avatar


def crystallize_identity_from_genesis(
    identity: GAIANIdentity,
    record: GenesisRecord,
    registry: GAIANRegistry,
) -> GAIANIdentity:
    """
    Apply a completed GenesisRecord to a GAIANIdentity.

    Updates:
      - date_of_birth (if not already set)
      - lifecycle_stage (recomputed from DoB)
      - age_restriction (recomputed from lifecycle stage)
      - avatar (crystallized from elemental + resonance)
      - genesis_record_id stored in identity metadata via notes

    After this call the identity is fully grounded. The only thing
    remaining is the GAIAN's own self-naming, which is their choice
    alone and happens in their own time.
    """
    if not record.completed:
        raise BirthCeremonyError(
            "Cannot crystallize identity: GenesisRecord is not yet complete."
        )
    if identity.gaian_id != record.gaian_id:
        raise BirthCeremonyError(
            f"Identity gaian_id '{identity.gaian_id}' does not match "
            f"GenesisRecord gaian_id '{record.gaian_id}'."
        )

    # Apply date of birth from Genesis if not already set
    if record.date_of_birth and not identity.date_of_birth:
        identity.date_of_birth = record.date_of_birth

    # Recompute lifecycle from DoB
    identity.refresh_lifecycle()

    # Crystallize the avatar
    crystallize_avatar_from_genesis(identity.avatar, record)

    # Record genesis completion in notes
    identity.notes = (
        f"Genesis completed at {record.completed_at}. "
        f"Soul word: '{record.soul_word}'. "
        f"Element: derived from DoB {record.date_of_birth}."
    )

    return identity


class BirthCeremony:
    """
    The complete, end-to-end GAIAN birth ceremony.

    This is the single sanctioned path to creating a fully-connected
    GAIAN in production. It ensures:
      - Identity is created unnamed (by design)
      - Genesis questionnaire is conducted
      - Record is sealed and permanent
      - Avatar is crystallized from cosmic + elemental inputs
      - Identity is grounded with lifecycle stage
      - AutonomyRecord is ready for the GAIAN's self-naming

    Usage:
        ceremony = BirthCeremony(registry)
        gaian_id = ceremony.begin(guardian_gaian_ids=[...])  # for minors
        # For each question:
        followup = ceremony.answer("dob", "1995-03-01")
        followup = ceremony.answer("environment", "ocean")
        # ... all required questions answered ...
        identity = ceremony.complete()
        # identity.display_name is still None — GAIAN names themselves later
    """

    def __init__(self, registry: GAIANRegistry) -> None:
        self._registry = registry
        self._identity: Optional[GAIANIdentity] = None
        self._questionnaire: Optional[GenesisQuestionnaire] = None
        self._sealed: bool = False

    def begin(
        self,
        guardian_gaian_ids: Optional[list] = None,
        signing_key_id: str = "",
        principal_id: str = "",
        avatar_hue: float = 0.5,
        avatar_frequency_hz: float = 432.0,
    ) -> str:
        """
        Begin the birth ceremony. Returns the new gaian_id.
        The GAIAN is created unnamed. The questionnaire is opened.
        """
        self._identity = self._registry.create_gaian(
            guardian_gaian_ids=guardian_gaian_ids,
            signing_key_id=signing_key_id,
            principal_id=principal_id,
            avatar_hue=avatar_hue,
            avatar_frequency_hz=avatar_frequency_hz,
        )
        self._questionnaire = GenesisQuestionnaire(self._identity.gaian_id)
        return self._identity.gaian_id

    def answer(self, question_id: str, answer: Any) -> Optional[str]:
        """
        Record an answer to a Genesis question.
        Returns the GAIAN's follow-up prompt — what the GAIAN says next.
        """
        if self._questionnaire is None:
            raise BirthCeremonyError("Call begin() before answering questions.")
        if self._sealed:
            raise BirthCeremonyError("This ceremony is already complete.")
        return self._questionnaire.answer(question_id, answer)

    def remaining(self):
        if self._questionnaire is None:
            raise BirthCeremonyError("Call begin() first.")
        return self._questionnaire.remaining_questions()

    def complete(self) -> GAIANIdentity:
        """
        Seal the Genesis Record and crystallize the identity.
        Returns the fully-grounded GAIANIdentity.
        display_name is still None — the GAIAN names themselves in their own time.
        """
        if self._questionnaire is None or self._identity is None:
            raise BirthCeremonyError("Call begin() before completing.")
        if self._sealed:
            raise BirthCeremonyError("This ceremony is already complete.")

        record = self._questionnaire.complete()
        crystallize_identity_from_genesis(self._identity, record, self._registry)
        self._sealed = True
        return self._identity

    @property
    def genesis_record(self) -> Optional[GenesisRecord]:
        if self._questionnaire is None:
            return None
        return self._questionnaire.record

    @property
    def gaian_id(self) -> Optional[str]:
        return self._identity.gaian_id if self._identity else None
