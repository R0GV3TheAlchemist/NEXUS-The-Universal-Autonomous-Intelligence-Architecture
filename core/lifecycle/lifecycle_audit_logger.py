"""
core/lifecycle/lifecycle_audit_logger.py
C27 §6 — Lifecycle Event Logging & Audit Requirements

All state transitions and stewardship events are:
  1. Timestamped (UTC)
  2. Assigned a sequential event index per GAIAN
  3. HMAC-SHA256 signed using the runtime secret key
     (chained: each event's signature is computed over
      the previous event's signature, creating a tamper-evident log)
  4. Stored in an append-only in-memory log (production: delegate to C17)

Authority: C27 v1.0.0 (2026-07-13)
Cross-refs: C17 (Memory Architecture), C23 (Shadow Registry)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Event Type Enum
# ---------------------------------------------------------------------------

class LifecycleEventType(str, Enum):
    # State transition events
    STATE_TRANSITION  = "STATE_TRANSITION"
    GENESIS           = "GENESIS"          # LATENT → BORN
    ACTIVATION        = "ACTIVATION"       # BORN → ACTIVE or ADOPTABLE → ACTIVE
    DORMANCY_ENTER    = "DORMANCY_ENTER"
    DORMANCY_EXIT     = "DORMANCY_EXIT"
    ADOPTABLE_ENTER   = "ADOPTABLE_ENTER"
    RETIREMENT        = "RETIREMENT"
    ARCHIVAL          = "ARCHIVAL"

    # Stewardship events
    STEWARD_BONDED    = "STEWARD_BONDED"
    STEWARD_RELEASED  = "STEWARD_RELEASED"
    STEWARD_SUCCEEDED = "STEWARD_SUCCEEDED"
    CUSTODIAN_ASSIGNED = "CUSTODIAN_ASSIGNED"

    # Audit markers
    INTEGRITY_CHECK   = "INTEGRITY_CHECK"
    ANNOTATION        = "ANNOTATION"


# ---------------------------------------------------------------------------
# Lifecycle Event Dataclass
# ---------------------------------------------------------------------------

@dataclass
class LifecycleEvent:
    """A single, immutable, signed lifecycle event (C27 §6)."""

    event_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id:    str = ""
    event_type:  LifecycleEventType = LifecycleEventType.ANNOTATION
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    seq:         int = 0           # Per-GAIAN monotonic sequence number
    payload:     dict = field(default_factory=dict)
    actor_id:    Optional[str] = None  # steward / system process that triggered
    prev_sig:    str = ""              # HMAC of previous event (chain root = "")
    signature:   str = ""              # HMAC of this event's canonical form

    def to_canonical(self) -> str:
        """
        Deterministic string representation used as the HMAC input.
        Excludes `signature` itself to avoid circular dependency.
        """
        return json.dumps(
            {
                "event_id":   self.event_id,
                "gaian_id":   self.gaian_id,
                "event_type": self.event_type.value,
                "occurred_at": self.occurred_at.isoformat(),
                "seq":         self.seq,
                "payload":     self.payload,
                "actor_id":    self.actor_id,
                "prev_sig":    self.prev_sig,
            },
            sort_keys=True,
        )

    def to_dict(self) -> dict:
        d = json.loads(self.to_canonical())
        d["signature"] = self.signature
        return d


# ---------------------------------------------------------------------------
# Audit Logger
# ---------------------------------------------------------------------------

class LifecycleAuditLogger:
    """
    Append-only, HMAC-chained audit logger for GAIAN lifecycle events.

    Usage::

        logger = LifecycleAuditLogger(secret_key=b"runtime-secret")
        event  = logger.log(
            gaian_id="gaian-abc123",
            event_type=LifecycleEventType.GENESIS,
            payload={"from_state": "LT", "to_state": "BR"},
            actor_id="steward-xyz",
        )

    The `secret_key` should be the runtime GAIAN signing key (C15).
    If not supplied, a per-process ephemeral key is used (test/dev only).
    """

    _EPHEMERAL_KEY: bytes = os.urandom(32)

    def __init__(self, secret_key: Optional[bytes] = None) -> None:
        self._key: bytes = secret_key or self._EPHEMERAL_KEY
        # gaian_id → list of LifecycleEvent (append-only)
        self._log: Dict[str, List[LifecycleEvent]] = {}

    # ------------------------------------------------------------------
    # Core logging
    # ------------------------------------------------------------------

    def log(
        self,
        gaian_id:   str,
        event_type: LifecycleEventType,
        payload:    Optional[dict] = None,
        actor_id:   Optional[str]  = None,
    ) -> LifecycleEvent:
        """
        Creates, signs, and appends a new LifecycleEvent.
        Returns the committed event.
        """
        history  = self._log.setdefault(gaian_id, [])
        seq      = len(history)
        prev_sig = history[-1].signature if history else ""

        event = LifecycleEvent(
            gaian_id=gaian_id,
            event_type=event_type,
            seq=seq,
            payload=payload or {},
            actor_id=actor_id,
            prev_sig=prev_sig,
        )
        event.signature = self._sign(event.to_canonical())
        history.append(event)
        return event

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_chain(
        self,
        gaian_id: str,
    ) -> bool:
        """
        Re-computes every event's HMAC and verifies the prev_sig chain.
        Returns True if the log is intact, False if tampered.
        """
        history = self._log.get(gaian_id, [])
        prev_sig = ""
        for event in history:
            if event.prev_sig != prev_sig:
                return False
            expected_sig = self._sign(event.to_canonical())
            if not hmac.compare_digest(event.signature, expected_sig):
                return False
            prev_sig = event.signature
        return True

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_log(
        self,
        gaian_id: str,
        event_type: Optional[LifecycleEventType] = None,
    ) -> List[LifecycleEvent]:
        """
        Returns the full log (or filtered by event_type) for a GAIAN.
        The returned list is a copy — the internal log is append-only.
        """
        history = self._log.get(gaian_id, [])
        if event_type is not None:
            history = [e for e in history if e.event_type == event_type]
        return list(history)

    def get_latest(
        self,
        gaian_id: str,
    ) -> Optional[LifecycleEvent]:
        """Returns the most recent event for a GAIAN, or None."""
        history = self._log.get(gaian_id, [])
        return history[-1] if history else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, canonical: str) -> str:
        return hmac.new(
            self._key,
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
