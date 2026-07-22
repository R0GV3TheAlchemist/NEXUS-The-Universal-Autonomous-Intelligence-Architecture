"""twins.engine

Digital Twin Coordination Engine

Provides typed stubs for GAIA's digital twin layer: twin descriptors,
synchronisation plans, consent gates, and the orchestrator that manages
twin lifecycles and state synchronisation.

Phase C: all methods raise NotImplementedError.
Phase D: implement against DIGITALTWINS.md specification.

Research reference:
    Azure Digital Twins   - twin graph models
    Eclipse Ditto         - state channels and sync
    W3C Web of Things     - consent and provenance
    GAIAN_LAWS.md Law II  - Right to Forget (consent-driven deletion)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Mapping, Optional, Sequence

logger = logging.getLogger("twins.engine")


class TwinStatus(Enum):
    """Lifecycle status of a digital twin."""
    PENDING = auto()    # Registered but not yet synchronised
    ACTIVE = auto()     # Live and synchronised
    DEGRADED = auto()   # Sync lagging or partial
    ARCHIVED = auto()   # Retired, read-only


@dataclass
class TwinSpec:
    """Descriptor for a NEXUS digital twin.

    Fields:
        twin_id:      UUID4 identifier.
        name:         Human-readable name (e.g., 'GAIA-Node-Alpha').
        model_id:     Reference to the DTDL or WoT model definition.
        owner:        Owning entity identifier.
        properties:   Initial twin property values.
        created_at:   UTC creation timestamp.
    """
    name: str
    model_id: str
    owner: str
    twin_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    properties: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TwinState:
    """Current state snapshot of a digital twin.

    Fields:
        twin_id:       Reference to the TwinSpec.
        properties:    Current property values.
        status:        TwinStatus lifecycle state.
        last_sync:     UTC timestamp of last successful sync.
    """
    twin_id: str
    properties: Mapping[str, Any] = field(default_factory=dict)
    status: TwinStatus = TwinStatus.PENDING
    last_sync: Optional[datetime] = None


@dataclass
class SyncPlan:
    """Plan for synchronising a digital twin with its physical counterpart.

    Fields:
        twin_id:         Target twin.
        strategy:        Sync strategy name ('push', 'pull', 'bidirectional').
        interval_sec:    Sync interval in seconds (0 = event-driven).
        conflict_policy: What to do on state conflict ('physical-wins', 'twin-wins', 'merge').
    """
    twin_id: str
    strategy: str = "bidirectional"
    interval_sec: float = 60.0
    conflict_policy: str = "physical-wins"


@dataclass
class TwinConsent:
    """Consent record for twin data access and synchronisation.

    Implements GAIAN_LAWS.md Law II (Right to Forget) and W3C WoT
    consent model.

    Fields:
        twin_id:         Twin this consent governs.
        granted_to:      Entity receiving access.
        permissions:     Set of permitted operations ('read', 'write', 'sync', 'delete').
        expires_at:      UTC expiry (None = indefinite).
        revoked:         True if consent has been explicitly revoked.
    """
    twin_id: str
    granted_to: str
    permissions: Sequence[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    revoked: bool = False


class TwinOrchestrator:
    """Orchestrates digital twin registration, sync, and consent.

    Phase C: stubs only.
    Phase D: implement against DIGITALTWINS.md.

    Reference:
        Azure Digital Twins, Eclipse Ditto, W3C WoT.
        GAIAN_LAWS.md Law II - Right to Forget.
    """

    def __init__(self) -> None:
        self._twins: dict[str, TwinSpec] = {}
        self._states: dict[str, TwinState] = {}
        self._consents: list[TwinConsent] = []
        logger.info("TwinOrchestrator initialised.")

    def register(self, spec: TwinSpec) -> str:
        """Register a new digital twin."""
        self._twins[spec.twin_id] = spec
        self._states[spec.twin_id] = TwinState(twin_id=spec.twin_id)
        logger.debug("TwinOrchestrator: registered twin '%s' (%s).", spec.name, spec.twin_id)
        return spec.twin_id

    def sync(self, twin_id: str, plan: SyncPlan) -> TwinState:
        """Synchronise a twin against its physical counterpart.

        Raises:
            NotImplementedError: Always in Phase C.
                Expected: apply SyncPlan strategy, resolve conflicts,
                update TwinState, emit telemetry event.
        """
        raise NotImplementedError(
            "TwinOrchestrator.sync() not implemented. "
            "Expected: apply SyncPlan, resolve conflicts per conflict_policy, "
            "update TwinState.last_sync and properties."
        )

    def grant_consent(self, consent: TwinConsent) -> None:
        """Grant data access/sync consent for a twin."""
        self._consents.append(consent)
        logger.debug("TwinOrchestrator: consent granted for twin '%s' to '%s'.",
                     consent.twin_id, consent.granted_to)

    def revoke_consent(self, twin_id: str, granted_to: str) -> bool:
        """Revoke consent for a twin and entity pair.

        Returns:
            True if a consent record was found and revoked.
        """
        for c in self._consents:
            if c.twin_id == twin_id and c.granted_to == granted_to and not c.revoked:
                c.revoked = True
                logger.info("TwinOrchestrator: consent revoked for twin '%s' / '%s'.",
                            twin_id, granted_to)
                return True
        return False
