"""GAIA Primordial Session — canonical boot-time session context.

Canon References: C04 (Human/Gaian Twin Architecture), C17 (Persistent Memory)
Issue: #440 (Session Bootstrap) — gaia.session.primordial missing

The primordial session is the pre-architect session context that GAIA
establishes at boot, before any Human Principal initiates a session.
It is the lowest-level session context — the ground state.

All E2E, integration, and boot tests assert that::

    gaia.session.primordial

exists in the session store immediately after the system boots.
This module writes and owns that context.

Usage (called automatically by SessionManager.__init__)::

    from core.session.primordial import bootstrap_primordial_session
    from core.session.store import SESSION_STORE

    bootstrap_primordial_session(SESSION_STORE)
    assert SESSION_STORE["gaia.session.primordial"] is not None
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict

# Session store key — this exact string is asserted by all boot/E2E tests
PRIMORDIAL_KEY = "gaia.session.primordial"


@dataclass
class PrimordialSession:
    """The boot-time GAIA session context.

    Written into the session store under ``gaia.session.primordial``
    the moment SessionManager is instantiated.  Read-only after creation.
    """

    session_id: str = "primordial"
    boot_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: str = "ACTIVE"
    mode: str = "PRIMORDIAL"       # GAIAMode.PRIMORDIAL — str to avoid circular import
    gaian_count: int = 0
    architect_count: int = 0
    schema_initialised: bool = False
    notes: str = "Primordial session bootstrapped at runtime init."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def mark_schema_ready(self) -> None:
        """Called by init_db() completion hook — marks DB schema as live."""
        self.schema_initialised = True


def bootstrap_primordial_session(
    session_store: dict,
    gaian_count: int = 0,
    architect_count: int = 0,
    schema_initialised: bool = False,
) -> PrimordialSession:
    """Create the PrimordialSession and write it into session_store.

    Safe to call multiple times — subsequent calls update the existing
    entry rather than overwriting with a new boot timestamp.

    Parameters
    ----------
    session_store:
        The mutable dict (or dict-like object) that the session package
        uses as its in-process store.  Must support __setitem__.
    gaian_count:
        Number of Gaian instances already registered at boot time.
    architect_count:
        Number of Architect profiles already in the DB at boot time.
    schema_initialised:
        True if init_db() has already run successfully.

    Returns
    -------
    PrimordialSession
        The created (or updated) primordial session object.
    """
    if PRIMORDIAL_KEY in session_store:
        # Already bootstrapped — update live counts rather than reset timestamp
        existing: PrimordialSession = session_store[PRIMORDIAL_KEY]
        existing.gaian_count = gaian_count
        existing.architect_count = architect_count
        existing.schema_initialised = schema_initialised
        return existing

    primordial = PrimordialSession(
        gaian_count=gaian_count,
        architect_count=architect_count,
        schema_initialised=schema_initialised,
    )
    session_store[PRIMORDIAL_KEY] = primordial
    return primordial
