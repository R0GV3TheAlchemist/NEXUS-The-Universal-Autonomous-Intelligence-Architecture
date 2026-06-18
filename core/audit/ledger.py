"""
core/audit/ledger.py
====================
Tamper-evident append-only ledger of GAIA-OS actions, policy decisions,
memory writes, tool executions, and state snapshots.

Exported names (required by core/__init__.py and gaian_runtime.py):
    ActionLedger              — main ledger class
    AuditEvent                — immutable event dataclass
    EventType                 — enum of recordable event categories
    LedgerVerificationResult  — result of chain-integrity verification
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EventType
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    """Categories of auditable events in GAIA-OS."""

    ACTION_EXECUTED     = "action_executed"
    POLICY_DECISION     = "policy_decision"
    MEMORY_WRITE        = "memory_write"
    MEMORY_READ         = "memory_read"
    TOOL_EXECUTION      = "tool_execution"
    STATE_SNAPSHOT      = "state_snapshot"
    SESSION_START       = "session_start"
    SESSION_END         = "session_end"
    IDENTITY_VERIFIED   = "identity_verified"
    ALIGNMENT_CHECK     = "alignment_check"
    SAFETY_INTERVENTION = "safety_intervention"
    CANON_INVOCATION    = "canon_invocation"
    SYSTEM_EVENT        = "system_event"
    ERROR               = "error"
    CUSTOM              = "custom"


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------

@dataclass
class AuditEvent:
    """
    Immutable record of a single auditable GAIA-OS event.

    Parameters
    ----------
    event_type:     Category of event (EventType member).
    actor:          Who performed the action (e.g. "gaia", "user", "policy").
    action:         Short action name or description.
    outcome:        Result string ("success", "failure", "blocked", …).
    user_id:        Authenticated user identifier (may be empty for system events).
    session_id:     Session the event belongs to.
    justification:  Why GAIA believed the action was justified.
    metadata:       Arbitrary extra context.  Must be JSON-serialisable.
    event_id:       Auto-generated UUIDv4 if not supplied.
    timestamp:      Unix epoch float; defaults to now.
    parent_id:      ID of a parent / preceding event for causal chains.
    """

    event_type:    EventType
    actor:         str
    action:        str
    outcome:       str                  = "success"
    user_id:       str                  = ""
    session_id:    str                  = ""
    justification: str                  = ""
    metadata:      Dict[str, Any]       = field(default_factory=dict)
    event_id:      str                  = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:     float                = field(default_factory=time.time)
    parent_id:     Optional[str]        = None

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id":      self.event_id,
            "event_type":    self.event_type.value,
            "actor":         self.actor,
            "user_id":       self.user_id,
            "session_id":    self.session_id,
            "action":        self.action,
            "outcome":       self.outcome,
            "justification": self.justification,
            "metadata":      self.metadata,
            "timestamp":     self.timestamp,
            "parent_id":     self.parent_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuditEvent":
        return cls(
            event_id      = d["event_id"],
            event_type    = EventType(d["event_type"]),
            actor         = d["actor"],
            user_id       = d.get("user_id", ""),
            session_id    = d.get("session_id", ""),
            action        = d["action"],
            outcome       = d.get("outcome", "success"),
            justification = d.get("justification", ""),
            metadata      = d.get("metadata", {}),
            timestamp     = d.get("timestamp", 0.0),
            parent_id     = d.get("parent_id"),
        )


# ---------------------------------------------------------------------------
# LedgerVerificationResult
# ---------------------------------------------------------------------------

@dataclass
class LedgerVerificationResult:
    """Result of ActionLedger.verify_chain()."""

    valid:         bool
    total_events:  int
    broken_at_seq: Optional[int]   = None   # 1-based sequence number of first broken link
    error_message: Optional[str]   = None

    @property
    def is_intact(self) -> bool:
        return self.valid

    def __bool__(self) -> bool:
        return self.valid


# ---------------------------------------------------------------------------
# ActionLedger
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS audit_events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT    NOT NULL UNIQUE,
    event_type   TEXT    NOT NULL,
    actor        TEXT    NOT NULL,
    user_id      TEXT    NOT NULL DEFAULT '',
    session_id   TEXT    NOT NULL DEFAULT '',
    action       TEXT    NOT NULL,
    outcome      TEXT    NOT NULL DEFAULT 'success',
    justification TEXT   NOT NULL DEFAULT '',
    metadata_json TEXT   NOT NULL DEFAULT '{}',
    timestamp    REAL    NOT NULL,
    parent_id    TEXT,
    payload_hash TEXT    NOT NULL,
    chain_hash   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_session  ON audit_events(session_id);
CREATE INDEX IF NOT EXISTS idx_actor    ON audit_events(actor);
CREATE INDEX IF NOT EXISTS idx_evtype   ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_ts       ON audit_events(timestamp);
"""


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


