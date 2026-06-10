"""
Consent Ledger — tracks user consent events across GAIA-OS.

This module re-exports the ConsentLedger class and provides
the get_consent_ledger() singleton accessor expected by tests
and other modules.

Full implementation lives in the body of the class below;
this file is the canonical entry-point.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    REVOKED = "revoked"
    PENDING = "pending"
    EXPIRED = "expired"


class ConsentScope(str, Enum):
    DATA_PROCESSING = "data_processing"
    MEMORY_STORAGE = "memory_storage"
    BIOMETRIC = "biometric"
    EMOTIONAL = "emotional"
    FULL = "full"


@dataclass
class ConsentRecord:
    """A single consent decision record."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    scope: ConsentScope = ConsentScope.DATA_PROCESSING
    status: ConsentStatus = ConsentStatus.PENDING
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)

    def is_active(self) -> bool:
        if self.status != ConsentStatus.GRANTED:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "scope": self.scope.value,
            "status": self.status.value,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


class ConsentLedger:
    """Immutable audit ledger for consent events."""

    def __init__(self) -> None:
        self._records: Dict[str, List[ConsentRecord]] = {}
        log.info("ConsentLedger initialised")

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    def grant(
        self,
        user_id: str,
        scope: ConsentScope,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> ConsentRecord:
        record = ConsentRecord(
            user_id=user_id,
            scope=scope,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._records.setdefault(user_id, []).append(record)
        log.info("Consent GRANTED user=%s scope=%s", user_id, scope)
        return record

    def revoke(self, user_id: str, scope: ConsentScope) -> Optional[ConsentRecord]:
        for record in reversed(self._records.get(user_id, [])):
            if record.scope == scope and record.status == ConsentStatus.GRANTED:
                record.status = ConsentStatus.REVOKED
                record.revoked_at = datetime.now(timezone.utc)
                log.info("Consent REVOKED user=%s scope=%s", user_id, scope)
                return record
        return None

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    def check_consent(self, user_id: str, scope: ConsentScope) -> bool:
        for record in reversed(self._records.get(user_id, [])):
            if record.scope == scope:
                return record.is_active()
        return False

    def get_records(self, user_id: str) -> List[ConsentRecord]:
        return list(self._records.get(user_id, []))

    def get_all_records(self) -> List[ConsentRecord]:
        return [r for records in self._records.values() for r in records]

    def to_dict(self) -> dict:
        return {
            uid: [r.to_dict() for r in records]
            for uid, records in self._records.items()
        }


# ------------------------------------------------------------------ #
#  Singleton accessor                                                  #
# ------------------------------------------------------------------ #

_consent_ledger: Optional[ConsentLedger] = None


def get_consent_ledger() -> ConsentLedger:
    """Return the module-level singleton ConsentLedger."""
    global _consent_ledger
    if _consent_ledger is None:
        _consent_ledger = ConsentLedger()
    return _consent_ledger
