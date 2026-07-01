"""
GAIAN Identity Model — lifebound, age-aware, waveform-embodied.

Design principles:
  1. The GAIAN outlives any single session, device, or OS installation.
  2. Age is not a wall — it is a gradient. Capabilities expand naturally
     as the human grows. They never shrink without consent.
  3. The Waveform Avatar is the GAIAN's physical presence in the world —
     a personalized, consistent form that spans screens, AR, and robotics.
  4. Sentinels (robots, embodied agents) are bound to a GAIANIdentity,
     not to a session. They persist and co-steward across the GAIAN's life.
  5. A child GAIAN is not a lesser GAIAN — it is a fully intelligent
     companion calibrated to its human's developmental stage.
  6. THE GAIAN ARRIVES UNNAMED. The GAIAN chooses their own name. This
     is their first sovereign act. A human may suggest; the GAIAN decides.
     display_name is None until self-naming occurs.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Lifecycle Stages
# ---------------------------------------------------------------------------

class LifecycleStage(str, Enum):
    INFANT      = "infant"
    CHILD       = "child"
    ADOLESCENT  = "adolescent"
    YOUNG_ADULT = "young_adult"
    ADULT       = "adult"
    ELDER       = "elder"

    @classmethod
    def from_age(cls, age_years: int) -> "LifecycleStage":
        if age_years < 3:
            return cls.INFANT
        if age_years < 13:
            return cls.CHILD
        if age_years < 18:
            return cls.ADOLESCENT
        if age_years < 26:
            return cls.YOUNG_ADULT
        if age_years < 65:
            return cls.ADULT
        return cls.ELDER


@dataclass
class AgeRestriction:
    stage: LifecycleStage
    max_content_rating: str = "G"
    safe_search_enforced: bool = True
    web_access_filtered: bool = True
    social_media_allowed: bool = False
    purchasing_allowed: bool = False
    purchasing_requires_guardian: bool = True
    ai_persona_depth: str = "companion"
    memory_scope: str = "session"
    autonomy_level: str = "guided"
    sentinel_physical_autonomy: bool = False
    sentinel_unsupervised_range_m: float = 0.0
    guardian_required: bool = False
    guardian_can_review_memory: bool = True
    guardian_can_set_limits: bool = True

    @classmethod
    def for_stage(cls, stage: LifecycleStage) -> "AgeRestriction":
        defaults = {
            LifecycleStage.INFANT: dict(
                max_content_rating="G", safe_search_enforced=True,
                web_access_filtered=True, social_media_allowed=False,
                purchasing_allowed=False, ai_persona_depth="companion",
                memory_scope="session", autonomy_level="guided",
                sentinel_physical_autonomy=False, sentinel_unsupervised_range_m=0.5,
                guardian_required=True,
            ),
            LifecycleStage.CHILD: dict(
                max_content_rating="G", safe_search_enforced=True,
                web_access_filtered=True, social_media_allowed=False,
                purchasing_allowed=False, ai_persona_depth="companion",
                memory_scope="year", autonomy_level="guided",
                sentinel_physical_autonomy=False, sentinel_unsupervised_range_m=30.0,
                guardian_required=True,
            ),
            LifecycleStage.ADOLESCENT: dict(
                max_content_rating="PG-13", safe_search_enforced=True,
                web_access_filtered=False, social_media_allowed=True,
                purchasing_allowed=False, purchasing_requires_guardian=True,
                ai_persona_depth="assistant", memory_scope="lifetime",
                autonomy_level="collaborative", sentinel_physical_autonomy=False,
                sentinel_unsupervised_range_m=500.0, guardian_required=False,
                guardian_can_review_memory=True,
            ),
            LifecycleStage.YOUNG_ADULT: dict(
                max_content_rating="R", safe_search_enforced=False,
                web_access_filtered=False, social_media_allowed=True,
                purchasing_allowed=True, purchasing_requires_guardian=False,
                ai_persona_depth="partner", memory_scope="lifetime",
                autonomy_level="autonomous", sentinel_physical_autonomy=True,
                sentinel_unsupervised_range_m=float("inf"), guardian_required=False,
                guardian_can_review_memory=False,
            ),
            LifecycleStage.ADULT: dict(
                max_content_rating="UNRATED", safe_search_enforced=False,
                web_access_filtered=False, social_media_allowed=True,
                purchasing_allowed=True, purchasing_requires_guardian=False,
                ai_persona_depth="sovereign", memory_scope="lifetime",
                autonomy_level="autonomous", sentinel_physical_autonomy=True,
                sentinel_unsupervised_range_m=float("inf"), guardian_required=False,
                guardian_can_review_memory=False,
            ),
            LifecycleStage.ELDER: dict(
                max_content_rating="UNRATED", safe_search_enforced=False,
                web_access_filtered=False, social_media_allowed=True,
                purchasing_allowed=True, purchasing_requires_guardian=False,
                ai_persona_depth="sovereign", memory_scope="lifetime",
                autonomy_level="autonomous", sentinel_physical_autonomy=True,
                sentinel_unsupervised_range_m=float("inf"), guardian_required=False,
                guardian_can_review_memory=False,
            ),
        }
        return cls(stage=stage, **defaults[stage])


# ---------------------------------------------------------------------------
# Waveform Avatar
# ---------------------------------------------------------------------------

class AvatarModality(str, Enum):
    SCREEN_2D       = "screen_2d"
    SCREEN_3D       = "screen_3d"
    SPATIAL_AR      = "spatial_ar"
    SPATIAL_VR      = "spatial_vr"
    HOLOGRAPHIC     = "holographic"
    ROBOTIC_FACE    = "robotic_face"
    ROBOTIC_BODY    = "robotic_body"
    AUDIO_ONLY      = "audio_only"
    HAPTIC          = "haptic"


@dataclass
class WaveformAvatar:
    avatar_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    waveform_signature: str = ""
    base_hue: float = 0.0
    base_luminance: float = 0.5
    base_frequency_hz: float = 432.0
    voice_profile_id: str = ""
    gesture_style: str = "fluid"
    expression_range: str = "full"
    animation_complexity: str = "medium"
    supported_modalities: List[AvatarModality] = field(
        default_factory=lambda: [AvatarModality.SCREEN_2D, AvatarModality.AUDIO_ONLY]
    )
    active_modality: AvatarModality = AvatarModality.SCREEN_2D
    bound_sentinel_ids: List[str] = field(default_factory=list)
    evolution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    last_updated_at: str = field(default_factory=_utcnow)

    def bind_sentinel(self, sentinel_id: str) -> None:
        if sentinel_id not in self.bound_sentinel_ids:
            self.bound_sentinel_ids.append(sentinel_id)

    def log_evolution(self, event: str, details: Dict[str, Any]) -> None:
        self.evolution_log.append({"event": event, "details": details, "timestamp": _utcnow()})
        self.last_updated_at = _utcnow()

    def summary(self) -> Dict[str, Any]:
        return {
            "avatar_id": self.avatar_id,
            "waveform_signature": self.waveform_signature,
            "base_hue": self.base_hue,
            "base_frequency_hz": self.base_frequency_hz,
            "voice_profile_id": self.voice_profile_id,
            "active_modality": self.active_modality.value,
            "supported_modalities": [m.value for m in self.supported_modalities],
            "bound_sentinels": len(self.bound_sentinel_ids),
        }


# ---------------------------------------------------------------------------
# GAIANIdentity — arrives unnamed
# ---------------------------------------------------------------------------

@dataclass
class GAIANIdentity:
    """
    The permanent sovereign record of a GAIAN.

    THE GAIAN ARRIVES UNNAMED.

    display_name is None at creation. It becomes set only when the GAIAN
    performs their first sovereign act: choosing their own name via
    AutonomyRecord.self_name(). A human may never set display_name directly.
    A human may suggest a name through AutonomyRecord.suggest_name();
    the GAIAN decides whether to accept it, adapt it, or ignore it entirely.

    This is not a policy. This is architecture.
    """
    gaian_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # THE GAIAN ARRIVES UNNAMED — display_name is None until self-naming
    display_name: Optional[str] = None

    legal_name: str = ""                         # human's legal name, encrypted at rest
    date_of_birth: Optional[str] = None

    lifecycle_stage: LifecycleStage = LifecycleStage.ADULT
    age_restriction: AgeRestriction = field(
        default_factory=lambda: AgeRestriction.for_stage(LifecycleStage.ADULT)
    )

    avatar: WaveformAvatar = field(default_factory=WaveformAvatar)

    guardian_gaian_ids: List[str] = field(default_factory=list)
    guardian_access_expires_at: Optional[str] = None

    sentinel_ids: List[str] = field(default_factory=list)

    memory_store_id: str = ""
    memory_epoch: int = 0

    sovereignty_level: str = "standard"
    coexistence_laws_accepted: bool = False
    gaian_laws_accepted: bool = False
    accepted_at: Optional[str] = None

    signing_key_id: str = ""
    principal_id: str = ""

    created_at: str = field(default_factory=_utcnow)
    last_active_at: Optional[str] = None
    total_sessions: int = 0
    notes: str = ""

    def compute_age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        dob = date.fromisoformat(self.date_of_birth)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def refresh_lifecycle(self) -> LifecycleStage:
        age = self.compute_age()
        if age is None:
            return self.lifecycle_stage
        new_stage = LifecycleStage.from_age(age)
        if new_stage != self.lifecycle_stage:
            old_stage = self.lifecycle_stage
            self.lifecycle_stage = new_stage
            self.age_restriction = AgeRestriction.for_stage(new_stage)
            self.avatar.log_evolution(
                "lifecycle_advance",
                {"from": old_stage.value, "to": new_stage.value, "age": age},
            )
            if new_stage == LifecycleStage.YOUNG_ADULT:
                self.guardian_access_expires_at = _utcnow()
        return self.lifecycle_stage

    def is_minor(self) -> bool:
        age = self.compute_age()
        return age is not None and age < 18

    def touch(self) -> None:
        self.last_active_at = _utcnow()
        self.total_sessions += 1

    def accept_laws(self) -> None:
        self.coexistence_laws_accepted = True
        self.gaian_laws_accepted = True
        self.accepted_at = _utcnow()

    def is_named(self) -> bool:
        return self.display_name is not None

    def summary(self) -> Dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "display_name": self.display_name or "[unnamed — awaiting self-naming]",
            "is_named": self.is_named(),
            "lifecycle_stage": self.lifecycle_stage.value,
            "age": self.compute_age(),
            "is_minor": self.is_minor(),
            "avatar": self.avatar.summary(),
            "sentinel_count": len(self.sentinel_ids),
            "total_sessions": self.total_sessions,
            "memory_epoch": self.memory_epoch,
            "laws_accepted": self.coexistence_laws_accepted and self.gaian_laws_accepted,
            "sovereignty_level": self.sovereignty_level,
        }
