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

── Pre-Authorization Extension ──────────────────────────────────────────────
Adds scope-aware pre-authorization so the AgenticLoop can resolve C01/C30
collisions when the Gaian is offline:

  Canon C01: No irreversible action without Gaian consent.
  Canon C30: No runaway loops; the system must be able to act decisively.

Resolution: The Gaian grants standing pre-authorization for defined scopes
(action pattern + risk tier ceiling + time window + session mode constraints).
The ActionGate checks pre-auth *before* requiring live Gaian presence.
Milestone-flagged records are always excluded from autonomous scope — C01 hard.
"""

import fnmatch
import hashlib
import json
import datetime
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Risk tier enumeration (mirrors ActionGate tiers)
# ─────────────────────────────────────────────────────────────────────────────

class RiskTier(int, Enum):
    """
    Action risk tiers, mirroring ActionGate's tier model.
    Pre-auth records declare a ceiling — they never authorize above it.
    """
    TIER_1 = 1   # Read-only, non-sensitive
    TIER_2 = 2   # Write, reversible, personal data
    TIER_3 = 3   # Irreversible, Canon-significant — live consent required
    TIER_4 = 4   # Systemic / cross-Gaian — always live consent required


# ─────────────────────────────────────────────────────────────────────────────
# Existing ConsentRecord (unchanged — backward compatible)
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Pre-Authorization Scope
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PreAuthScope:
    """
    Declares *what* the Gaian pre-authorizes.

    action_pattern
        Glob or exact string matched against the action name.
        Examples:
          "delete_emotional_cache"           exact match
          "delete_*_cache"                   glob — any cache deletion
          "fetch_*"                          all fetch operations
          "*"                                everything at or below tier ceiling
                                             (use with extreme caution)

    tier_ceiling
        Maximum RiskTier this scope covers. Actions above the ceiling
        are NEVER resolved by pre-auth — they always require live consent.
        Default: TIER_2.

    exclude_canon_milestones
        If True (default), any action flagged as touching Canon milestone
        records is excluded from this scope — C01 hard boundary.

    allowed_session_modes
        If set, pre-auth only applies during these session modes.
        None means all modes are allowed.
        Example: ["autonomous_maintenance", "background"]

    allowed_time_window
        Optional (start_hour, end_hour) UTC tuple.
        Pre-auth only resolves within this window.
        Example: (2, 6) allows autonomous action between 02:00–06:00 UTC.

    description
        Human-readable explanation shown to the Gaian in the consent UI.
    """
    action_pattern: str
    tier_ceiling: RiskTier = RiskTier.TIER_2
    exclude_canon_milestones: bool = True
    allowed_session_modes: Optional[list[str]] = None
    allowed_time_window: Optional[tuple[int, int]] = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "action_pattern": self.action_pattern,
            "tier_ceiling": self.tier_ceiling.value,
            "exclude_canon_milestones": self.exclude_canon_milestones,
            "allowed_session_modes": self.allowed_session_modes,
            "allowed_time_window": (
                list(self.allowed_time_window)
                if self.allowed_time_window else None
            ),
            "description": self.description,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Pre-Authorization Record
# ─────────────────────────────────────────────────────────────────────────────

class PreAuthRecord:
    """
    A living pre-authorization granted by the Gaian.
    Wraps a PreAuthScope with lifecycle management:
    validity, revocation, usage tracking, and cryptographic ID.
    """

    def __init__(
        self,
        gaian_id: str,
        scope: PreAuthScope,
        granted_at: str,
        expires_at: Optional[str] = None,
        label: str = "",
    ):
        self.gaian_id = gaian_id
        self.scope = scope
        self.granted_at = granted_at
        self.expires_at = expires_at
        self.label = label or scope.description or scope.action_pattern
        self.revoked = False
        self.revoked_at: Optional[str] = None
        self.use_count = 0
        self.last_used_at: Optional[str] = None
        self.record_id = self._compute_id()

    def _compute_id(self) -> str:
        payload = (
            f"{self.gaian_id}:{self.scope.action_pattern}"
            f":{self.scope.tier_ceiling.value}:{self.granted_at}"
        )
        return "CL-" + hashlib.sha256(payload.encode()).hexdigest()[:12].upper()

    def is_valid(self) -> bool:
        """Check lifecycle validity (not scope match — see match())."""
        if self.revoked:
            return False
        if self.expires_at:
            now = datetime.datetime.utcnow().isoformat()
            if now > self.expires_at:
                return False
        return True

    def match(
        self,
        action: str,
        tier: RiskTier,
        session_mode: str = "default",
        has_canon_milestone: bool = False,
    ) -> tuple[bool, str]:
        """
        Test whether this record authorizes the given action.

        Returns (matched: bool, reason: str).
        Reason is always populated — consumed by ActionGate for audit logs.
        """
        if not self.is_valid():
            return False, f"PreAuth {self.record_id} is expired or revoked."

        # Tier ceiling check — hard boundary
        if tier.value > self.scope.tier_ceiling.value:
            return False, (
                f"Action tier {tier.name} exceeds pre-auth ceiling "
                f"{self.scope.tier_ceiling.name} on {self.record_id}."
            )

        # Canon milestone exclusion — C01 hard boundary
        if has_canon_milestone and self.scope.exclude_canon_milestones:
            return False, (
                f"Action touches Canon milestone records. "
                f"Pre-auth {self.record_id} excludes milestone scope — live consent required."
            )

        # Session mode constraint
        if self.scope.allowed_session_modes is not None:
            if session_mode not in self.scope.allowed_session_modes:
                return False, (
                    f"Session mode '{session_mode}' not in pre-auth allowed modes "
                    f"{self.scope.allowed_session_modes} on {self.record_id}."
                )

        # Time window constraint (UTC)
        if self.scope.allowed_time_window is not None:
            start_h, end_h = self.scope.allowed_time_window
            current_h = datetime.datetime.utcnow().hour
            in_window = (
                start_h <= current_h < end_h
                if start_h <= end_h
                else current_h >= start_h or current_h < end_h  # overnight window
            )
            if not in_window:
                return False, (
                    f"Current UTC hour {current_h} outside pre-auth window "
                    f"{start_h}–{end_h} on {self.record_id}."
                )

        # Action pattern match (glob)
        if not fnmatch.fnmatch(action, self.scope.action_pattern):
            return False, (
                f"Action '{action}' does not match pattern "
                f"'{self.scope.action_pattern}' on {self.record_id}."
            )

        # All checks passed
        return True, (
            f"Pre-authorized by {self.record_id} "
            f"(pattern='{self.scope.action_pattern}', tier={tier.name})."
        )

    def _record_use(self) -> None:
        self.use_count += 1
        self.last_used_at = datetime.datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "gaian_id": self.gaian_id,
            "label": self.label,
            "scope": self.scope.to_dict(),
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at,
            "use_count": self.use_count,
            "last_used_at": self.last_used_at,
            "valid": self.is_valid(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# PreAuthMatch — structured result for ActionGate consumption
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PreAuthMatch:
    """
    Returned by ConsentLedger.check_preauth().
    ActionGate reads .matched to decide; .reason goes into the audit log.
    """
    matched: bool
    record: Optional[PreAuthRecord] = None
    reason: str = ""

    @property
    def record_id(self) -> Optional[str]:
        return self.record.record_id if self.record else None


# ─────────────────────────────────────────────────────────────────────────────
# ConsentLedger (extended — backward compatible)
# ─────────────────────────────────────────────────────────────────────────────

class ConsentLedger:
    """
    Append-only consent ledger. Records all consent grants, renewals,
    and revocations. Every write is permanent — the ledger never forgets,
    even when consent is revoked (revocation is its own ledger entry).

    This is the audit surface for GAIA's consent governance.

    ── Pre-Authorization API (new) ──────────────────────────────────────────
    Gaians can grant standing pre-authorizations for defined action scopes.
    The AgenticLoop and ActionGate check pre-auth before requiring live
    Gaian presence — resolving the C01/C30 canonical collision.

    Pre-auth never overrides TIER_3+ or Canon milestone protections.
    Those always require live, present Gaian consent.
    """

    def __init__(self):
        self._ledger: list = []        # Immutable append-only log
        self._active: dict = {}        # gaian_id -> {purpose -> ConsentRecord}
        self._preauth: dict = {}       # gaian_id -> [PreAuthRecord]

    # ── Existing API (unchanged) ──────────────────────────────────────────

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

    def check(self, party_id: str, purpose: str, action: str = "", tier: Optional[RiskTier] = None, session_mode: str = "default", has_canon_milestone: bool = False) -> bool:
        """
        Check if valid consent exists.
        Extended: also resolves pre-auth scopes when action + tier are provided.
        Backward compatible — original signature (party_id, purpose) still works.
        """
        # Original purpose-level check
        record = self._active.get(party_id, {}).get(purpose)
        if record and record.is_valid():
            return True

        # Extended: pre-auth scope check
        if action and tier is not None:
            match = self.check_preauth(
                gaian_id=party_id,
                action=action,
                tier=tier,
                session_mode=session_mode,
                has_canon_milestone=has_canon_milestone,
            )
            return match.matched

        return False

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

    # ── Pre-Authorization API (new) ───────────────────────────────────────

    def preauthorize(
        self,
        gaian_id: str,
        scope: PreAuthScope,
        duration_days: Optional[int] = 180,
        label: str = "",
    ) -> PreAuthRecord:
        """
        Gaian grants standing pre-authorization for an action scope.

        This is the *only* way pre-auth records are created.
        The Gaian must be present and authenticated to call this.
        (Authentication is enforced at the API/route layer, not here.)

        Parameters
        ----------
        gaian_id:
            The sovereign Gaian granting this authorization.
        scope:
            PreAuthScope defining what is authorized (pattern, tier, constraints).
        duration_days:
            How long this pre-auth is valid. None = no expiry (not recommended).
            Default: 180 days.
        label:
            Human-readable name shown in the Gaian's consent dashboard.

        Returns
        -------
        PreAuthRecord with a cryptographic record_id (e.g. CL-A3F7C2...).

        Example
        -------
        ledger.preauthorize(
            gaian_id="r0gv3",
            scope=PreAuthScope(
                action_pattern="delete_*_cache",
                tier_ceiling=RiskTier.TIER_2,
                exclude_canon_milestones=True,
                allowed_session_modes=["autonomous_maintenance"],
                allowed_time_window=(2, 6),
                description="Auto-delete non-milestone cache during maintenance window",
            ),
            duration_days=180,
            label="Nightly cache cleanup",
        )
        """
        now = datetime.datetime.utcnow().isoformat()
        expires = None
        if duration_days:
            expires = (
                datetime.datetime.utcnow()
                + datetime.timedelta(days=duration_days)
            ).isoformat()

        record = PreAuthRecord(
            gaian_id=gaian_id,
            scope=scope,
            granted_at=now,
            expires_at=expires,
            label=label,
        )

        # Append to ledger (immutable)
        self._ledger.append({
            "event": "preauth_grant",
            "record": record.to_dict(),
        })

        # Store in active pre-auth index
        if gaian_id not in self._preauth:
            self._preauth[gaian_id] = []
        self._preauth[gaian_id].append(record)

        return record

    def check_preauth(
        self,
        gaian_id: str,
        action: str,
        tier: RiskTier,
        session_mode: str = "default",
        has_canon_milestone: bool = False,
    ) -> PreAuthMatch:
        """
        Check whether any pre-authorization covers the requested action.

        Called by ActionGate before requiring live Gaian presence.
        Returns a PreAuthMatch with .matched, .record, and .reason.

        The first matching record is returned. Records are evaluated in
        grant order (oldest first) — most specific patterns should be
        granted before broad glob patterns.

        Parameters
        ----------
        gaian_id:
            The Gaian whose pre-auths to check.
        action:
            The exact action name being requested (e.g. "delete_emotional_cache").
        tier:
            The RiskTier of the action as assessed by ActionGate.
        session_mode:
            Current loop session mode (e.g. "autonomous_maintenance").
        has_canon_milestone:
            True if the action touches Canon milestone records.
            This flag causes all records with exclude_canon_milestones=True to deny.

        Returns
        -------
        PreAuthMatch
            .matched  — True if pre-auth covers this action
            .record   — the matching PreAuthRecord (or None)
            .reason   — human-readable audit string
        """
        # TIER_3+ is never resolvable by pre-auth — C01 hard boundary
        if tier.value >= RiskTier.TIER_3.value:
            return PreAuthMatch(
                matched=False,
                reason=(
                    f"Action tier {tier.name} is at or above TIER_3. "
                    "Pre-authorization cannot substitute for live Gaian consent."
                ),
            )

        records = self._preauth.get(gaian_id, [])
        if not records:
            return PreAuthMatch(
                matched=False,
                reason=f"No pre-authorizations found for gaian_id='{gaian_id}'.",
            )

        # Evaluate each record; collect denial reasons for audit log
        denial_reasons: list[str] = []
        for record in records:
            matched, reason = record.match(
                action=action,
                tier=tier,
                session_mode=session_mode,
                has_canon_milestone=has_canon_milestone,
            )
            if matched:
                record._record_use()
                self._ledger.append({
                    "event": "preauth_used",
                    "record_id": record.record_id,
                    "action": action,
                    "tier": tier.name,
                    "session_mode": session_mode,
                    "has_canon_milestone": has_canon_milestone,
                    "at": datetime.datetime.utcnow().isoformat(),
                })
                return PreAuthMatch(matched=True, record=record, reason=reason)
            denial_reasons.append(reason)

        return PreAuthMatch(
            matched=False,
            reason=(
                f"No pre-auth matched action='{action}' tier={tier.name}. "
                f"Denial reasons: {' | '.join(denial_reasons)}"
            ),
        )

    def revoke_preauth(self, gaian_id: str, record_id: str) -> bool:
        """
        Revoke a specific pre-authorization by its record_id.
        Revocation is immediate and appended to the ledger.
        Returns True if found and revoked.
        """
        for record in self._preauth.get(gaian_id, []):
            if record.record_id == record_id and not record.revoked:
                record.revoked = True
                record.revoked_at = datetime.datetime.utcnow().isoformat()
                self._ledger.append({
                    "event": "preauth_revoke",
                    "record": record.to_dict(),
                })
                return True
        return False

    def list_preauth(
        self,
        gaian_id: str,
        include_expired: bool = False,
    ) -> list[dict]:
        """
        List all pre-authorizations for a Gaian.
        Used by the consent dashboard to show the Gaian what they've granted.

        Parameters
        ----------
        gaian_id:
            The Gaian whose pre-auths to list.
        include_expired:
            If True, includes expired and revoked records.
            Default: False (active only).
        """
        records = self._preauth.get(gaian_id, [])
        if not include_expired:
            records = [r for r in records if r.is_valid()]
        return [r.to_dict() for r in records]

    def audit_preauth_usage(
        self,
        gaian_id: str,
    ) -> list[dict]:
        """
        Return all preauth_used ledger events for a Gaian.
        Feeds the sovereignty audit dashboard — Gaian can see
        exactly when and why pre-auth was invoked autonomously.
        """
        return [
            entry for entry in self._ledger
            if entry.get("event") == "preauth_used"
            and self._preauth.get(gaian_id)
            and any(
                r.record_id == entry.get("record_id")
                for r in self._preauth.get(gaian_id, [])
            )
        ]
