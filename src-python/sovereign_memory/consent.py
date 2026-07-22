# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Sovereign Memory — Consent Gate
# Phase E: The consent gate is the constitutional enforcer of Memory Sovereignty.
# Every write and read operation passes through here first.
# GAIAN Law II: Memory Sovereignty — no memory is written without consent.

from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Consent model
# ---------------------------------------------------------------------------

class ConsentScope(str, Enum):
    """Granular consent scopes. Owner grants each independently."""
    EPISODIC_WRITE = "episodic_write"
    EPISODIC_READ  = "episodic_read"
    SEMANTIC_WRITE = "semantic_write"
    SEMANTIC_READ  = "semantic_read"
    BIOMETRIC_WRITE = "biometric_write"
    BIOMETRIC_READ  = "biometric_read"
    LEDGER_WRITE   = "ledger_write"
    ALL            = "all"           # Omnibus grant — covers all scopes


class ConsentDecision(str, Enum):
    GRANTED = "granted"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class ConsentRecord:
    scope: ConsentScope
    decision: ConsentDecision
    granted_by: str             # e.g. "owner", "operator", "bootstrap"
    granted_at: str             # ISO-8601 UTC
    expires_at: str | None = None
    note: str = ""

    def is_active(self) -> bool:
        if self.decision != ConsentDecision.GRANTED:
            return False
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc).isoformat() <= self.expires_at


# ---------------------------------------------------------------------------
# ConsentDenied exception
# ---------------------------------------------------------------------------

class ConsentDenied(PermissionError):
    """Raised when an operation is attempted without valid consent."""
    def __init__(self, scope: ConsentScope, detail: str = "") -> None:
        self.scope = scope
        msg = f"Consent denied for scope '{scope.value}'"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


# ---------------------------------------------------------------------------
# ConsentGate — the enforcer
# ---------------------------------------------------------------------------

class ConsentGate:
    """
    SQLite-backed consent registry.
    Persists consent records across restarts.
    Thread-safe.  Every check raises ConsentDenied on failure.

    GAIAN Law II: No memory operation proceeds without an active consent
    record for the required scope (or ConsentScope.ALL).

    Usage::

        gate = ConsentGate(db_path="nexus_data/consent.db")
        gate.grant(ConsentScope.EPISODIC_WRITE, granted_by="owner")
        gate.require(ConsentScope.EPISODIC_WRITE)   # passes
        gate.revoke(ConsentScope.EPISODIC_WRITE)
        gate.require(ConsentScope.EPISODIC_WRITE)   # raises ConsentDenied
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        from pathlib import Path as _Path
        import os
        default = _Path(os.environ.get("NEXUS_CONSENT_DB", "nexus_data/consent.db"))
        self._db_path = _Path(db_path) if db_path else default
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._init_db()
        self._bootstrap_defaults()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grant(
        self,
        scope: ConsentScope,
        granted_by: str = "owner",
        expires_at: str | None = None,
        note: str = "",
    ) -> ConsentRecord:
        """Grant consent for a scope. Idempotent — safe to call multiple times."""
        now = datetime.now(timezone.utc).isoformat()
        record = ConsentRecord(
            scope=scope,
            decision=ConsentDecision.GRANTED,
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
            note=note,
        )
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO consent_records "
                "(scope, decision, granted_by, granted_at, expires_at, note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (scope.value, record.decision.value, granted_by, now, expires_at, note),
            )
            conn.commit()
        logger.info("consent.grant scope=%s by=%s", scope.value, granted_by)
        return record

    def revoke(self, scope: ConsentScope, revoked_by: str = "owner") -> None:
        """Revoke consent for a scope."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO consent_records "
                "(scope, decision, granted_by, granted_at, expires_at, note) "
                "VALUES (?, ?, ?, ?, NULL, ?)",
                (scope.value, ConsentDecision.REVOKED.value, revoked_by, now, f"revoked by {revoked_by}"),
            )
            conn.commit()
        logger.info("consent.revoke scope=%s by=%s", scope.value, revoked_by)

    def check(self, scope: ConsentScope) -> bool:
        """Return True if scope (or ALL) is actively granted."""
        with self._lock:
            return self._is_granted(scope)

    def require(self, scope: ConsentScope) -> None:
        """Assert consent is active. Raises ConsentDenied if not."""
        with self._lock:
            if not self._is_granted(scope):
                raise ConsentDenied(scope)

    def status(self) -> dict[str, str]:
        """Return current consent status for all scopes."""
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT scope, decision, expires_at FROM consent_records"
            ).fetchall()
            result: dict[str, str] = {}
            for scope_val, decision, expires_at in rows:
                now = datetime.now(timezone.utc).isoformat()
                if decision == ConsentDecision.GRANTED.value:
                    if expires_at is None or now <= expires_at:
                        result[scope_val] = "active"
                    else:
                        result[scope_val] = "expired"
                else:
                    result[scope_val] = decision
            return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_granted(self, scope: ConsentScope) -> bool:
        """Must be called under self._lock."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        # Check the specific scope OR the omnibus ALL grant
        for s in (scope.value, ConsentScope.ALL.value):
            row = conn.execute(
                "SELECT decision, expires_at FROM consent_records WHERE scope = ?",
                (s,),
            ).fetchone()
            if row:
                decision, expires_at = row
                if decision == ConsentDecision.GRANTED.value:
                    if expires_at is None or now <= expires_at:
                        return True
        return False

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consent_records (
                scope       TEXT PRIMARY KEY,
                decision    TEXT NOT NULL,
                granted_by  TEXT NOT NULL,
                granted_at  TEXT NOT NULL,
                expires_at  TEXT,
                note        TEXT DEFAULT ''
            )
        """)
        conn.commit()

    def _bootstrap_defaults(self) -> None:
        """
        On first run, grant all scopes by default under 'bootstrap' authority.
        This follows GAIAN Law II: the system starts in an open-consent state
        and the owner may selectively revoke scopes at runtime.
        """
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM consent_records").fetchone()
        if row[0] == 0:
            logger.info("consent.bootstrap granting all scopes (first run)")
            self.grant(ConsentScope.ALL, granted_by="bootstrap", note="Initial open-consent state")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn
