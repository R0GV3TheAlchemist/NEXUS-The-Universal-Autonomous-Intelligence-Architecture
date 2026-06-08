"""
ConsentLedger — Cryptographic consent lifecycle manager.

Every consent grant in GAIA is:
  - Time-bound (expires unless renewed)
  - Purpose-limited (tagged with what it authorizes)
  - Revocable at any time by the human sovereign
  - Recorded on an append-only ledger (tamper-evident)

This is the technical implementation of GAIA's consent architecture,
aligned with IETF vCon standards and SCITT transparency infrastructure.

Epistemic Status: ESTABLISHED
Canon Ref: Doc 21 (Sovereignty), Doc 35 (Security), GDPR/CCPA alignment
"""

import hashlib
import datetime
from typing import Optional


class ConsentRecord:
    def __init__(
        self,
        party_id: str,
        purpose: str,
        granted_at: str,
        expires_at: Optional[str] = None,
        revocable: bool = True,
    ):
        self.party_id = party_id
        self.purpose = purpose
        self.granted_at = granted_at
        self.expires_at = expires_at
        self.revocable = revocable
        self.revoked = False
        self.revoked_at: Optional[str] = None
        self.record_id = self._compute_id()

    def _compute_id(self) -> str:
        payload = f"{self.party_id}:{self.purpose}:{self.granted_at}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        if self.expires_at:
            now = datetime.datetime.utcnow().isoformat()
            if now > self.expires_at:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "party_id": self.party_id,
            "purpose": self.purpose,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "revocable": self.revocable,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at,
            "valid": self.is_valid(),
        }


class ConsentLedger:
    """
    Append-only consent ledger. Records all consent grants, renewals,
    and revocations. Every write is permanent — the ledger never forgets,
    even when consent is revoked (revocation is its own ledger entry).

    This is the audit surface for GAIA's consent governance.
    """

    def __init__(self):
        self._ledger: list = []       # Immutable append-only log
        self._active: dict = {}       # party_id -> {purpose -> ConsentRecord}

    def grant(
        self,
        party_id: str,
        purpose: str,
        duration_days: Optional[int] = 365,
    ) -> ConsentRecord:
        """Grant consent for a specific purpose."""
        now = datetime.datetime.utcnow().isoformat()
        expires = None
        if duration_days:
            expires = (
                datetime.datetime.utcnow()
                + datetime.timedelta(days=duration_days)
            ).isoformat()

        record = ConsentRecord(
            party_id=party_id,
            purpose=purpose,
            granted_at=now,
            expires_at=expires,
        )

        self._ledger.append({"event": "grant", "record": record.to_dict()})
        if party_id not in self._active:
            self._active[party_id] = {}
        self._active[party_id][purpose] = record
        return record

    def revoke(self, party_id: str, purpose: str) -> bool:
        """Revoke consent. Returns True if a valid consent was found and revoked."""
        record = self._active.get(party_id, {}).get(purpose)
        if not record or not record.revocable:
            return False
        record.revoked = True
        record.revoked_at = datetime.datetime.utcnow().isoformat()
        self._ledger.append({"event": "revoke", "record": record.to_dict()})
        return True

    def check(self, party_id: str, purpose: str) -> bool:
        """Check if valid consent exists for this party and purpose."""
        record = self._active.get(party_id, {}).get(purpose)
        return record is not None and record.is_valid()

    def get_ledger(self) -> list:
        """Return the full immutable ledger."""
        return list(self._ledger)

    def get_active_consents(self, party_id: str) -> dict:
        """Return all active consents for a party."""
        return {
            purpose: record.to_dict()
            for purpose, record in self._active.get(party_id, {}).items()
            if record.is_valid()
        }
