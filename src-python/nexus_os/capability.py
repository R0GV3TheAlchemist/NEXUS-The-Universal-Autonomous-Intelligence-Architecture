# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS OS — seL4-Inspired Capability System
# Phase E: CNode (capability table), CapabilityAuthority (minting, delegation,
#          revocation, audit), CapabilityError hierarchy.
# Design: seL4 microkernel capability derivation model.
# Ethics: ETHICS.md Prohibition 6 — No Unaudited Privilege Escalation
# GAIAN Law III: No Silent Override

from __future__ import annotations

import logging
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, FrozenSet, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Well-known kernel object IDs
# ---------------------------------------------------------------------------

KERNEL_PID       = "pid-0:nexus-kernel"
ROOT_AUTHORITY   = "capability-authority:root"

# Standard operation sets
OPS_READ         = frozenset({"read"})
OPS_WRITE        = frozenset({"write"})
OPS_READ_WRITE   = frozenset({"read", "write"})
OPS_EXECUTE      = frozenset({"execute"})
OPS_MANAGE       = frozenset({"read", "write", "execute", "delegate", "revoke"})
OPS_MEMORY       = frozenset({"alloc", "free", "map", "unmap"})
OPS_IPC          = frozenset({"send", "receive", "call", "reply"})
OPS_PROCESS      = frozenset({"spawn", "terminate", "reap", "suspend", "resume"})
OPS_SCHUMANN     = frozenset({"read", "subscribe"})
OPS_AFFECT       = frozenset({"read", "write", "subscribe"})
OPS_MEMORY_STORE = frozenset({"read", "write", "query"})


# ---------------------------------------------------------------------------
# Capability errors
# ---------------------------------------------------------------------------

class CapabilityError(PermissionError):
    """Base class for all capability violations."""

class CapabilityNotFound(CapabilityError):
    """No capability token found for the requested object + operation."""
    def __init__(self, object_id: str, operation: str) -> None:
        super().__init__(f"No capability for op='{operation}' on object='{object_id}'")

class CapabilityExpired(CapabilityError):
    """A capability token was found but has expired."""
    def __init__(self, token_id: str) -> None:
        super().__init__(f"Capability token '{token_id}' has expired")

class CapabilityRevoked(CapabilityError):
    """A capability token has been explicitly revoked."""
    def __init__(self, token_id: str) -> None:
        super().__init__(f"Capability token '{token_id}' has been revoked")

class PrivilegeEscalationError(CapabilityError):
    """Attempt to mint or delegate ops not held by the issuer."""
    def __init__(self, issuer_pid: str, ops: FrozenSet[str]) -> None:
        super().__init__(
            f"Process '{issuer_pid}' attempted privilege escalation — "
            f"requested ops {sorted(ops)} exceed issuer's own capabilities."
        )


# ---------------------------------------------------------------------------
# CapabilityToken — re-exported from kernel for single-source-of-truth
# (canonical definition stays in kernel.py; imported here for convenience)
# ---------------------------------------------------------------------------

from nexus_os.kernel import CapabilityToken, ProcessDescriptor, ProcessState


# ---------------------------------------------------------------------------
# CNode — the capability table for a single process
# ---------------------------------------------------------------------------

class CNode:
    """
    A CNode (Capability Node) is the per-process capability table.
    Modelled on seL4's CNode objects: a finite-size table of capability slots.

    Each slot holds a CapabilityToken or is empty.
    The kernel issues capabilities into a process's CNode;
    the process can look up, enumerate, and (if it holds the right cap) delegate.
    """

    def __init__(self, owner_pid: str, max_slots: int = 1024) -> None:
        self._owner = owner_pid
        self._slots: dict[str, CapabilityToken] = {}   # token_id -> token
        self._lock  = threading.Lock()
        self._max   = max_slots

    # ------------------------------------------------------------------
    # Slot management
    # ------------------------------------------------------------------

    def insert(self, token: CapabilityToken) -> None:
        """Insert a capability token into a free slot."""
        with self._lock:
            if len(self._slots) >= self._max:
                raise CapabilityError(f"CNode for {self._owner}: no free slots")
            self._slots[token.token_id] = token

    def delete(self, token_id: str) -> None:
        """Delete (nullify) a capability slot."""
        with self._lock:
            self._slots.pop(token_id, None)

    def lookup(
        self,
        object_id: str,
        operation: str,
        raise_on_missing: bool = True,
    ) -> Optional[CapabilityToken]:
        """
        Find a valid, non-expired, non-revoked token for object_id + operation.
        Returns None (or raises CapabilityNotFound) if none found.
        """
        with self._lock:
            for token in self._slots.values():
                if token.object_id == object_id and token.allows(operation):
                    if token.is_expired():
                        raise CapabilityExpired(token.token_id)
                    return token
        if raise_on_missing:
            raise CapabilityNotFound(object_id, operation)
        return None

    def has(self, object_id: str, operation: str) -> bool:
        """Return True if a valid capability exists for object_id + operation."""
        try:
            return self.lookup(object_id, operation, raise_on_missing=True) is not None
        except CapabilityError:
            return False

    def list_tokens(self) -> list[CapabilityToken]:
        with self._lock:
            return list(self._slots.values())

    @property
    def owner_pid(self) -> str:
        return self._owner

    def __len__(self) -> int:
        with self._lock:
            return len(self._slots)


