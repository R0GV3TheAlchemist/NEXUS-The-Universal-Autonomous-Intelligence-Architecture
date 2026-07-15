"""Session Manager — the unified session lifecycle coordinator.

The SessionManager is the single point of entry for all session operations.
It owns the bootstrap, seal, architect repository, and tracks all open sessions.

Higher-level modules (API layer, NLP engine, runtime) interact with session
state exclusively through the SessionManager.

REST API surface (to be wired by FastAPI/Flask router):
  POST /session/init     — open a new session
  POST /session/seal     — seal the current session
  GET  /session/current  — current session state
  GET  /session/history  — all sealed sessions for an architect
"""
from __future__ import annotations

from typing import Any, Optional

from core.ontology import GAIARuntime
from core.memory.manager import MemoryManager
from core.memory.layers import MemoryTag
from .architect import ArchitectRepository
from .bootstrap import SessionBootstrap
from .seal import SessionSeal
from .result import SessionInitResult, SealedSessionRecord
from .store import SESSION_STORE                              # Fix 5a
from .primordial import bootstrap_primordial_session          # Fix 5b
from .stubs import (
    ICircadianLightEngine,
    IMagnumOpusStageEngine,
    IShadowInterrogatorEngine,
    ISpectralForceEngine,
    ISystemPromptBuilder,
)


class SessionManager:
    """Unified session lifecycle coordinator.

    Usage::

        sm = SessionManager(runtime=runtime)
        result = sm.init_session(architect_name="Kyle Steen")
        # ... session work ...
        record = sm.seal_session(
            session_id=result.session_id,
            authorise_persist=True,
            session_summary="Built the World Fabric tonight.",
        )
    """

    def __init__(
        self,
        runtime: GAIARuntime,
        circadian_engine: Optional[ICircadianLightEngine] = None,
        spectral_engine: Optional[ISpectralForceEngine] = None,
        magnum_opus_engine: Optional[IMagnumOpusStageEngine] = None,
        shadow_engine: Optional[IShadowInterrogatorEngine] = None,
        prompt_builder: Optional[ISystemPromptBuilder] = None,
    ) -> None:
        self._runtime = runtime
        self._architect_repo = ArchitectRepository()
        self._memory_managers: dict[str, MemoryManager] = {}  # gaian_id -> MemoryManager
        self._bootstrap = SessionBootstrap(
            runtime=runtime,
            architect_repo=self._architect_repo,
            memory_managers=self._memory_managers,
            circadian_engine=circadian_engine,
            spectral_engine=spectral_engine,
            magnum_opus_engine=magnum_opus_engine,
            shadow_engine=shadow_engine,
            prompt_builder=prompt_builder,
        )
        self._seal = SessionSeal(runtime=runtime)

        # Active sessions: session_id -> SessionInitResult
        self._active_sessions: dict[str, SessionInitResult] = {}

        # ------------------------------------------------------------------
        # Fix 5 — bootstrap gaia.session.primordial into the module-level
        # SESSION_STORE so that all E2E/integration/boot tests can assert
        # SESSION_STORE["gaia.session.primordial"] is not None.
        # ------------------------------------------------------------------
        bootstrap_primordial_session(SESSION_STORE)

    # ------------------------------------------------------------------
    # POST /session/init
    # ------------------------------------------------------------------

    def init_session(
        self,
        architect_name: str,
        foundation_statement: str = "",
        elemental_signature: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        space_context: Optional[str] = None,
        autonomy_tier: int = 4,
    ) -> SessionInitResult:
        """Open a new GAIA session.

        Executes the full 10-step bootstrap.
        Returns a SessionInitResult with full context, opening prompt,
        and bootstrap log.  The session is OPEN after this call.
        """
        result = self._bootstrap.run(
            architect_name=architect_name,
            foundation_statement=foundation_statement,
            elemental_signature=elemental_signature,
            latitude=latitude,
            longitude=longitude,
            space_context=space_context,
            autonomy_tier=autonomy_tier,
        )
        self._active_sessions[result.session_id] = result
        return result

    # ------------------------------------------------------------------
    # POST /session/seal
    # ------------------------------------------------------------------

    def seal_session(
        self,
        session_id: str,
        authorise_persist: bool = False,
        session_summary: Optional[str] = None,
        breakthrough: bool = False,
        shadow_work: bool = False,
        interaction_count: int = 0,
        filter_tags: Optional[list[MemoryTag]] = None,
    ) -> SealedSessionRecord:
        """Seal an open session.  Immutable after this call."""
        init_result = self._active_sessions.get(session_id)
        if not init_result:
            raise KeyError(f"No active session found: {session_id[:8]}")

        mm = self._memory_managers.get(init_result.gaian_id)
        if not mm:
            raise RuntimeError(f"No MemoryManager for gaian {init_result.gaian_id[:8]}")

        sealed = self._seal.run(
            session_id=session_id,
            gaian_id=init_result.gaian_id,
            memory_manager=mm,
            stage_at_open=(
                init_result.stage_report.stage if init_result.stage_report else "NIGREDO"
            ),
            authorise_persist=authorise_persist,
            session_summary=session_summary,
            breakthrough=breakthrough,
            shadow_work=shadow_work,
            interaction_count=interaction_count,
            opened_at=init_result.opened_at,
            filter_tags=filter_tags,
        )
        # Move from active to sealed
        del self._active_sessions[session_id]
        return sealed

    # ------------------------------------------------------------------
    # GET /session/current
    # ------------------------------------------------------------------

    def get_current_session(self, session_id: str) -> Optional[SessionInitResult]:
        """Return the current state of an active session."""
        return self._active_sessions.get(session_id)

    def list_active_sessions(self) -> list[SessionInitResult]:
        """All currently open sessions."""
        return list(self._active_sessions.values())

    # ------------------------------------------------------------------
    # GET /session/history
    # ------------------------------------------------------------------

    def get_session_history(
        self, gaian_id: Optional[str] = None
    ) -> list[SealedSessionRecord]:
        """All sealed session records, optionally filtered by gaian_id."""
        return self._seal.history(gaian_id)

    # ------------------------------------------------------------------
    # Memory access (convenience)
    # ------------------------------------------------------------------

    def get_memory_manager(self, gaian_id: str) -> Optional[MemoryManager]:
        return self._memory_managers.get(gaian_id)

    def get_architect_profile(self, name: str):
        return self._architect_repo.get_by_name(name)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        return {
            "active_sessions": len(self._active_sessions),
            "sealed_sessions": self._seal.count(),
            "registered_architects": self._architect_repo.count(),
            "memory_managers": len(self._memory_managers),
        }

    def __repr__(self) -> str:
        return (
            f"<SessionManager active={len(self._active_sessions)} "
            f"sealed={self._seal.count()}>"
        )
