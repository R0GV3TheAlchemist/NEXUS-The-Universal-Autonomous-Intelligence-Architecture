"""
core/infra/sqlite_lifecycle_repository.py
C17 / C23 / C27 — SQLite-backed LifecycleRepository

Drop-in persistent replacement for InMemoryLifecycleRepository.
Uses Python's stdlib ``sqlite3`` — no additional dependencies required.

Schema (auto-created on first instantiation)
--------------------------------------------

  gaian_lifecycle_state
    gaian_id    TEXT PRIMARY KEY
    state       TEXT NOT NULL
    changed_at  TEXT NOT NULL   (ISO-8601 UTC)

  lifecycle_audit_log
    id          INTEGER PRIMARY KEY AUTOINCREMENT
    gaian_id    TEXT NOT NULL
    seq         INTEGER NOT NULL
    event_type  TEXT NOT NULL
    payload     TEXT NOT NULL   (JSON)
    logged_at   TEXT NOT NULL
    hmac_sig    TEXT            (hex, may be NULL for legacy entries)

Thread safety
-------------
check_same_thread=False is set; every public method opens a connection
using the shared DB path so that threads each get their own sqlite3
connection object. WAL journal mode is enabled for concurrent reads.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from core.lifecycle.gaian_lifecycle_state import GAIANLifecycleState
from core.lifecycle.lifecycle_audit_logger import LifecycleEvent
from core.lifecycle.repositories import LifecycleRepository

_DDL = """
CREATE TABLE IF NOT EXISTS gaian_lifecycle_state (
    gaian_id   TEXT PRIMARY KEY,
    state      TEXT NOT NULL,
    changed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lifecycle_audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    gaian_id   TEXT    NOT NULL,
    seq        INTEGER NOT NULL,
    event_type TEXT    NOT NULL,
    payload    TEXT    NOT NULL,
    logged_at  TEXT    NOT NULL,
    hmac_sig   TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_gaian
    ON lifecycle_audit_log (gaian_id, id);
"""


class SqliteLifecycleRepository(LifecycleRepository):
    """
    SQLite-backed lifecycle state + audit log repository.

    Parameters
    ----------
    db_path :
        Path to the SQLite database file, or ``':memory:'`` for an
        in-process ephemeral database (useful for integration tests).
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._bootstrap()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _bootstrap(self) -> None:
        with self._connect() as conn:
            conn.executescript(_DDL)

    @staticmethod
    def _event_to_row(event: LifecycleEvent) -> dict:
        payload = {
            "gaian_id":   event.gaian_id,
            "event_type": event.event_type,
            "from_state": event.from_state.value if event.from_state else None,
            "to_state":   event.to_state.value   if event.to_state   else None,
            "actor_id":   event.actor_id,
            "metadata":   event.metadata,
        }
        return {
            "gaian_id":   event.gaian_id,
            "seq":        event.seq,
            "event_type": event.event_type,
            "payload":    json.dumps(payload),
            "logged_at":  event.logged_at,
            "hmac_sig":   event.hmac_sig,
        }

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> LifecycleEvent:
        payload = json.loads(row["payload"])

        def _state(v):
            return GAIANLifecycleState(v) if v else None

        return LifecycleEvent(
            gaian_id=row["gaian_id"],
            seq=row["seq"],
            event_type=row["event_type"],
            from_state=_state(payload.get("from_state")),
            to_state=_state(payload.get("to_state")),
            actor_id=payload.get("actor_id"),
            metadata=payload.get("metadata", {}),
            logged_at=row["logged_at"],
            hmac_sig=row["hmac_sig"],
        )

    # ------------------------------------------------------------------
    # LifecycleRepository interface
    # ------------------------------------------------------------------

    def save_state(
        self,
        gaian_id:   str,
        state:      GAIANLifecycleState,
        changed_at: datetime,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO gaian_lifecycle_state (gaian_id, state, changed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(gaian_id) DO UPDATE SET
                    state      = excluded.state,
                    changed_at = excluded.changed_at
                """,
                (gaian_id, state.value, changed_at.isoformat()),
            )

    def load_state(self, gaian_id: str) -> Optional[GAIANLifecycleState]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state FROM gaian_lifecycle_state WHERE gaian_id = ?",
                (gaian_id,),
            ).fetchone()
        return GAIANLifecycleState(row["state"]) if row else None

    def save_audit_event(self, gaian_id: str, event: LifecycleEvent) -> None:
        row = self._event_to_row(event)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO lifecycle_audit_log
                    (gaian_id, seq, event_type, payload, logged_at, hmac_sig)
                VALUES
                    (:gaian_id, :seq, :event_type, :payload, :logged_at, :hmac_sig)
                """,
                row,
            )

    def load_audit_log(self, gaian_id: str) -> List[LifecycleEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT gaian_id, seq, event_type, payload, logged_at, hmac_sig
                FROM   lifecycle_audit_log
                WHERE  gaian_id = ?
                ORDER  BY id ASC
                """,
                (gaian_id,),
            ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def all_gaian_ids(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT gaian_id FROM gaian_lifecycle_state"
            ).fetchall()
        return [r["gaian_id"] for r in rows]
