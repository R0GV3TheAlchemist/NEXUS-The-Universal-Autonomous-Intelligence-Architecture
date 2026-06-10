"""
core/consent_ledger.py
Consent Ledger — tracks user consent events for GAIA.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class ConsentStatus(str, Enum):
    """Current consent status for a given gaian+scope pair."""
    GRANTED  = "granted"
    REVOKED  = "revoked"
    NOT_SET  = "not_set"


# Legacy alias kept for backwards compatibility
class ConsentAction(str, Enum):
    GRANT  = "grant"
    REVOKE = "revoke"
    UPDATE = "update"


class ConsentScope(str, Enum):
    """Scopes of consent that can be granted or revoked."""
    EMOTIONAL_DATA    = "emotional_data"
    MEMORY_RETENTION  = "memory_retention"
    MEMORY_WRITE      = "memory_write"
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
    # Supports both old 'user_id' and new 'gaian_id' field names
    gaian_id:   str
    scope:      ConsentScope
    status:     ConsentStatus = ConsentStatus.GRANTED
    granted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    revoked_at: Optional[str] = None
    metadata:   dict = field(default_factory=dict)

    # back-compat alias
    @property
    def user_id(self) -> str:
        return self.gaian_id

    @property
    def is_active(self) -> bool:
        return self.status == ConsentStatus.GRANTED and self.revoked_at is None

    def to_dict(self) -> dict:
        return {
            "gaian_id":   self.gaian_id,
            "scope":      self.scope.value if isinstance(self.scope, ConsentScope) else self.scope,
            "status":     self.status.value,
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

    def grant(
        self,
        gaian_id: Optional[str] = None,
        scope: Optional[ConsentScope] = None,
        # legacy keyword
        user_id: Optional[str] = None,
        **meta,
    ) -> ConsentEntry:
        gid = gaian_id or user_id or ""
        e = ConsentEntry(
            gaian_id=gid,
            scope=scope,  # type: ignore[arg-type]
            status=ConsentStatus.GRANTED,
            metadata=dict(meta),
        )
        self.record(e)
        return e

    def revoke(
        self,
        gaian_id: Optional[str] = None,
        scope: Optional[ConsentScope] = None,
        user_id: Optional[str] = None,
    ) -> None:
        gid = gaian_id or user_id or ""
        ts = datetime.now(timezone.utc).isoformat()
        for e in reversed(self._entries):
            if e.gaian_id == gid and e.scope == scope and e.status == ConsentStatus.GRANTED:
                e.revoked_at = ts
                e.status = ConsentStatus.REVOKED
                break

    def check(
        self,
        gaian_id: Optional[str] = None,
        scope: Optional[ConsentScope] = None,
        user_id: Optional[str] = None,
    ) -> ConsentStatus:
        gid = gaian_id or user_id or ""
        for e in reversed(self._entries):
            if e.gaian_id == gid and e.scope == scope:
                return e.status
        return ConsentStatus.NOT_SET

    def is_permitted(
        self,
        gaian_id: Optional[str] = None,
        scope: Optional[ConsentScope] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        status = self.check(gaian_id=gaian_id, scope=scope, user_id=user_id)
        return status == ConsentStatus.GRANTED

    # Legacy method name
    def is_consented(self, user_id: str, scope: str) -> bool:
        return self.is_permitted(gaian_id=user_id, scope=scope)  # type: ignore[arg-type]

    def history(self, gaian_id: Optional[str] = None) -> List[ConsentEntry]:
        if gaian_id:
            return [e for e in self._entries if e.gaian_id == gaian_id]
        return list(self._entries)


_ledger: Optional[ConsentLedger] = None


def get_consent_ledger() -> ConsentLedger:
    global _ledger
    if _ledger is None:
        _ledger = ConsentLedger()
    return _ledger