class ActionLedger:
    """
    Append-only, tamper-evident audit ledger backed by SQLite.

    Each appended event is linked to the previous event's chain_hash
    (SHA-256) so that any post-hoc modification breaks the chain and
    is detected by verify_chain().

    Parameters
    ----------
    db_path : Path to the SQLite file.  Pass ``":memory:"`` for an
              ephemeral in-process ledger (useful in tests).
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn    = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def append(self, event: AuditEvent) -> str:
        """
        Append *event* to the ledger.

        Returns the event_id of the stored record.
        """
        payload_hash = _hash(event.to_json())

        # Chain hash = hash(payload_hash + previous chain_hash)
        prev_hash = self._last_chain_hash()
        chain_hash = _hash(payload_hash + prev_hash)

        try:
            self._conn.execute(
                """
                INSERT INTO audit_events
                    (event_id, event_type, actor, user_id, session_id, action,
                     outcome, justification, metadata_json, timestamp,
                     parent_id, payload_hash, chain_hash)
                VALUES
                    (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.event_id,
                    event.event_type.value,
                    event.actor,
                    event.user_id,
                    event.session_id,
                    event.action,
                    event.outcome,
                    event.justification,
                    json.dumps(event.metadata, sort_keys=True),
                    event.timestamp,
                    event.parent_id,
                    payload_hash,
                    chain_hash,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            logger.warning("audit_ledger: duplicate event_id %s — skipped", event.event_id)

        return event.event_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def recent(
        self,
        limit: int = 50,
        session_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
    ) -> List[AuditEvent]:
        """Return the most recent *limit* events, newest first."""
        query  = "SELECT * FROM audit_events"
        params: list = []
        clauses: list = []

        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type.value)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY seq DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve a single event by ID, or None if not found."""
        row = self._conn.execute(
            "SELECT * FROM audit_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return self._row_to_event(row) if row else None

    def count(self) -> int:
        """Return total number of stored events."""
        return self._conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def verify_chain(self) -> LedgerVerificationResult:
        """
        Walk the entire chain and verify that no record has been tampered with.

        Returns a LedgerVerificationResult indicating whether the chain is intact.
        """
        rows = self._conn.execute(
            "SELECT seq, event_id, payload_hash, chain_hash FROM audit_events ORDER BY seq ASC"
        ).fetchall()

        total = len(rows)
        prev_chain = ""

        for row in rows:
            expected_chain = _hash(row["payload_hash"] + prev_chain)
            if expected_chain != row["chain_hash"]:
                return LedgerVerificationResult(
                    valid=False,
                    total_events=total,
                    broken_at_seq=row["seq"],
                    error_message=(
                        f"Chain broken at seq={row['seq']} event_id={row['event_id']}"
                    ),
                )
            prev_chain = row["chain_hash"]

        return LedgerVerificationResult(valid=True, total_events=total)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        try:
            self._conn.close()
        except Exception:
            pass

    def __enter__(self) -> "ActionLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _last_chain_hash(self) -> str:
        row = self._conn.execute(
            "SELECT chain_hash FROM audit_events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return row["chain_hash"] if row else ""

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> AuditEvent:
        return AuditEvent(
            event_id      = row["event_id"],
            event_type    = EventType(row["event_type"]),
            actor         = row["actor"],
            user_id       = row["user_id"],
            session_id    = row["session_id"],
            action        = row["action"],
            outcome       = row["outcome"],
            justification = row["justification"],
            metadata      = json.loads(row["metadata_json"] or "{}"),
            timestamp     = row["timestamp"],
            parent_id     = row["parent_id"],
        )