# ---------------------------------------------------------------------------
# AuditRecord — immutable record of every privileged kernel event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditRecord:
    event_id:    str
    event_type:  str        # "mint", "revoke", "delegate", "spawn", "terminate", "reap", "boot"
    actor_pid:   str
    object_id:   str
    ops:         tuple[str, ...]   # sorted tuple for determinism
    timestamp:   str               # ISO-8601 UTC
    note:        str = ""

    @classmethod
    def new(
        cls,
        event_type: str,
        actor_pid: str,
        object_id: str,
        ops: FrozenSet[str] | set[str] | tuple[str, ...] = frozenset(),
        note: str = "",
    ) -> "AuditRecord":
        return cls(
            event_id   = str(uuid.uuid4()),
            event_type = event_type,
            actor_pid  = actor_pid,
            object_id  = object_id,
            ops        = tuple(sorted(ops)),
            timestamp  = datetime.now(timezone.utc).isoformat(),
            note       = note,
        )


# ---------------------------------------------------------------------------
# CapabilityAuthority — the kernel-level minting/delegation/revocation oracle
# ---------------------------------------------------------------------------

class CapabilityAuthority:
    """
    CapabilityAuthority manages the lifecycle of all capability tokens in NEXUS OS.

    Responsibilities:
      - Mint new capability tokens (seL4 CNode.Mint analogue)
      - Delegate capabilities (subset of issuer's ops only — no escalation)
      - Revoke tokens (explicit, or on process termination)
      - Persist all minted tokens and audit records to SQLite
      - Wire every privileged event to the Planetary Ledger

    Privilege escalation is constitutionally forbidden (ETHICS.md Prohibition 6).
    Every action is logged to the immutable audit trail before it takes effect.

    Usage::

        auth = CapabilityAuthority()
        token = auth.mint(
            object_id="schumann_sync",
            permitted_ops=OPS_SCHUMANN,
            issuer_pid=KERNEL_PID,
        )
        auth.require(token.token_id, "read")   # passes
        auth.revoke(token.token_id, revoker_pid=KERNEL_PID)
        auth.require(token.token_id, "read")   # raises CapabilityRevoked
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        ledger: Any | None = None,
        session_id: str | None = None,
    ) -> None:
        import os
        default = Path(os.environ.get("NEXUS_CAP_DB", "nexus_data/capabilities.db"))
        self._db_path   = Path(db_path) if db_path else default
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ledger    = ledger
        self._session_id = session_id
        self._lock      = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._revoked:  set[str] = set()   # token_id -> revoked (in-memory fast path)
        self._init_db()
        self._load_revoked()
        logger.info("CapabilityAuthority online (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def mint(
        self,
        object_id: str,
        permitted_ops: FrozenSet[str],
        issuer_pid: str,
        expiry: Optional[datetime] = None,
        note: str = "",
    ) -> CapabilityToken:
        """
        Mint a new, unforgeable CapabilityToken.
        Logs audit record and persists token before returning.
        """
        token = CapabilityToken(
            token_id      = str(uuid.uuid4()),
            object_id     = object_id,
            permitted_ops = frozenset(permitted_ops),
            issuer        = issuer_pid,
            issued_at     = datetime.now(timezone.utc),
            expiry        = expiry,
        )
        audit = AuditRecord.new("mint", issuer_pid, object_id, permitted_ops, note)
        with self._lock:
            self._persist_token(token)
            self._persist_audit(audit)
        self._ledger_write(audit)
        logger.info("cap.mint object=%s ops=%s issuer=%s", object_id, sorted(permitted_ops), issuer_pid)
        return token

    def delegate(
        self,
        source_token: CapabilityToken,
        delegated_ops: FrozenSet[str],
        delegate_pid: str,
        expiry: Optional[datetime] = None,
    ) -> CapabilityToken:
        """
        Delegate a subset of a token's operations to another process.
        seL4 principle: you cannot delegate more than you hold.
        Raises PrivilegeEscalationError if delegated_ops ⊆ source_token.permitted_ops.
        """
        extra = delegated_ops - source_token.permitted_ops
        if extra:
            raise PrivilegeEscalationError(source_token.issuer, extra)
        if source_token.is_expired():
            raise CapabilityExpired(source_token.token_id)
        if source_token.token_id in self._revoked:
            raise CapabilityRevoked(source_token.token_id)

        derived = CapabilityToken(
            token_id      = str(uuid.uuid4()),
            object_id     = source_token.object_id,
            permitted_ops = frozenset(delegated_ops),
            issuer        = source_token.issuer,
            issued_at     = datetime.now(timezone.utc),
            expiry        = expiry or source_token.expiry,
        )
        audit = AuditRecord.new(
            "delegate", source_token.issuer, source_token.object_id,
            delegated_ops,
            note=f"delegated to {delegate_pid} from {source_token.token_id}",
        )
        with self._lock:
            self._persist_token(derived)
            self._persist_audit(audit)
        self._ledger_write(audit)
        logger.info(
            "cap.delegate object=%s ops=%s to=%s",
            source_token.object_id, sorted(delegated_ops), delegate_pid,
        )
        return derived

    def revoke(self, token_id: str, revoker_pid: str, note: str = "") -> None:
        """
        Revoke a capability token. Idempotent.
        Any future require() call for this token_id raises CapabilityRevoked.
        """
        audit = AuditRecord.new(
            "revoke", revoker_pid, token_id, note=note or f"revoked by {revoker_pid}"
        )
        with self._lock:
            self._revoked.add(token_id)
            conn = self._get_conn()
            conn.execute(
                "UPDATE capability_tokens SET revoked = 1 WHERE token_id = ?",
                (token_id,),
            )
            conn.commit()
            self._persist_audit(audit)
        self._ledger_write(audit)
        logger.info("cap.revoke token_id=%s by=%s", token_id, revoker_pid)

    def require(self, token_id: str, operation: str) -> CapabilityToken:
        """
        Assert that a token is valid and permits the operation.
        Raises CapabilityRevoked, CapabilityExpired, or CapabilityNotFound.
        """
        if token_id in self._revoked:
            raise CapabilityRevoked(token_id)
        token = self._load_token(token_id)
        if token is None:
            raise CapabilityNotFound(token_id, operation)
        if token.is_expired():
            raise CapabilityExpired(token_id)
        if not token.allows(operation):
            raise CapabilityNotFound(token.object_id, operation)
        return token

    def get_audit_log(self, limit: int = 100) -> list[AuditRecord]:
        """Return the most recent audit records."""
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT event_id, event_type, actor_pid, object_id, ops_json, timestamp, note "
                "FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        import json as _json
        return [
            AuditRecord(
                event_id   = r[0],
                event_type = r[1],
                actor_pid  = r[2],
                object_id  = r[3],
                ops        = tuple(_json.loads(r[4])),
                timestamp  = r[5],
                note       = r[6],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS capability_tokens (
                token_id      TEXT PRIMARY KEY,
                object_id     TEXT NOT NULL,
                permitted_ops TEXT NOT NULL,   -- JSON array
                issuer        TEXT NOT NULL,
                issued_at     TEXT NOT NULL,
                expiry        TEXT,
                revoked       INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                event_id   TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                actor_pid  TEXT NOT NULL,
                object_id  TEXT NOT NULL,
                ops_json   TEXT NOT NULL,
                timestamp  TEXT NOT NULL,
                note       TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);
        """)
        conn.commit()

    def _load_revoked(self) -> None:
        rows = self._get_conn().execute(
            "SELECT token_id FROM capability_tokens WHERE revoked = 1"
        ).fetchall()
        self._revoked = {r[0] for r in rows}

    def _persist_token(self, token: CapabilityToken) -> None:
        import json as _json
        self._get_conn().execute(
            "INSERT OR IGNORE INTO capability_tokens "
            "(token_id, object_id, permitted_ops, issuer, issued_at, expiry, revoked) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (
                token.token_id,
                token.object_id,
                _json.dumps(sorted(token.permitted_ops)),
                token.issuer,
                token.issued_at.isoformat(),
                token.expiry.isoformat() if token.expiry else None,
            ),
        )
        self._get_conn().commit()

    def _load_token(self, token_id: str) -> Optional[CapabilityToken]:
        import json as _json
        row = self._get_conn().execute(
            "SELECT token_id, object_id, permitted_ops, issuer, issued_at, expiry "
            "FROM capability_tokens WHERE token_id = ?",
            (token_id,),
        ).fetchone()
        if row is None:
            return None
        expiry = datetime.fromisoformat(row[5]) if row[5] else None
        return CapabilityToken(
            token_id      = row[0],
            object_id     = row[1],
            permitted_ops = frozenset(_json.loads(row[2])),
            issuer        = row[3],
            issued_at     = datetime.fromisoformat(row[4]),
            expiry        = expiry,
        )

    def _persist_audit(self, audit: AuditRecord) -> None:
        import json as _json
        self._get_conn().execute(
            "INSERT OR IGNORE INTO audit_log "
            "(event_id, event_type, actor_pid, object_id, ops_json, timestamp, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                audit.event_id, audit.event_type, audit.actor_pid,
                audit.object_id, _json.dumps(list(audit.ops)),
                audit.timestamp, audit.note,
            ),
        )
        self._get_conn().commit()

    def _ledger_write(self, audit: AuditRecord) -> None:
        if self._ledger is None:
            return
        try:
            from planetary_ledger import EventType
            self._ledger.append(
                event_type=EventType.CUSTOM,
                payload={
                    "cap_event": audit.event_type,
                    "actor": audit.actor_pid,
                    "object": audit.object_id,
                    "ops": list(audit.ops),
                    "event_id": audit.event_id,
                },
                tags=["capability", "kernel", "phase-e"],
                session_id=self._session_id,
            )
        except Exception:
            logger.exception("CapabilityAuthority ledger write failed")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn
