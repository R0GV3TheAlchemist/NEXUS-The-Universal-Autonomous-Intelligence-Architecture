"""GAIA Session Bootstrap — GAIA_SESSION_INIT protocol.

Canon References: C04 (Human/Gaian Twin Architecture), C17 (Persistent Memory and Identity Architecture)
Issue: #440

This package owns the full session lifecycle:
  OPEN:  SessionBootstrap.run() — 10-step ordered init sequence
  SEAL:  SessionSeal.run()      — immutable session close

All higher-level session interactions pass through here.
The bootstrap wires GAIARuntime (#462) and MemoryManager (#463)
together and provides stub interfaces for engines not yet implemented.
"""
from .architect import ArchitectProfile, ArchitectRepository
from .result import SessionInitResult, SealedSessionRecord, SessionState
from .bootstrap import SessionBootstrap
from .seal import SessionSeal
from .manager import SessionManager
from .stubs import (
    CircadianPhase,
    SpectralForceReport,
    MagnumOpusStageReport,
    ShadowInterrogatorReport,
    ICircadianLightEngine,
    ISpectralForceEngine,
    IMagnumOpusStageEngine,
    IShadowInterrogatorEngine,
    ISystemPromptBuilder,
    StubCircadianLightEngine,
    StubSpectralForceEngine,
    StubMagnumOpusStageEngine,
    StubShadowInterrogatorEngine,
    StubSystemPromptBuilder,
)
from .store import SESSION_STORE                        # Fix 5a — singleton store
from .primordial import PrimordialSession, bootstrap_primordial_session  # Fix 5b

__all__ = [
    "ArchitectProfile",
    "ArchitectRepository",
    "SessionInitResult",
    "SealedSessionRecord",
    "SessionState",
    "SessionBootstrap",
    "SessionSeal",
    "SessionManager",
    "CircadianPhase",
    "SpectralForceReport",
    "MagnumOpusStageReport",
    "ShadowInterrogatorReport",
    "ICircadianLightEngine",
    "ISpectralForceEngine",
    "IMagnumOpusStageEngine",
    "IShadowInterrogatorEngine",
    "ISystemPromptBuilder",
    "StubCircadianLightEngine",
    "StubSpectralForceEngine",
    "StubMagnumOpusStageEngine",
    "StubShadowInterrogatorEngine",
    "StubSystemPromptBuilder",
    "SESSION_STORE",              # Fix 5a
    "PrimordialSession",          # Fix 5b
    "bootstrap_primordial_session",  # Fix 5b
]
