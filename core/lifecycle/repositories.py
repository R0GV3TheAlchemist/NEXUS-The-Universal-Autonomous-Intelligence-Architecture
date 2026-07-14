"""
core/lifecycle/repositories.py
C17 / C23 / C27 — Lifecycle Persistence Repository Interfaces

Defines abstract repository contracts for the two stateful registries
that LifecycleManager depends on. In-memory implementations are
provided as defaults (identical to Phase 1/2 behaviour). Production
deployments inject persistent subclasses.

Injection pattern::

    from core.lifecycle.repositories import SqliteLifecycleRepository  # your impl
    mgr = LifecycleManager(
        lifecycle_repo=SqliteLifecycleRepository(db_url),
        stewardship_repo=SqliteStewardshipRepository(db_url),
    )
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from .gaian_lifecycle_state import GAIANLifecycleState
from .lifecycle_audit_logger import LifecycleEvent
from .stewardship import StewardRole, StewardshipBond


# ---------------------------------------------------------------------------
# Lifecycle state repository
# ---------------------------------------------------------------------------

class LifecycleRepository(ABC):
    """
    Abstract repository for GAIAN lifecycle state persistence (C17/C23).

    Each method has atomicity semantics: either the full mutation is
    persisted or the call raises and leaves state unchanged.
    """

    @abstractmethod
    def save_state(
        self,
        gaian_id:   str,
        state:      GAIANLifecycleState,
        changed_at: datetime,
    ) -> None:
        """Persist a new lifecycle state for *gaian_id*."""

    @abstractmethod
    def load_state(self, gaian_id: str) -> Optional[GAIANLifecycleState]:
        """Return the current persisted state, or None if not registered."""

    @abstractmethod
    def save_audit_event(self, gaian_id: str, event: LifecycleEvent) -> None:
        """Append a LifecycleEvent to the durable audit log."""

    @abstractmethod
    def load_audit_log(self, gaian_id: str) -> List[LifecycleEvent]:
        """Return all audit events for *gaian_id* in insertion order."""

    @abstractmethod
    def all_gaian_ids(self) -> List[str]:
        """Return all registered GAIAN IDs."""


class InMemoryLifecycleRepository(LifecycleRepository):
    """
    In-memory lifecycle repository (default / test fallback).
    Behaviorally identical to the Phase 1/2 in-process stores.
    """

    def __init__(self) -> None:
        self._states: Dict[str, GAIANLifecycleState] = {}
        self._audit:  Dict[str, List[LifecycleEvent]] = {}

    def save_state(self, gaian_id: str, state: GAIANLifecycleState, changed_at: datetime) -> None:
        self._states[gaian_id] = state

    def load_state(self, gaian_id: str) -> Optional[GAIANLifecycleState]:
        return self._states.get(gaian_id)

    def save_audit_event(self, gaian_id: str, event: LifecycleEvent) -> None:
        self._audit.setdefault(gaian_id, []).append(event)

    def load_audit_log(self, gaian_id: str) -> List[LifecycleEvent]:
        return list(self._audit.get(gaian_id, []))

    def all_gaian_ids(self) -> List[str]:
        return list(self._states.keys())


# ---------------------------------------------------------------------------
# Stewardship bond repository
# ---------------------------------------------------------------------------

class StewardshipRepository(ABC):
    """
    Abstract repository for StewardshipBond persistence (C17/C23).
    """

    @abstractmethod
    def save_bond(self, bond: StewardshipBond) -> None:
        """Persist or update a stewardship bond."""

    @abstractmethod
    def load_active_bond(
        self,
        gaian_id: str,
        role:     Optional[StewardRole] = None,
    ) -> Optional[StewardshipBond]:
        """Return the active bond for *gaian_id* (optionally filtered by role)."""

    @abstractmethod
    def load_bond_history(self, gaian_id: str) -> List[StewardshipBond]:
        """Return all bonds (active + released) for *gaian_id*."""


class InMemoryStewardshipRepository(StewardshipRepository):
    """
    In-memory stewardship repository (default / test fallback).
    Mirrors the Phase 1/2 in-process StewardshipRegistry storage.
    """

    def __init__(self) -> None:
        self._bonds: Dict[str, List[StewardshipBond]] = {}

    def save_bond(self, bond: StewardshipBond) -> None:
        self._bonds.setdefault(bond.gaian_id, []).append(bond)

    def load_active_bond(
        self,
        gaian_id: str,
        role:     Optional[StewardRole] = None,
    ) -> Optional[StewardshipBond]:
        for b in reversed(self._bonds.get(gaian_id, [])):
            if b.is_active and (role is None or b.role == role):
                return b
        return None

    def load_bond_history(self, gaian_id: str) -> List[StewardshipBond]:
        return list(self._bonds.get(gaian_id, []))
