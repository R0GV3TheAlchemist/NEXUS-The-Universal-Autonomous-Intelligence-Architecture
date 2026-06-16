"""Memory Manager — the unified API for GAIA's memory system.

The MemoryManager is the single point of entry for all memory operations.
It owns all five layers and coordinates between them.

Higher-level GAIA modules (Runtime, NLP Engine, Context Injection Protocol)
interact with memory exclusively through the MemoryManager.

Integrates with:
  - GAIARuntime (C03) via gaian_id / human_principal_id pairing
  - AuditTrail (C03) for revocation logging
  - GaianTwinProfile (C04) for session close updates
  - ShadowRegistry (C23) for pattern learning
"""

from __future__ import annotations

from typing import Any, Optional

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag
from .session_buffer import SessionBuffer
from .episodic import EpisodicMemoryStore
from .semantic import SemanticMemoryStore
from .identity import IdentityMemoryStore, GaianTwinProfile
from .shared import SharedMemoryStore
from .shadow_registry import ShadowRegistry, ShadowPattern, ShadowEntry
from .retrieval import MemoryRetrievalEngine, RetrievalQuery, RankedMemory


class MemoryManager:
    """The unified memory API for a single Gaian instance.

    One MemoryManager per Gaian instance. Contains all five layers
    and the retrieval engine.

    Usage:
        mm = MemoryManager(gaian_id=gaian.id, human_principal_id=hp.id)
        session = mm.open_session(session_id="xyz")
        session.append("User expressed desire to build GAIA OS", tags=[MemoryTag.FACTUAL])
        mm.close_session(session_id="xyz", authorise_persist=True)
        results = mm.retrieve(RetrievalQuery(tags=[MemoryTag.FACTUAL]))
    """

    def __init__(self, gaian_id: str, human_principal_id: str) -> None:
        self.gaian_id = gaian_id
        self.human_principal_id = human_principal_id

        self.episodic = EpisodicMemoryStore(gaian_id, human_principal_id)
        self.semantic = SemanticMemoryStore(gaian_id, human_principal_id)
        self.identity = IdentityMemoryStore(gaian_id, human_principal_id)
        self.shared = SharedMemoryStore()
        self.shadow = ShadowRegistry(gaian_id, human_principal_id)
        self.retrieval = MemoryRetrievalEngine(
            episodic=self.episodic,
            semantic=self.semantic,
            identity=self.identity,
        )

        self._active_sessions: dict[str, SessionBuffer] = {}

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def open_session(self, session_id: str) -> SessionBuffer:
        """Open a new M0 session buffer. One buffer per session_id."""
        if session_id in self._active_sessions:
            raise ValueError(f"Session {session_id} is already open.")
        buffer = SessionBuffer(
            session_id=session_id,
            gaian_id=self.gaian_id,
            human_principal_id=self.human_principal_id,
        )
        self._active_sessions[session_id] = buffer
        return buffer

    def get_session(self, session_id: str) -> Optional[SessionBuffer]:
        """Return an active session buffer."""
        return self._active_sessions.get(session_id)

    def close_session(
        self,
        session_id: str,
        authorise_persist: bool = False,
        filter_tags: Optional[list[MemoryTag]] = None,
        breakthrough: bool = False,
        shadow_work: bool = False,
        interaction_count: int = 0,
        session_summary: Optional[str] = None,
    ) -> list[MemoryRecord]:
        """Close a session buffer.

        If authorise_persist=True (Human Principal consent), transfers
        M0 records to M1 Episodic Memory.
        Updates the GaianTwinProfile with session history.
        Clears the buffer regardless.

        Returns the list of M1 records created (empty if not persisted).
        """
        buffer = self._active_sessions.pop(session_id, None)
        if buffer is None:
            raise KeyError(f"No active session found: {session_id}")

        buffer_records = buffer.close()
        persisted: list[MemoryRecord] = []

        if authorise_persist:
            persisted = self.episodic.transfer_from_buffer(
                buffer_records, session_id, filter_tags
            )
            if session_summary:
                self.episodic.store(
                    content=session_summary,
                    session_id=session_id,
                    tags=[MemoryTag.SESSION_SUMMARY],
                    confidence=1.0,
                    source="SESSION_CLOSE",
                )

        # Update Twin Profile
        self.identity.profile.record_session(
            session_id=session_id,
            breakthrough=breakthrough,
            shadow_work=shadow_work,
            interaction_count=interaction_count,
        )

        # Sync shadow flags to Twin Profile
        active_flags = [f.value for f in self.shadow.active_flags()]
        self.identity.profile.shadow_registry_flags = active_flags

        buffer.clear()
        return persisted

    # ------------------------------------------------------------------
    # Memory operations (delegated to layers)
    # ------------------------------------------------------------------

    def remember(
        self,
        content: str,
        session_id: str,
        layer: MemoryLayer = MemoryLayer.M1_EPISODIC,
        tags: Optional[list[MemoryTag]] = None,
        confidence: float = 1.0,
        structured_data: Optional[dict[str, Any]] = None,
        canon_ref: Optional[str] = None,
    ) -> MemoryRecord:
        """Store a memory directly to a specific layer (bypassing session buffer).

        For M1: stores directly to episodic.
        For M2: raises — use assert_fact() for semantic memory.
        For M3: stores identity record.
        """
        if layer == MemoryLayer.M1_EPISODIC:
            return self.episodic.store(
                content, session_id, tags, structured_data, confidence,
                canon_ref=canon_ref,
            )
        elif layer == MemoryLayer.M3_IDENTITY:
            return self.identity.store(
                content, session_id, tags, structured_data, confidence,
                canon_ref=canon_ref,
            )
        elif layer == MemoryLayer.M2_SEMANTIC:
            raise ValueError(
                "Use MemoryManager.semantic.assert_fact() for M2 Semantic Memory. "
                "Semantic facts require a concept key."
            )
        else:
            raise ValueError(f"Cannot directly write to layer {layer.value} via remember().")

    def retrieve(self, query: RetrievalQuery) -> list[RankedMemory]:
        """Cross-layer relevance-ranked retrieval."""
        return self.retrieval.retrieve(query)

    def log_shadow(
        self,
        pattern: ShadowPattern,
        session_id: str,
        description: str,
        trigger: Optional[str] = None,
    ) -> ShadowEntry:
        """Log a shadow pattern event to the Shadow Registry."""
        return self.shadow.log(pattern, session_id, description, trigger)

    # ------------------------------------------------------------------
    # Right to Forget — Privacy controls
    # ------------------------------------------------------------------

    def forget_session(
        self, session_id: str, audit_id: str
    ) -> int:
        """Revoke all episodic records from a specific session.

        Human Principal's right to forget. The audit trail records
        that revocation occurred — not what was revoked.
        """
        return self.episodic.revoke_session(session_id, audit_id)

    def forget_fact(self, concept: str, audit_id: str) -> bool:
        """Revoke a specific semantic fact by concept key."""
        return self.semantic.revoke_fact(concept, audit_id)

    def full_identity_revocation(self, audit_id: str) -> None:
        """Full M3 revocation. Terminates the Gaian instance per C17.

        This is the nuclear option. The HP invokes this to completely
        end the Gaian relationship. Cannot be undone.
        """
        self.identity.full_revocation(audit_id)

    # ------------------------------------------------------------------
    # Profile access
    # ------------------------------------------------------------------

    @property
    def profile(self) -> GaianTwinProfile:
        """Direct access to the Gaian Twin Profile."""
        return self.identity.profile

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "human_principal_id": self.human_principal_id,
            "episodic_count": self.episodic.count(),
            "semantic_count": self.semantic.count(),
            "identity_record_count": self.identity.count(),
            "shared_count": self.shared.count(),
            "shadow_total": self.shadow.count(),
            "shadow_unresolved": self.shadow.count(unresolved_only=True),
            "active_sessions": list(self._active_sessions.keys()),
            "relationship_depth": self.identity.profile.relationship_depth
            if not self.identity.is_terminated else None,
            "shadow_flags": self.shadow.active_flags(),
        }

    def __repr__(self) -> str:
        return (
            f"<MemoryManager gaian={self.gaian_id[:8]} "
            f"episodic={self.episodic.count()} "
            f"semantic={self.semantic.count()}>"
        )
