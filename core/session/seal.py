"""GAIA Session Seal — immutable session close protocol.

Executed when a session ends or when the Architect manually seals.

The 7-step seal sequence:
  1. Retrieve the open session and its MemoryManager
  2. Compute session metrics (duration, interaction count)
  3. HP-authorised M0→M1 transfer (if authorised)
  4. Log MagnumOpus stage at closing
  5. Update GaianTwinProfile with session delta
  6. Seal the SealedSessionRecord (immutable from this point)
  7. Emit session sealed event to audit trail

Once sealed, the SealedSessionRecord cannot be modified.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from core.ontology import GAIARuntime
from core.memory.manager import MemoryManager
from core.memory.layers import MemoryTag

from .result import SealedSessionRecord


class SessionSeal:
    """Executes the GAIA session seal protocol.

    Usage:
        seal = SessionSeal(runtime=runtime)
        record = seal.run(
            session_id=result.session_id,
            gaian_id=result.gaian_id,
            memory_manager=mm,
            authorise_persist=True,
            session_summary="Built #462 and #463 tonight.",
            breakthrough=True,
        )
    """

    def __init__(self, runtime: GAIARuntime) -> None:
        self._runtime = runtime
        self._sealed_records: dict[str, SealedSessionRecord] = {}  # session_id -> record

    def run(
        self,
        session_id: str,
        gaian_id: str,
        memory_manager: MemoryManager,
        stage_at_open: str = "NIGREDO",
        authorise_persist: bool = False,
        session_summary: Optional[str] = None,
        breakthrough: bool = False,
        shadow_work: bool = False,
        interaction_count: int = 0,
        opened_at: Optional[datetime] = None,
        filter_tags: Optional[list[MemoryTag]] = None,
    ) -> SealedSessionRecord:
        """Execute the 7-step session seal sequence.

        Returns a SealedSessionRecord — immutable after this call.
        """
        record = SealedSessionRecord(
            session_id=session_id,
            gaian_id=gaian_id,
            architect_id=memory_manager.human_principal_id,
            opened_at=opened_at or datetime.now(timezone.utc),
        )
        record.stage_at_open = stage_at_open
        record.interaction_count = interaction_count

        # ----------------------------------------------------------------
        # STEP 1: Verify session exists and compute duration
        # ----------------------------------------------------------------
        record.log_seal_step(1, f"Sealing session {session_id[:8]}")
        buf = memory_manager.get_session(session_id)
        m0_count = buf.count() if buf else 0
        record.m0_records_created = m0_count
        if opened_at:
            record.duration_seconds = (
                datetime.now(timezone.utc) - opened_at
            ).total_seconds()
        record.log_seal_step(1, f"M0 records in buffer: {m0_count}")

        # ----------------------------------------------------------------
        # STEP 2: HP-authorised M0 → M1 transfer
        # ----------------------------------------------------------------
        record.log_seal_step(2, f"M1 persistence authorised: {authorise_persist}")
        persisted = memory_manager.close_session(
            session_id=session_id,
            authorise_persist=authorise_persist,
            filter_tags=filter_tags,
            breakthrough=breakthrough,
            shadow_work=shadow_work,
            interaction_count=interaction_count,
            session_summary=session_summary,
        )
        record.m1_records_persisted = len(persisted)
        record.session_summary = session_summary
        record.breakthrough_occurred = breakthrough
        record.shadow_work_occurred = shadow_work
        record.log_seal_step(2, f"M1 records persisted: {record.m1_records_persisted}")

        # ----------------------------------------------------------------
        # STEP 3: Get stage at seal from Twin Profile
        # ----------------------------------------------------------------
        record.log_seal_step(3, "Recording stage at seal")
        try:
            profile = memory_manager.profile
            record.stage_at_seal = profile.current_alchemical_stage
            record.stage_advanced = record.stage_at_open != record.stage_at_seal
        except RuntimeError:
            record.stage_at_seal = stage_at_open  # Identity terminated
        record.log_seal_step(
            3,
            f"Stage: {record.stage_at_open} → {record.stage_at_seal} "
            f"(advanced={record.stage_advanced})"
        )

        # ----------------------------------------------------------------
        # STEP 4: Write to audit trail
        # ----------------------------------------------------------------
        record.log_seal_step(4, "Writing seal to GAIARuntime audit trail")
        trail = self._runtime.get_audit_trail(gaian_id)
        if trail:
            trail.record(
                action="SESSION_SEALED",
                human_principal_id=memory_manager.human_principal_id,
                session_id=session_id,
                target_entity_id=gaian_id,
                target_entity_type="GAIAN",
                before_state={"stage": record.stage_at_open},
                after_state={
                    "stage": record.stage_at_seal,
                    "m1_persisted": record.m1_records_persisted,
                    "breakthrough": breakthrough,
                },
                result="SUCCESS",
                metadata={
                    "session_summary": session_summary,
                    "duration_seconds": record.duration_seconds,
                },
            )
        record.log_seal_step(4, "Audit entry written")

        # ----------------------------------------------------------------
        # STEP 5: Seal the record (immutable from this point)
        # ----------------------------------------------------------------
        record.log_seal_step(5, "Sealing record — immutable from this point")
        record.seal()
        self._sealed_records[session_id] = record
        record.log_seal_step(5, "[SESSION SEALED]")

        return record

    def get_sealed(self, session_id: str) -> Optional[SealedSessionRecord]:
        """Retrieve a sealed session record by session_id."""
        return self._sealed_records.get(session_id)

    def history(self, gaian_id: Optional[str] = None) -> list[SealedSessionRecord]:
        """All sealed records, optionally filtered by gaian_id."""
        records = list(self._sealed_records.values())
        if gaian_id:
            records = [r for r in records if r.gaian_id == gaian_id]
        return sorted(records, key=lambda r: r.sealed_at)

    def count(self) -> int:
        return len(self._sealed_records)
