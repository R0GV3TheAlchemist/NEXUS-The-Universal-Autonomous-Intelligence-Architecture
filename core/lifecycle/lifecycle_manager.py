"""
core/lifecycle/lifecycle_manager.py
C27 — GAIAN Lifecycle Manager  (Phase 2 hardened)

Changes from Phase 2 commit:
  - Real Ed25519 signing via Ed25519LifecycleSigner + InProcessVault
  - 180-day archival eligibility gate (C27 §8.3)
  - RetirementEngine integration (C27 §8.2): notice period, legacy package
  - trigger_class propagated from all callers
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from .adoption_queue import AdoptionQueue
from .compliance_sentinel import ComplianceSentinel
from .ed25519_audit import CanonicalAuditEntry
from .gaian_lifecycle_state import (
    GAIANLifecycleState,
    LifecycleTransitionError,
    assert_transition_valid,
    _ARCHIVE_ELIGIBLE,
)
from .lifecycle_audit_logger import LifecycleAuditLogger, LifecycleEventType
from .permissions import PermissionEnvelope, PermissionManager
from .retirement_engine import LegacyPackage, RetirementEngine, RetirementReason
from .signing import Ed25519LifecycleSigner, InProcessVault
from .stewardship import StewardRole, StewardshipBond, StewardshipRegistry


class _GAIANRecord:
    __slots__ = (
        "gaian_id", "state", "born_at",
        "last_transition_at", "canonical_audit", "retired_at",
    )

    def __init__(self, gaian_id: str) -> None:
        self.gaian_id:           str                  = gaian_id
        self.state:              GAIANLifecycleState  = GAIANLifecycleState.LATENT
        self.born_at:            Optional[datetime]   = None
        self.last_transition_at: Optional[datetime]   = None
        self.canonical_audit:    list                 = []
        self.retired_at:         Optional[datetime]   = None


class LifecycleManager:
    def __init__(
        self,
        audit_logger:          Optional[LifecycleAuditLogger] = None,
        stewardship_registry:  Optional[StewardshipRegistry]  = None,
        adoption_queue:        Optional[AdoptionQueue]         = None,
        permission_manager:    Optional[PermissionManager]     = None,
        sentinel:              Optional[ComplianceSentinel]    = None,
        retirement_engine:     Optional[RetirementEngine]      = None,
        signer:                Optional[Ed25519LifecycleSigner] = None,
    ) -> None:
        self._logger     = audit_logger           or LifecycleAuditLogger()
        self._stewards   = stewardship_registry   or StewardshipRegistry()
        self._queue      = adoption_queue         or AdoptionQueue()
        self._permissions= permission_manager     or PermissionManager()
        self._sentinel   = sentinel               or ComplianceSentinel()
        self._retirement = retirement_engine      or RetirementEngine()
        self._records: Dict[str, _GAIANRecord] = {}

        if signer is not None:
            self._signer = signer
        else:
            vault = InProcessVault()
            vault.generate_key("lifecycle-default")
            self._signer = Ed25519LifecycleSigner(vault=vault, key_id="lifecycle-default")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_record(self, gaian_id: str) -> _GAIANRecord:
        r = self._records.get(gaian_id)
        if r is None:
            raise KeyError(f"[C27] GAIAN '{gaian_id}' not registered. Call register_latent() first.")
        return r

    def _append_canonical_audit(
        self,
        gaian_id:      str,
        event_type:    str,
        from_state:    Optional[str],
        to_state:      Optional[str],
        trigger_class: str,
        actor_id:      Optional[str],
        justification: Optional[str],
        metadata:      Optional[dict] = None,
    ) -> CanonicalAuditEntry:
        record = self._get_record(gaian_id)
        prior  = record.canonical_audit[-1] if record.canonical_audit else None
        entry  = CanonicalAuditEntry(
            gaian_id=gaian_id,
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            trigger_class=trigger_class,
            actor_id=actor_id,
            justification=justification,
            metadata=metadata or {},
            previous_entry_hash=self._signer.previous_hash(prior),
        )
        entry.signature = self._signer.sign(entry.payload_for_signing())
        record.canonical_audit.append(entry)
        return entry

    def _transition(
        self,
        gaian_id:      str,
        to_state:      GAIANLifecycleState,
        event_type:    LifecycleEventType,
        actor_id:      Optional[str] = None,
        extra:         Optional[dict] = None,
        justification: Optional[str] = None,
        trigger_class: str = "SYSTEM_EVENT",
    ) -> None:
        record = self._get_record(gaian_id)
        self._sentinel.check_transition(gaian_id, record.state, to_state)
        assert_transition_valid(gaian_id, record.state, to_state)
        payload = {"from_state": record.state.value, "to_state": to_state.value}
        if extra:
            payload.update(extra)
        self._logger.log(gaian_id=gaian_id, event_type=event_type, payload=payload, actor_id=actor_id)
        self._append_canonical_audit(
            gaian_id=gaian_id,
            event_type="LIFECYCLE_TRANSITION",
            from_state=record.state.value,
            to_state=to_state.value,
            trigger_class=trigger_class,
            actor_id=actor_id,
            justification=justification,
            metadata=extra or {},
        )
        record.state = to_state
        record.last_transition_at = datetime.now(timezone.utc)
        self._permissions.contract_for_state(gaian_id, to_state)
        self._sentinel.check_audit_log_integrity(gaian_id, self._logger.verify_chain(gaian_id))
        self._sentinel.check_steward_bond_present(
            gaian_id,
            to_state,
            has_primary_bond=self._stewards.get_active_bond(gaian_id, role=StewardRole.PRIMARY) is not None,
        )

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_latent(self, gaian_id: str, actor_id: Optional[str] = None) -> None:
        if gaian_id in self._records:
            return
        self._records[gaian_id] = _GAIANRecord(gaian_id)
        self._logger.log(
            gaian_id=gaian_id,
            event_type=LifecycleEventType.ANNOTATION,
            payload={"state": GAIANLifecycleState.LATENT.value, "note": "registered"},
            actor_id=actor_id,
        )

    # ------------------------------------------------------------------
    # Lifecycle transition methods
    # ------------------------------------------------------------------

    def genesis(self, gaian_id: str, steward_id: str, actor_id: Optional[str] = None) -> StewardshipBond:
        record = self._get_record(gaian_id)
        bond = self._stewards.create_bond(gaian_id=gaian_id, steward_id=steward_id, role=StewardRole.PRIMARY)
        self._transition(
            gaian_id=gaian_id, to_state=GAIANLifecycleState.BORN,
            event_type=LifecycleEventType.GENESIS,
            actor_id=actor_id or steward_id,
            extra={"steward_id": steward_id, "bond_id": bond.bond_id, "canon_reference": "C27"},
            justification=None, trigger_class="STEWARD_ACTION",
        )
        record.born_at = record.last_transition_at
        return bond

    def activate(
        self,
        gaian_id:      str,
        actor_id:      Optional[str] = None,
        justification: Optional[str] = None,
        trigger_class: str = "SYSTEM_EVENT",
    ) -> None:
        self._transition(
            gaian_id, GAIANLifecycleState.ACTIVE, LifecycleEventType.ACTIVATION,
            actor_id, justification=justification, trigger_class=trigger_class,
        )
        self._queue.remove(gaian_id)

    def enter_dormancy(self, gaian_id: str, reason: str = "unspecified", actor_id: Optional[str] = None) -> None:
        self._transition(
            gaian_id, GAIANLifecycleState.DORMANT, LifecycleEventType.DORMANCY_ENTER, actor_id,
            extra={"reason": reason, "canon_reference": "C27"},
            justification=reason,
            trigger_class="STEWARD_ACTION" if actor_id else "SYSTEM_EVENT",
        )

    def exit_dormancy(self, gaian_id: str, actor_id: Optional[str] = None) -> None:
        self._transition(
            gaian_id, GAIANLifecycleState.ACTIVE, LifecycleEventType.DORMANCY_EXIT, actor_id,
            justification="resume from dormancy",
            trigger_class="SYSTEM_EVENT" if actor_id is None else "STEWARD_ACTION",
        )

    def enter_adoptable(
        self,
        gaian_id:          str,
        release_reason:    str,
        actor_id:          Optional[str] = None,
        archetype:         Optional[str] = None,
        elemental_profile: Optional[str] = None,
        capability_summary: Optional[str] = None,
        health_status:     Optional[str] = None,
        known_anomalies:   Optional[list] = None,
    ) -> StewardshipBond:
        released_bond = self._stewards.release_bond(gaian_id=gaian_id, reason=release_reason)
        self._transition(
            gaian_id, GAIANLifecycleState.ADOPTABLE, LifecycleEventType.ADOPTABLE_ENTER, actor_id,
            extra={"release_reason": release_reason, "bond_id": released_bond.bond_id, "canon_reference": "C27"},
            justification=release_reason,
            trigger_class="STEWARD_ACTION" if actor_id else "CANON_PROCESS",
        )
        record = self._get_record(gaian_id)
        self._queue.enqueue(
            gaian_id=gaian_id, archetype=archetype, elemental_profile=elemental_profile,
            capability_summary=capability_summary,
            lifecycle_history_summary={"current_state": record.state.value},
            health_status=health_status, known_anomalies=known_anomalies or [],
        )
        return released_bond

    def adopt(self, gaian_id: str, new_steward_id: str, actor_id: Optional[str] = None) -> StewardshipBond:
        bond = self._stewards.create_bond(gaian_id=gaian_id, steward_id=new_steward_id, role=StewardRole.PRIMARY)
        self._logger.log(
            gaian_id=gaian_id, event_type=LifecycleEventType.STEWARD_SUCCEEDED,
            payload={"new_steward_id": new_steward_id, "bond_id": bond.bond_id},
            actor_id=actor_id or new_steward_id,
        )
        self._append_canonical_audit(
            gaian_id=gaian_id, event_type="STEWARD_ACTION",
            from_state=GAIANLifecycleState.ADOPTABLE.value,
            to_state=GAIANLifecycleState.ACTIVE.value,
            trigger_class="CANON_PROCESS",
            actor_id=actor_id or new_steward_id,
            justification="adoption finalized",
            metadata={"successor_steward_id": new_steward_id, "canon_reference": "C27"},
        )
        self.activate(gaian_id, actor_id=actor_id or new_steward_id, justification="new steward accepted", trigger_class="CANON_PROCESS")
        return bond

    def assign_custodian(self, gaian_id: str, custodian_id: str, actor_id: Optional[str] = None) -> StewardshipBond:
        record = self._get_record(gaian_id)
        if record.state != GAIANLifecycleState.ADOPTABLE:
            raise ValueError(f"Custodian can only be assigned while GAIAN is ADOPTABLE (current: {record.state.name}).")
        bond = self._stewards.assign_custodian(gaian_id, custodian_id)
        self._logger.log(gaian_id=gaian_id, event_type=LifecycleEventType.CUSTODIAN_ASSIGNED,
                         payload={"custodian_id": custodian_id, "bond_id": bond.bond_id}, actor_id=actor_id)
        self._append_canonical_audit(
            gaian_id=gaian_id, event_type="STEWARD_ACTION",
            from_state=record.state.value, to_state=record.state.value,
            trigger_class="STEWARD_ACTION", actor_id=actor_id,
            justification="custodian assigned during adoptable period",
            metadata={"steward_id": custodian_id, "canon_reference": "C27"},
        )
        return bond

    def evaluate_adoption_queue(self) -> list:
        actions = self._queue.evaluate_timeouts()
        for action in actions:
            gid = action["gaian_id"]
            self._sentinel.check_adoption_timeout(gid, action["days"])
            self._append_canonical_audit(
                gaian_id=gid, event_type="CANON_PROCESS",
                from_state=GAIANLifecycleState.ADOPTABLE.value,
                to_state=GAIANLifecycleState.ADOPTABLE.value,
                trigger_class="CANON_PROCESS", actor_id="system-adoption-daemon",
                justification=f"adoption queue evaluation at day {action['days']}",
                metadata={"queue_action": action["action"], "canon_reference": "C27"},
            )
        return actions

    # ------------------------------------------------------------------
    # §8.2  Retirement (now wired to RetirementEngine)
    # ------------------------------------------------------------------

    def initiate_retirement(
        self,
        gaian_id:      str,
        reason:        RetirementReason,
        justification: str,
        actor_id:      Optional[str] = None,
        waive_notice:  bool = False,
    ):
        """
        Step 1 of C27 §8.2: Log retirement intent and start 72-hour notice.
        Does NOT yet transition state — call retire() after notice elapses.
        Returns the RetirementRecord.
        """
        return self._retirement.initiate_retirement(
            gaian_id=gaian_id,
            reason=reason,
            justification=justification,
            actor_id=actor_id,
            waive_notice=waive_notice,
        )

    def retire(
        self,
        gaian_id:          str,
        reason:            str,
        actor_id:          Optional[str] = None,
        retirement_reason: Optional[RetirementReason] = None,
        memory_data:       Optional[bytes] = None,
        contributions:     Optional[list] = None,
        knowledge_artifacts: Optional[list] = None,
        relationships:     Optional[list] = None,
        waive_notice:      bool = False,
    ) -> LegacyPackage:
        """
        Executes C27 §8.2 retirement in full:
          - Initiates retirement (if not already done)
          - Completes retirement: memory seal, legacy package
          - Transitions state to RETIRED

        Returns the generated LegacyPackage.
        """
        _reason = retirement_reason or RetirementReason.STEWARD_INITIATED
        if self._retirement.get_record(gaian_id) is None:
            self._retirement.initiate_retirement(
                gaian_id=gaian_id, reason=_reason, justification=reason,
                actor_id=actor_id, waive_notice=waive_notice,
            )
        audit_log = self.get_audit_log(gaian_id)
        steward_history = [
            b.to_dict() for b in self._stewards.get_bond_history(gaian_id)
        ]
        legacy = self._retirement.complete_retirement(
            gaian_id=gaian_id,
            audit_log=audit_log,
            steward_history=steward_history,
            memory_data=memory_data,
            contributions=contributions or [],
            knowledge_artifacts=knowledge_artifacts or [],
            relationships=relationships or [],
        )
        active_bond = self._stewards.get_active_bond(gaian_id)
        if active_bond:
            active_bond.release(reason=f"GAIAN retirement: {reason}")
        self._transition(
            gaian_id, GAIANLifecycleState.RETIRED, LifecycleEventType.RETIREMENT, actor_id,
            extra={"reason": reason, "legacy_package_id": legacy.package_id, "canon_reference": "C27"},
            justification=reason,
            trigger_class="CANON_PROCESS" if "timeout" in reason.lower() else (
                "STEWARD_ACTION" if actor_id else "SYSTEM_EVENT"
            ),
        )
        record = self._get_record(gaian_id)
        record.retired_at = record.last_transition_at
        self._queue.remove(gaian_id)
        return legacy

    # ------------------------------------------------------------------
    # §8.3  Archival (with 180-day gate)
    # ------------------------------------------------------------------

    def archive(
        self,
        gaian_id:             str,
        actor_id:             Optional[str] = None,
        bypass_180_day_check: bool = False,
    ) -> None:
        """
        RETIRED → ARCHIVED (C27 §8.3)

        Enforces the 180-day minimum post-RETIRED unless
        *bypass_180_day_check* is True (for tests / council override).

        Raises ValueError if the GAIAN is not yet archival-eligible.
        """
        record = self._get_record(gaian_id)
        if record.state not in _ARCHIVE_ELIGIBLE:
            self._sentinel.check_transition(gaian_id, record.state, GAIANLifecycleState.ARCHIVED)
            raise LifecycleTransitionError(
                gaian_id=gaian_id, from_state=record.state,
                to_state=GAIANLifecycleState.ARCHIVED,
                reason="Only RETIRED GAIANs may be archived.",
            )
        if not bypass_180_day_check and record.retired_at is not None:
            if not self._retirement.check_archival_eligible(gaian_id, record.retired_at):
                elapsed = (datetime.now(timezone.utc) - record.retired_at).days
                raise ValueError(
                    f"[C27 §8.3] GAIAN '{gaian_id}' is not yet archival-eligible. "
                    f"Requires 180 days post-RETIRED; currently {elapsed} day(s)."
                )
        self._logger.log(
            gaian_id=gaian_id, event_type=LifecycleEventType.ARCHIVAL,
            payload={"from_state": record.state.value, "to_state": GAIANLifecycleState.ARCHIVED.value},
            actor_id=actor_id,
        )
        self._append_canonical_audit(
            gaian_id=gaian_id, event_type="CANON_PROCESS",
            from_state=record.state.value, to_state=GAIANLifecycleState.ARCHIVED.value,
            trigger_class="CANON_PROCESS", actor_id=actor_id,
            justification="archival process executed",
            metadata={"canon_reference": "C27", "days_since_retirement": (
                (datetime.now(timezone.utc) - record.retired_at).days if record.retired_at else None
            )},
        )
        record.state = GAIANLifecycleState.ARCHIVED
        record.last_transition_at = datetime.now(timezone.utc)
        self._permissions.contract_for_state(gaian_id, GAIANLifecycleState.ARCHIVED)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def set_permission_envelope(self, gaian_id: str, envelope: PermissionEnvelope) -> None:
        self._permissions.set_envelope(gaian_id, envelope)

    def get_permission_envelope(self, gaian_id: str) -> PermissionEnvelope:
        return self._permissions.get_envelope(gaian_id)

    def get_active_steward(self, gaian_id: str) -> Optional[StewardshipBond]:
        return self._stewards.get_active_bond(gaian_id, role=StewardRole.PRIMARY)

    def get_state(self, gaian_id: str) -> GAIANLifecycleState:
        return self._get_record(gaian_id).state

    def get_audit_log(self, gaian_id: str) -> list:
        return [e.to_dict() for e in self._logger.get_log(gaian_id)]

    def get_canonical_audit_log(self, gaian_id: str) -> list:
        return [e.to_dict() for e in self._get_record(gaian_id).canonical_audit]

    def verify_log_integrity(self, gaian_id: str) -> bool:
        return self._logger.verify_chain(gaian_id)

    def verify_canonical_chain(self, gaian_id: str) -> bool:
        """Verifies the Ed25519 signatures and hash chain of canonical audit entries."""
        entries = self._get_record(gaian_id).canonical_audit
        return self._signer.verify_chain(entries)

    def get_adoption_entry(self, gaian_id: str):
        return self._queue.get(gaian_id)

    def get_sentinel_findings(self, gaian_id: str):
        return [
            {"case_id": f.case_id, "check_id": f.check_id.value,
             "severity": f.severity.value, "message": f.message, "resolved": f.resolved}
            for f in self._sentinel.get_findings(gaian_id)
        ]

    def get_legacy_package(self, gaian_id: str) -> Optional[LegacyPackage]:
        record = self._retirement.get_record(gaian_id)
        return record.legacy_package if record else None
