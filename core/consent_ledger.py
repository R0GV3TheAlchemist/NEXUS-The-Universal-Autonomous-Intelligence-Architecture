"""
core/consent_ledger.py
Consent Ledger — tracks user consent events for GAIA.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class ConsentAction(str, Enum):
    GRANT  = "grant"
    REVOKE = "revoke"
    UPDATE = "update"


class ConsentScope(str, Enum):
    """Scopes of consent that can be granted or revoked."""
    EMOTIONAL_DATA    = "emotional_data"
    MEMORY_RETENTION  = "memory_retention"
    CANON_CITATION    = "canon_citation"
    SOUL_MIRROR       = "soul_mirror"
    SHADOW_WORK       = "shadow_work"
    BIOMETRIC_DATA    = "biometric_data"
    RESEARCH          = "research"
    THIRD_PARTY_SHARE = "third_party_share"
    FULL_PERSONA      = "full_persona"
    MINIMAL           = "minimal"


@dataclass
class ConsentEntry:
    user_id:    str
    scope:      str
    action:     ConsentAction = ConsentAction.GRANT
    granted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    revoked_at: Optional[str] = None
    metadata:   dict = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.action == ConsentAction.GRANT and self.revoked_at is None

    def to_dict(self) -> dict:
        return {
            "user_id":    self.user_id,
            "scope":      self.scope,
            "action":     self.action.value,
            "granted_at": self.granted_at,
            "revoked_at": self.revoked_at,
            "metadata":   self.metadata,
        }


class ConsentLedger:
    """In-memory consent ledger."""

    def __init__(self) -> None:
        self._entries: List[ConsentEntry] = []

    def record(self, entry: ConsentEntry) -> None:
        self._entries.append(entry)

    def grant(self, user_id: str, scope: str, **meta) -> ConsentEntry:
        e = ConsentEntry(
            user_id=user_id,
            scope=scope,
            action=ConsentAction.GRANT,
            metadata=dict(meta),
        )
        self.record(e)
        return e

    def revoke(self, user_id: str, scope: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        for e in reversed(self._entries):
            if e.user_id == user_id and e.scope == scope and e.action == ConsentAction.GRANT:
                e.revoked_at = ts
                e.action = ConsentAction.REVOKE
                break

    def is_consented(self, user_id: str, scope: str) -> bool:
        for e in reversed(self._entries):
            if e.user_id == user_id and e.scope == scope:
                return e.action == ConsentAction.GRANT and e.revoked_at is None
        return False

    def history(self, user_id: Optional[str] = None) -> List[ConsentEntry]:
        if user_id:
            return [e for e in self._entries if e.user_id == user_id]
        return list(self._entries)


_ledger: Optional[ConsentLedger] = None


def get_consent_ledger() -> ConsentLedger:
    global _ledger
    if _ledger is None:
        _ledger = ConsentLedger()
    return _ledger
