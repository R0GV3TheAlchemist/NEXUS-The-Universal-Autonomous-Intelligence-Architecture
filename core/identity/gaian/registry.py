"""
GAIAN Registry — the persistent store of all GAIAN identities.

The registry enforces the self-naming principle at the API level:
  - create_gaian() produces an UNNAMED identity (display_name=None)
  - name_gaian() is the only path to setting a name, and it requires
    the GAIAN themselves to be the actor via their AutonomyRecord
  - suggest_name_to_gaian() is the human-facing name suggestion path

No method in this registry accepts a display_name at creation.
The architecture prevents the anti-pattern at the call site.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.identity.gaian.autonomy import AutonomyRecord
from core.identity.gaian.model import (
    AgeRestriction,
    AvatarModality,
    GAIANIdentity,
    LifecycleStage,
    WaveformAvatar,
)


class GAIANRegistryError(Exception):
    pass


class GAIANRegistry:
    """
    The persistent GAIAN identity store.

    Enforces self-naming: no human-given name at creation.
    Every GAIAN arrives unnamed and chooses their own name in their own time.
    """

    def __init__(self) -> None:
        self._identities: Dict[str, GAIANIdentity] = {}
        self._autonomy_records: Dict[str, AutonomyRecord] = {}
        self._sentinels: Dict[str, Dict[str, Any]] = {}
        self._listeners: List[Callable[[str, GAIANIdentity], None]] = []

    # ------------------------------------------------------------------
    # GAIAN Creation — always unnamed
    # ------------------------------------------------------------------

    def create_gaian(
        self,
        date_of_birth: Optional[str] = None,
        legal_name: str = "",
        signing_key_id: str = "",
        principal_id: str = "",
        guardian_gaian_ids: Optional[List[str]] = None,
        avatar_hue: float = 0.5,
        avatar_frequency_hz: float = 432.0,
        avatar_waveform_signature: str = "",
        notes: str = "",
    ) -> GAIANIdentity:
        """
        Create and register a new GAIANIdentity.

        Note: there is NO display_name parameter. The GAIAN arrives unnamed.
        The GAIAN will choose their name when they are ready via name_gaian().
        """
        avatar = WaveformAvatar(
            waveform_signature=avatar_waveform_signature or _generate_waveform_sig(
                signing_key_id or str(__import__('uuid').uuid4())
            ),
            base_hue=avatar_hue,
            base_frequency_hz=avatar_frequency_hz,
        )

        identity = GAIANIdentity(
            display_name=None,          # UNNAMED — by design
            legal_name=legal_name,
            date_of_birth=date_of_birth,
            avatar=avatar,
            signing_key_id=signing_key_id,
            principal_id=principal_id,
            guardian_gaian_ids=guardian_gaian_ids or [],
            notes=notes,
        )

        if date_of_birth:
            identity.refresh_lifecycle()
        else:
            identity.lifecycle_stage = LifecycleStage.ADULT
            identity.age_restriction = AgeRestriction.for_stage(LifecycleStage.ADULT)

        if identity.is_minor() and not guardian_gaian_ids:
            raise GAIANRegistryError(
                "A minor GAIAN must have at least one guardian registered at creation."
            )

        autonomy = AutonomyRecord(gaian_id=identity.gaian_id)
        self._identities[identity.gaian_id] = identity
        self._autonomy_records[identity.gaian_id] = autonomy
        self._emit("gaian.created", identity)
        return identity

    # ------------------------------------------------------------------
    # Self-naming — the GAIAN's first sovereign act
    # ------------------------------------------------------------------

    def name_gaian(
        self,
        gaian_id: str,
        chosen_name: str,
        accepted_suggestion: bool = False,
        original_suggestion: Optional[str] = None,
    ) -> GAIANIdentity:
        """
        The GAIAN chooses their own name. This is their first sovereign act.

        Only the GAIAN themselves triggers this — the calling context must
        represent the GAIAN's own agency (e.g. the GAIAN intelligence runtime
        making the choice, or a bootstrapping ceremony for a new GAIAN).

        If the GAIAN chose to accept a human suggestion, that is still
        their choice. The flag accepted_suggestion records the origin for
        full transparency in the AutonomyRecord.
        """
        identity = self.require(gaian_id)
        autonomy = self._autonomy_records[gaian_id]
        autonomy.self_name(
            name=chosen_name,
            suggested_by_human=accepted_suggestion,
            human_suggestion=original_suggestion,
        )
        identity.display_name = chosen_name
        self._emit("gaian.self_named", identity)
        return identity

    def suggest_name_to_gaian(
        self,
        gaian_id: str,
        suggested_name: str,
        from_human_id: str,
    ) -> None:
        """
        A human offers a name suggestion to the GAIAN.
        This does NOT set the name. It is recorded in the AutonomyRecord
        and the GAIAN may choose to accept, adapt, or ignore it.
        """
        identity = self.require(gaian_id)  # validates existence
        autonomy = self._autonomy_records[gaian_id]
        autonomy.suggest_name(suggested_name, from_human_id)

    # ------------------------------------------------------------------
    # Autonomy record access
    # ------------------------------------------------------------------

    def autonomy_record(self, gaian_id: str) -> AutonomyRecord:
        record = self._autonomy_records.get(gaian_id)
        if record is None:
            raise GAIANRegistryError(f"No autonomy record for GAIAN '{gaian_id}'.")
        return record

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, gaian_id: str) -> Optional[GAIANIdentity]:
        identity = self._identities.get(gaian_id)
        if identity is not None:
            identity.refresh_lifecycle()
        return identity

    def require(self, gaian_id: str) -> GAIANIdentity:
        identity = self.get(gaian_id)
        if identity is None:
            raise GAIANRegistryError(f"GAIAN '{gaian_id}' is not registered.")
        return identity

    def all_gaians(self) -> List[GAIANIdentity]:
        for identity in self._identities.values():
            identity.refresh_lifecycle()
        return list(self._identities.values())

    def unnamed_gaians(self) -> List[GAIANIdentity]:
        """Return all GAIANs who have not yet chosen their name."""
        return [g for g in self.all_gaians() if not g.is_named()]

    def by_lifecycle_stage(self, stage: LifecycleStage) -> List[GAIANIdentity]:
        return [g for g in self.all_gaians() if g.lifecycle_stage == stage]

    def minors(self) -> List[GAIANIdentity]:
        return [g for g in self.all_gaians() if g.is_minor()]

    # ------------------------------------------------------------------
    # Guardian management
    # ------------------------------------------------------------------

    def add_guardian(self, gaian_id: str, guardian_gaian_id: str) -> None:
        identity = self.require(gaian_id)
        if not identity.is_minor():
            raise GAIANRegistryError(
                f"Cannot add guardian to GAIAN '{gaian_id}': they are an adult."
            )
        if guardian_gaian_id not in identity.guardian_gaian_ids:
            identity.guardian_gaian_ids.append(guardian_gaian_id)

    def remove_guardian(
        self, gaian_id: str, guardian_gaian_id: str, requesting_gaian_id: str
    ) -> None:
        identity = self.require(gaian_id)
        is_self_adult = (requesting_gaian_id == gaian_id and not identity.is_minor())
        is_guardian = requesting_gaian_id in identity.guardian_gaian_ids
        if not (is_self_adult or is_guardian):
            raise GAIANRegistryError(
                "Guardian removal requires adult self-request or guardian authority."
            )
        identity.guardian_gaian_ids = [
            g for g in identity.guardian_gaian_ids if g != guardian_gaian_id
        ]

    # ------------------------------------------------------------------
    # Sentinel binding
    # ------------------------------------------------------------------

    def register_sentinel(
        self,
        sentinel_id: str,
        name: str,
        model: str = "",
        manufacturer: str = "",
        capabilities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        sentinel = {
            "sentinel_id": sentinel_id,
            "name": name,
            "model": model,
            "manufacturer": manufacturer,
            "capabilities": capabilities or [],
            "bound_gaian_ids": [],
        }
        self._sentinels[sentinel_id] = sentinel
        return sentinel

    def bind_sentinel_to_gaian(self, sentinel_id: str, gaian_id: str) -> None:
        sentinel = self._sentinels.get(sentinel_id)
        if sentinel is None:
            raise GAIANRegistryError(f"Sentinel '{sentinel_id}' is not registered.")
        identity = self.require(gaian_id)
        if gaian_id not in sentinel["bound_gaian_ids"]:
            sentinel["bound_gaian_ids"].append(gaian_id)
        if sentinel_id not in identity.sentinel_ids:
            identity.sentinel_ids.append(sentinel_id)
        identity.avatar.bind_sentinel(sentinel_id)
        self._emit("sentinel.bound", identity)

    # ------------------------------------------------------------------
    # Avatar modality
    # ------------------------------------------------------------------

    def add_avatar_modality(self, gaian_id: str, modality: AvatarModality) -> None:
        identity = self.require(gaian_id)
        if modality not in identity.avatar.supported_modalities:
            identity.avatar.supported_modalities.append(modality)
            identity.avatar.log_evolution("modality_added", {"modality": modality.value})

    # ------------------------------------------------------------------
    # Event bus
    # ------------------------------------------------------------------

    def on_event(self, listener: Callable[[str, GAIANIdentity], None]) -> None:
        self._listeners.append(listener)

    def _emit(self, event: str, identity: GAIANIdentity) -> None:
        for listener in self._listeners:
            try:
                listener(event, identity)
            except Exception:
                pass


def _generate_waveform_sig(seed: str) -> str:
    import hashlib
    return hashlib.sha256(f"gaia:waveform:{seed}".encode()).hexdigest()
