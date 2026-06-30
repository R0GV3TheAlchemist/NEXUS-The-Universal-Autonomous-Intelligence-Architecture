"""Space data model — the core domain types for GAIA Spaces.

All types are pure-Python dataclasses with no external dependencies so
they can be freely serialised, compared, and tested in isolation.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SpaceStatus(str, Enum):
    ACTIVE = "active"        # operational — context reads/writes allowed
    LOCKED = "locked"        # read-only until explicitly unlocked
    ARCHIVED = "archived"    # immutable historical record
    DESTROYED = "destroyed"  # soft-deleted; no operations permitted


class SpaceRole(str, Enum):
    OWNER = "owner"          # full control: archive, destroy, manage members
    STEWARD = "steward"      # can write context and emit events
    OBSERVER = "observer"    # read-only access


class SpaceEventKind(str, Enum):
    CREATED = "created"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_ROLE_CHANGED = "member_role_changed"
    CONTEXT_SET = "context_set"
    CONTEXT_DELETED = "context_deleted"
    STATUS_CHANGED = "status_changed"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SpaceMember:
    """A participant in a Space.

    A member is identified by a principal_id (user, agent, or system
    process) and carries a role that governs what operations they may
    perform.
    """
    principal_id: str
    role: SpaceRole = SpaceRole.OBSERVER
    joined_at: str = field(default_factory=_utcnow)
    display_name: str = ""


@dataclass
class SpaceEvent:
    """An immutable record of something that happened in a Space.

    Events are append-only; once written they are never modified.
    The payload is an arbitrary dict so each event kind can carry its
    own structured data without requiring schema migrations.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kind: SpaceEventKind = SpaceEventKind.CUSTOM
    actor_id: str = ""          # principal that triggered the event
    payload: Dict[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=_utcnow)


@dataclass
class Space:
    """A persistent, named, shared environment.

    Attributes:
        space_id:      Unique identifier (UUID by default).
        name:          Human-readable label, unique within a SpaceStore.
        description:   Purpose of this Space.
        status:        Lifecycle state.
        owner_id:      Principal who created and owns the Space.
        members:       Roster of participants indexed by principal_id.
        context:       Mutable key-value store; values are any JSON-safe type.
        events:        Append-only log of everything that has happened.
        criticality:   Float [0, 1] — 0.5 ≈ edge-of-chaos target.
        tags:          Free-form labels for search and filter.
        created_at:    ISO-8601 creation timestamp.
        updated_at:    ISO-8601 timestamp of last modification.
    """
    name: str
    owner_id: str
    space_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: SpaceStatus = SpaceStatus.ACTIVE
    members: Dict[str, SpaceMember] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    events: List[SpaceEvent] = field(default_factory=list)
    criticality: float = 0.5
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_member(self, principal_id: str) -> Optional[SpaceMember]:
        return self.members.get(principal_id)

    def is_member(self, principal_id: str) -> bool:
        return principal_id in self.members

    def can_write(self, principal_id: str) -> bool:
        member = self.members.get(principal_id)
        if member is None:
            return False
        return member.role in (SpaceRole.OWNER, SpaceRole.STEWARD)

    def is_writable(self) -> bool:
        return self.status == SpaceStatus.ACTIVE

    # ------------------------------------------------------------------
    # Mutation helpers (return self for chaining; caller owns persistence)
    # ------------------------------------------------------------------

    def _touch(self) -> None:
        self.updated_at = _utcnow()

    def _append_event(self, event: SpaceEvent) -> None:
        self.events.append(event)
        self._touch()

    def add_member(
        self,
        principal_id: str,
        role: SpaceRole = SpaceRole.OBSERVER,
        display_name: str = "",
        actor_id: str = "",
    ) -> SpaceMember:
        member = SpaceMember(
            principal_id=principal_id,
            role=role,
            display_name=display_name,
        )
        self.members[principal_id] = member
        self._append_event(SpaceEvent(
            kind=SpaceEventKind.MEMBER_JOINED,
            actor_id=actor_id or principal_id,
            payload={"principal_id": principal_id, "role": role.value},
        ))
        return member

    def remove_member(self, principal_id: str, actor_id: str = "") -> None:
        if principal_id in self.members:
            del self.members[principal_id]
            self._append_event(SpaceEvent(
                kind=SpaceEventKind.MEMBER_LEFT,
                actor_id=actor_id or principal_id,
                payload={"principal_id": principal_id},
            ))

    def change_member_role(
        self,
        principal_id: str,
        new_role: SpaceRole,
        actor_id: str = "",
    ) -> None:
        member = self.members.get(principal_id)
        if member is None:
            raise KeyError(f"Principal '{principal_id}' is not a member.")
        old_role = member.role
        member.role = new_role
        self._append_event(SpaceEvent(
            kind=SpaceEventKind.MEMBER_ROLE_CHANGED,
            actor_id=actor_id,
            payload={"principal_id": principal_id, "old_role": old_role.value, "new_role": new_role.value},
        ))

    def set_context(self, key: str, value: Any, actor_id: str = "") -> None:
        self.context[key] = value
        self._append_event(SpaceEvent(
            kind=SpaceEventKind.CONTEXT_SET,
            actor_id=actor_id,
            payload={"key": key},
        ))

    def delete_context(self, key: str, actor_id: str = "") -> None:
        if key in self.context:
            del self.context[key]
            self._append_event(SpaceEvent(
                kind=SpaceEventKind.CONTEXT_DELETED,
                actor_id=actor_id,
                payload={"key": key},
            ))

    def set_status(self, new_status: SpaceStatus, actor_id: str = "") -> None:
        old = self.status
        self.status = new_status
        self._append_event(SpaceEvent(
            kind=SpaceEventKind.STATUS_CHANGED,
            actor_id=actor_id,
            payload={"old": old.value, "new": new_status.value},
        ))

    def emit(
        self,
        kind: SpaceEventKind = SpaceEventKind.CUSTOM,
        actor_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> SpaceEvent:
        event = SpaceEvent(kind=kind, actor_id=actor_id, payload=payload or {})
        self._append_event(event)
        return event

    def summary(self) -> Dict[str, Any]:
        return {
            "space_id": self.space_id,
            "name": self.name,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "member_count": len(self.members),
            "context_keys": list(self.context.keys()),
            "event_count": len(self.events),
            "criticality": self.criticality,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
