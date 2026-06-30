"""SpaceManager — high-level operations on the SpaceStore.

The manager provides the principal-aware API that the agentic loop and
external surfaces call. It enforces:
  - Ownership rules (only OWNER can archive, destroy, manage members)
  - Write-lock checks (LOCKED spaces reject context mutations)
  - Consent hook (optional — pluggable callable for action_gate)
  - Event emission on every state change

Usage:
    store = SpaceStore()
    manager = SpaceManager(store)

    space = manager.create("project-x", owner_id="gaian-1", description="...")
    manager.join(space.space_id, principal_id="gaian-2", role=SpaceRole.STEWARD)
    manager.set_context(space.space_id, actor_id="gaian-2", key="phase", value="planning")
    ctx = manager.get_context(space.space_id, "phase")
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.spaces.model import (
    Space,
    SpaceEvent,
    SpaceEventKind,
    SpaceMember,
    SpaceRole,
    SpaceStatus,
)
from core.spaces.store import SpaceStore


class PermissionError(Exception):
    """Raised when a principal attempts a forbidden action."""


class SpaceManager:
    """Principal-aware Space lifecycle and context manager.

    Args:
        store: The SpaceStore this manager operates on.
        consent_checker: Optional callable(space_id, actor_id, action) -> bool.
            When provided, called before any write that mutates a LOCKED space.
    """

    def __init__(
        self,
        store: SpaceStore,
        consent_checker: Optional[Callable[[str, str, str], bool]] = None,
    ) -> None:
        self.store = store
        self.consent_checker = consent_checker

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        owner_id: str,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Space:
        """Create and persist a new Space. The owner is auto-added."""
        space = Space(
            name=name,
            owner_id=owner_id,
            description=description,
            tags=tags or [],
        )
        space.add_member(owner_id, role=SpaceRole.OWNER, actor_id=owner_id)
        space.events.append(SpaceEvent(
            kind=SpaceEventKind.CREATED,
            actor_id=owner_id,
            payload={"name": name},
        ))
        self.store.save(space)
        return space

    def archive(self, space_id: str, actor_id: str) -> Space:
        space = self._require_owner(space_id, actor_id)
        space.set_status(SpaceStatus.ARCHIVED, actor_id=actor_id)
        self.store.save(space)
        return space

    def destroy(self, space_id: str, actor_id: str) -> Space:
        space = self._require_owner(space_id, actor_id)
        space.set_status(SpaceStatus.DESTROYED, actor_id=actor_id)
        self.store.save(space)
        return space

    def lock(self, space_id: str, actor_id: str) -> Space:
        space = self._require_owner(space_id, actor_id)
        space.set_status(SpaceStatus.LOCKED, actor_id=actor_id)
        self.store.save(space)
        return space

    def unlock(self, space_id: str, actor_id: str) -> Space:
        space = self._require_owner(space_id, actor_id)
        space.set_status(SpaceStatus.ACTIVE, actor_id=actor_id)
        self.store.save(space)
        return space

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def join(
        self,
        space_id: str,
        principal_id: str,
        role: SpaceRole = SpaceRole.OBSERVER,
        display_name: str = "",
        actor_id: str = "",
    ) -> SpaceMember:
        space = self.store.require(space_id)
        self._assert_not_destroyed(space)
        # Only an owner may grant non-observer roles
        if role != SpaceRole.OBSERVER and actor_id:
            self._assert_owner(space, actor_id)
        member = space.add_member(
            principal_id,
            role=role,
            display_name=display_name,
            actor_id=actor_id or principal_id,
        )
        self.store.save(space)
        return member

    def leave(self, space_id: str, principal_id: str) -> None:
        space = self.store.require(space_id)
        self._assert_not_destroyed(space)
        space.remove_member(principal_id, actor_id=principal_id)
        self.store.save(space)

    def change_role(
        self,
        space_id: str,
        principal_id: str,
        new_role: SpaceRole,
        actor_id: str,
    ) -> None:
        space = self._require_owner(space_id, actor_id)
        space.change_member_role(principal_id, new_role, actor_id=actor_id)
        self.store.save(space)

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def set_context(
        self,
        space_id: str,
        key: str,
        value: Any,
        actor_id: str,
    ) -> None:
        space = self.store.require(space_id)
        self._assert_writable(space, actor_id)
        self._check_consent(space_id, actor_id, "set_context")
        space.set_context(key, value, actor_id=actor_id)
        self.store.save(space)

    def delete_context(self, space_id: str, key: str, actor_id: str) -> None:
        space = self.store.require(space_id)
        self._assert_writable(space, actor_id)
        space.delete_context(key, actor_id=actor_id)
        self.store.save(space)

    def get_context(self, space_id: str, key: str) -> Any:
        space = self.store.require(space_id)
        return space.context.get(key)

    def get_all_context(self, space_id: str) -> Dict[str, Any]:
        return dict(self.store.require(space_id).context)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def emit(
        self,
        space_id: str,
        actor_id: str,
        kind: SpaceEventKind = SpaceEventKind.CUSTOM,
        payload: Optional[Dict[str, Any]] = None,
    ) -> SpaceEvent:
        space = self.store.require(space_id)
        self._assert_not_destroyed(space)
        if not space.is_member(actor_id):
            raise PermissionError(
                f"Principal '{actor_id}' is not a member of space '{space_id}'."
            )
        event = space.emit(kind=kind, actor_id=actor_id, payload=payload)
        self.store.save(space)
        return event

    def get_events(
        self,
        space_id: str,
        kind: Optional[SpaceEventKind] = None,
    ) -> List[SpaceEvent]:
        space = self.store.require(space_id)
        if kind is None:
            return list(space.events)
        return [e for e in space.events if e.kind == kind]

    # ------------------------------------------------------------------
    # Criticality (hook for CriticalityMonitor)
    # ------------------------------------------------------------------

    def set_criticality(self, space_id: str, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Criticality must be in [0.0, 1.0].")
        space = self.store.require(space_id)
        space.criticality = value
        space._touch()
        self.store.save(space)

    # ------------------------------------------------------------------
    # Internal guards
    # ------------------------------------------------------------------

    def _assert_owner(self, space: Space, actor_id: str) -> None:
        member = space.members.get(actor_id)
        if member is None or member.role != SpaceRole.OWNER:
            raise PermissionError(
                f"Principal '{actor_id}' is not an owner of space '{space.space_id}'."
            )

    def _require_owner(self, space_id: str, actor_id: str) -> Space:
        space = self.store.require(space_id)
        self._assert_owner(space, actor_id)
        return space

    def _assert_not_destroyed(self, space: Space) -> None:
        if space.status == SpaceStatus.DESTROYED:
            raise PermissionError(
                f"Space '{space.space_id}' has been destroyed."
            )

    def _assert_writable(self, space: Space, actor_id: str) -> None:
        self._assert_not_destroyed(space)
        if space.status == SpaceStatus.ARCHIVED:
            raise PermissionError("Space is archived and read-only.")
        if not space.can_write(actor_id):
            raise PermissionError(
                f"Principal '{actor_id}' does not have write access."
            )

    def _check_consent(
        self,
        space_id: str,
        actor_id: str,
        action: str,
    ) -> None:
        if self.consent_checker is None:
            return
        allowed = self.consent_checker(space_id, actor_id, action)
        if not allowed:
            raise PermissionError(
                f"Consent denied for action '{action}' by '{actor_id}' on space '{space_id}'."
            )
