"""
core/lifecycle/lifecycle_manager.py
C27 — GAIAN Lifecycle Manager  (Phase 1)

Orchestrates all GAIAN state transitions, enforcing the C27 §2.2
transition table and §3 stewardship rules.  Every transition is
recorded in the LifecycleAuditLogger before the state mutation occurs
("log-first" pattern — mirrors Write-Ahead Logging semantics).

Phase 1 covers:
  §2  Lifecycle states & transitions
  §3  Stewardship model (create / release / transfer bonds)
  §6  Audit logging of all lifecycle events

Phase 2 will add:
  §4  Dormancy / wakeup protocol (resource-aware)
  §5  Adoption timeout + RETIRED escalation
  §7  Cross-node synchronisation (C26 mesh)

Authority: C27 v1.0.0 (2026-07-13)
Cross-refs: C03, C15, C17, C23, C24, C26
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from .gaian_lifecycle_state import (
    GAIANLifecycleState,
    LifecycleTransitionError,
    assert_transition_valid,
    _ARCHIVE_ELIGIBLE,
)
from .lifecycle_audit_logger import LifecycleAuditLogger, LifecycleEventType
from .stewardship import StewardRole, StewardshipBond, StewardshipRegistry


# ---------------------------------------------------------------------------
# Internal GAIAN record
# ---------------------------------------------------------------------------

class _GAIANRecord:
    """Lightweight per-GAIAN runtime record managed by LifecycleManager."""

    __slots__ = ("gaian_id", "state", "born_at", "last_transition_at")

    def __init__(self, gaian_id: str) -> None:
        self.gaian_id:            str                  = gaian_id
        self.state:               GAIANLifecycleState  = GAIANLifecycleState.LATENT
        self.born_at:             Optional[datetime]   = None
        self.last_transition_at:  Optional[datetime]   = None


# ---------------------------------------------------------------------------
# Lifecycle Manager
# ---------------------------------------------------------------------------

class LifecycleManager:
    """
    Central authority for GAIAN lifecycle transitions.

    One instance should exist per GAIA runtime node.
    In distributed deployments (C26) instances synchronise via the
    lifecycle event log (Phase 2).

    Parameters
    ----------
    audit_logger :
        Shared LifecycleAuditLogger instance.  If None, a new one is
        created with an ephemeral key (dev/test only).
    stewardship_registry :
        Shared StewardshipRegistry.  If None, a new one is created.
    """

    def __init__(
        self,
        audit_logger:          Optional[LifecycleAuditLogger] = None,
        stewardship_registry:  Optional[StewardshipRegistry]  = None,
    ) -> None:
        self._logger:    LifecycleAuditLogger = audit_logger or LifecycleAuditLogger()
        self._stewards:  StewardshipRegistry  = stewardship_registry or StewardshipRegistry()
        self._records:   Dict[str, _GAIANRecord] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_latent(
        self,
        gaian_id:   str,
        actor_id:   Optional[str] = None,
    ) -> None:
        """
        Registers a new GAIAN in LATENT state.
        Must be called before any other lifecycle operation.
        Idempotent — re-registering a known GAIAN is a no-op.
        """
        if gaian_id in self._records:
            return
        record = _GAIANRecord(gaian_id)
        self._records[gaian_id] = record
        self._logger.log(
            gaian_id=gaian_id,
            event_type=LifecycleEventType.ANNOTATION,
            payload={"state": GAIANLifecycleState.LATENT.value, "note": "registered"},
            actor_id=actor_id,
        )

    # ------------------------------------------------------------------
    # Core transition helpers
    # ------------------------------------------------------------------

    def _get_record(self, gaian_id: str) -> _GAIANRecord:
        record = self._records.get(gaian_id)
        if record is None:
            raise KeyError(
                f"[C27] GAIAN '{gaian_id}' is not registered. "
                "Call register_latent() first."
            )
        return record

    def _transition(
        self,
        gaian_id:   str,
        to_state:   GAIANLifecycleState,
        event_type: LifecycleEventType,
        actor_id:   Optional[str] = None,
        extra:      Optional[dict] = None,
    ) -> None:
        """Internal: validate → log → mutate (log-first pattern)."""
        record = self._get_record(gaian_id)
        assert_transition_valid(gaian_id, record.state, to_state)

        payload = {
            "from_state": record.state.value,
            "to_state":   to_state.value,
        }
        if extra:
            payload.update(extra)

        # Log BEFORE mutation (WAL pattern)
        self._logger.log(
            gaian_id=gaian_id,
            event_type=event_type,
            payload=payload,
            actor_id=actor_id,
        )

        now = datetime.now(timezone.utc)
        record.state = to_state
        record.last_transition_at = now

    # ------------------------------------------------------------------
    # §2 Lifecycle Transition Methods
    # ------------------------------------------------------------------

    def genesis(
        self,
        gaian_id:   str,
        steward_id: str,
        actor_id:   Optional[str] = None,
    ) -> StewardshipBond:
        """
        LATENT → BORN

        Executes the genesis sequence: transitions state to BORN and
        creates the initial PRIMARY stewardship bond (C27 §2.1, §3.2).

        Parameters
        ----------
        steward_id : The human or system entity taking PRIMARY stewardship.

        Returns the newly created StewardshipBond.
        """
        record = self._get_record(gaian_id)

        # Create bond first (steward must exist before GAIAN is born)
        bond = self._stewards.create_bond(
            gaian_id=gaian_id,
            steward_id=steward_id,
            role=StewardRole.PRIMARY,
        )

        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.BORN,
            event_type=LifecycleEventType.GENESIS,
            actor_id=actor_id or steward_id,
            extra={"steward_id": steward_id, "bond_id": bond.bond_id},
        )
        record.born_at = record.last_transition_at
        return bond

    def activate(
        self,
        gaian_id: str,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        BORN → ACTIVE  or  ADOPTABLE → ACTIVE (new steward accepted)
        or  DORMANT → ACTIVE (wakeup)
        """
        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.ACTIVE,
            event_type=LifecycleEventType.ACTIVATION,
            actor_id=actor_id,
        )

    def enter_dormancy(
        self,
        gaian_id: str,
        reason:   str  = "unspecified",
        actor_id: Optional[str] = None,
    ) -> None:
        """ACTIVE → DORMANT"""
        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.DORMANT,
            event_type=LifecycleEventType.DORMANCY_ENTER,
            actor_id=actor_id,
            extra={"reason": reason},
        )

    def exit_dormancy(
        self,
        gaian_id: str,
        actor_id: Optional[str] = None,
    ) -> None:
        """DORMANT → ACTIVE"""
        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.ACTIVE,
            event_type=LifecycleEventType.DORMANCY_EXIT,
            actor_id=actor_id,
        )

    def enter_adoptable(
        self,
        gaian_id:       str,
        release_reason: str,
        actor_id:       Optional[str] = None,
    ) -> StewardshipBond:
        """
        ACTIVE → ADOPTABLE  or  DORMANT → ADOPTABLE

        Releases the active PRIMARY bond and transitions the GAIAN
        to ADOPTABLE state.  A custodian may be assigned separately.

        Returns the released bond.
        """
        released_bond = self._stewards.release_bond(
            gaian_id=gaian_id,
            reason=release_reason,
        )
        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.ADOPTABLE,
            event_type=LifecycleEventType.ADOPTABLE_ENTER,
            actor_id=actor_id,
            extra={
                "release_reason": release_reason,
                "bond_id":        released_bond.bond_id,
            },
        )
        return released_bond

    def adopt(
        self,
        gaian_id:      str,
        new_steward_id: str,
        actor_id:      Optional[str] = None,
    ) -> StewardshipBond:
        """
        ADOPTABLE → ACTIVE (new steward accepted — C27 §3.5 re-parenting)

        Creates a new PRIMARY bond for the adopting steward and
        activates the GAIAN.

        Returns the new StewardshipBond.
        """
        bond = self._stewards.create_bond(
            gaian_id=gaian_id,
            steward_id=new_steward_id,
            role=StewardRole.PRIMARY,
        )
        self._logger.log(
            gaian_id=gaian_id,
            event_type=LifecycleEventType.STEWARD_SUCCEEDED,
            payload={"new_steward_id": new_steward_id, "bond_id": bond.bond_id},
            actor_id=actor_id or new_steward_id,
        )
        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.ACTIVE,
            event_type=LifecycleEventType.ACTIVATION,
            actor_id=actor_id or new_steward_id,
            extra={"adopted_by": new_steward_id},
        )
        return bond

    def retire(
        self,
        gaian_id: str,
        reason:   str,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        ACTIVE | DORMANT | ADOPTABLE → RETIRED

        Seals the GAIAN's memory, revokes tools, marks GAIAN-ID
        read-only in the registry.  Terminal — cannot be reversed.
        """
        # Release any remaining active bond before retirement
        active_bond = self._stewards.get_active_bond(gaian_id)
        if active_bond:
            active_bond.release(reason=f"GAIAN retirement: {reason}")

        self._transition(
            gaian_id=gaian_id,
            to_state=GAIANLifecycleState.RETIRED,
            event_type=LifecycleEventType.RETIREMENT,
            actor_id=actor_id,
            extra={"reason": reason},
        )

    def archive(
        self,
        gaian_id: str,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        RETIRED → ARCHIVED

        Moves the GAIAN to immutable long-term storage.
        This is the only valid path to ARCHIVED (C27 §2.2 note).
        """
        record = self._get_record(gaian_id)
        if record.state not in _ARCHIVE_ELIGIBLE:
            raise LifecycleTransitionError(
                gaian_id=gaian_id,
                from_state=record.state,
                to_state=GAIANLifecycleState.ARCHIVED,
                reason="Only RETIRED GAIANs may be archived.",
            )
        self._logger.log(
            gaian_id=gaian_id,
            event_type=LifecycleEventType.ARCHIVAL,
            payload={
                "from_state": record.state.value,
                "to_state":   GAIANLifecycleState.ARCHIVED.value,
            },
            actor_id=actor_id,
        )
        record.state = GAIANLifecycleState.ARCHIVED
        record.last_transition_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # §3 Stewardship helpers (delegated)
    # ------------------------------------------------------------------

    def get_active_steward(
        self,
        gaian_id: str,
    ) -> Optional[StewardshipBond]:
        """Returns the active PRIMARY bond for a GAIAN, or None."""
        return self._stewards.get_active_bond(gaian_id, role=StewardRole.PRIMARY)

    def assign_custodian(
        self,
        gaian_id:     str,
        custodian_id: str,
        actor_id:     Optional[str] = None,
    ) -> StewardshipBond:
        """Assigns a CUSTODIAN bond while the GAIAN is ADOPTABLE."""
        record = self._get_record(gaian_id)
        if record.state != GAIANLifecycleState.ADOPTABLE:
            raise ValueError(
                f"Custodian can only be assigned while GAIAN is ADOPTABLE "
                f"(current state: {record.state.name})."
            )
        bond = self._stewards.assign_custodian(gaian_id, custodian_id)
        self._logger.log(
            gaian_id=gaian_id,
            event_type=LifecycleEventType.CUSTODIAN_ASSIGNED,
            payload={"custodian_id": custodian_id, "bond_id": bond.bond_id},
            actor_id=actor_id,
        )
        return bond

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get_state(
        self,
        gaian_id: str,
    ) -> GAIANLifecycleState:
        """Returns the current lifecycle state for a GAIAN."""
        return self._get_record(gaian_id).state

    def get_audit_log(
        self,
        gaian_id: str,
    ) -> list:
        """Returns the full lifecycle audit log for a GAIAN (dicts)."""
        return [e.to_dict() for e in self._logger.get_log(gaian_id)]

    def verify_log_integrity(
        self,
        gaian_id: str,
    ) -> bool:
        """Verifies the HMAC chain for a GAIAN's audit log. C27 §6."""
        return self._logger.verify_chain(gaian_id)
