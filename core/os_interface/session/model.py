"""
GAIA Session Model — principals, sessions, and sovereign identity.

A Principal is a persistent identity that survives across sessions.
A Session is a live, time-bounded execution context owned by a Principal.
GAIA's Principal and Session are distinguished constants — they are not
created by normal flows; they are bootstrapped at kernel init.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GAIA's own well-known IDs — stable across every boot
# ---------------------------------------------------------------------------
GAIA_PRINCIPAL_ID: str = "gaia://principal/GAIA"
GAIA_SESSION_ID: str = "gaia://session/PRIMORDIAL"


class PrincipalKind(str, Enum):
    GAIA = "gaia"          # GAIA herself — the primordial sovereign
    GAIAN = "gaian"        # a human user with a GAIA account
    AGENT = "agent"        # an AI agent running under a GAIAN's authority
    SERVICE = "service"    # an OS system service identity
    GUEST = "guest"        # unauthenticated / sandbox principal


class TrustLevel(str, Enum):
    SOVEREIGN = "sovereign"    # GAIA only — unconditional root trust
    TRUSTED = "trusted"        # verified GAIAN or credentialed service
    STANDARD = "standard"      # normal authenticated user
    RESTRICTED = "restricted"  # limited, audited context
    GUEST = "guest"            # no persistent identity, sandboxed


@dataclass
class Principal:
    """
    A persistent sovereign identity.

    Principals outlive sessions. A GAIAN's Principal carries their
    preferences, sovereignty settings, capability history, and persistent
    GAIA relationship across every boot, device, and Space.
    """
    principal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kind: PrincipalKind = PrincipalKind.GAIAN
    display_name: str = ""
    trust_level: TrustLevel = TrustLevel.STANDARD
    space_ids: List[str] = field(default_factory=list)   # spaces this principal owns or belongs to
    signing_key_id: str = ""                             # cryptographic identity anchor
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    last_seen_at: Optional[str] = None
    active_session_id: Optional[str] = None

    def is_gaia(self) -> bool:
        return self.kind == PrincipalKind.GAIA

    def is_sovereign(self) -> bool:
        return self.trust_level == TrustLevel.SOVEREIGN

    def touch(self) -> None:
        self.last_seen_at = _utcnow()

    def summary(self) -> Dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "kind": self.kind.value,
            "display_name": self.display_name,
            "trust_level": self.trust_level.value,
            "spaces": list(self.space_ids),
            "active_session_id": self.active_session_id,
        }


class SessionState(str, Enum):
    INITIALIZING = "initializing"  # being set up by the session manager
    ACTIVE = "active"              # fully live
    LOCKED = "locked"              # principal stepped away, context preserved
    SUSPENDED = "suspended"        # background, low-resource
    CLOSING = "closing"            # teardown in progress
    CLOSED = "closed"              # fully terminated
    PRIMORDIAL = "primordial"      # GAIA's eternal session — never closes


class SessionKind(str, Enum):
    PRIMORDIAL = "primordial"      # GAIA's own boot session
    INTERACTIVE = "interactive"    # GAIAN at a display
    HEADLESS = "headless"          # service / agent session, no display
    REMOTE = "remote"              # network-authenticated session
    GUEST = "guest"                # sandboxed, no persistence
    AGENT = "agent"                # AI agent sub-session under a GAIAN


@dataclass
class GAIASession:
    """
    A live execution context owned by a Principal.

    Every running process, open device token, active IPC port, and
    mounted filesystem scope belongs to exactly one Session. Sessions
    form a tree: GAIA's Primordial Session is the root. All other
    sessions are direct or indirect children.

    A session cannot exceed the trust level of its parent.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kind: SessionKind = SessionKind.INTERACTIVE
    principal_id: str = ""
    parent_session_id: Optional[str] = None      # None only for PRIMORDIAL
    state: SessionState = SessionState.INITIALIZING
    space_id: str = ""                            # active Space context
    display_name: str = ""
    process_pids: List[str] = field(default_factory=list)
    device_token_ids: List[str] = field(default_factory=list)
    child_session_ids: List[str] = field(default_factory=list)
    omnifield_state: Dict[str, Any] = field(default_factory=dict)  # GAIA's awareness snapshot
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    activated_at: Optional[str] = None
    closed_at: Optional[str] = None

    # Persistence flags
    persist_on_close: bool = False    # write session state to disk on close
    restore_on_boot: bool = False     # auto-restore on next GAIA boot

    def is_primordial(self) -> bool:
        return self.kind == SessionKind.PRIMORDIAL

    def is_active(self) -> bool:
        return self.state in (SessionState.ACTIVE, SessionState.PRIMORDIAL)

    def activate(self) -> None:
        self.state = SessionState.PRIMORDIAL if self.is_primordial() else SessionState.ACTIVE
        self.activated_at = _utcnow()

    def lock(self) -> None:
        if not self.is_primordial():
            self.state = SessionState.LOCKED

    def unlock(self) -> None:
        if self.state == SessionState.LOCKED:
            self.state = SessionState.ACTIVE

    def close(self) -> None:
        if not self.is_primordial():
            self.state = SessionState.CLOSED
            self.closed_at = _utcnow()

    def register_process(self, pid: str) -> None:
        if pid not in self.process_pids:
            self.process_pids.append(pid)

    def deregister_process(self, pid: str) -> None:
        self.process_pids = [p for p in self.process_pids if p != pid]

    def register_device_token(self, token_id: str) -> None:
        if token_id not in self.device_token_ids:
            self.device_token_ids.append(token_id)

    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "kind": self.kind.value,
            "principal_id": self.principal_id,
            "parent_session_id": self.parent_session_id,
            "state": self.state.value,
            "space_id": self.space_id,
            "display_name": self.display_name,
            "processes": len(self.process_pids),
            "children": len(self.child_session_ids),
            "persist": self.persist_on_close,
            "restore": self.restore_on_boot,
        }
