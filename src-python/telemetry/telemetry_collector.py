"""Issue #188 — TelemetryCollector: append-only SQLite store + Glass Room stream.

Canon C05: Transparency — every event is persisted and queryable.
Canon C01: Sovereignty — user can export all telemetry and request erasure.
Canon C30: No silent failures — failed emit never crashes the calling engine.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from .telemetry_event import RiskTier, TelemetryEvent

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path.home() / ".gaia" / "telemetry" / "events.db"

_CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id     TEXT PRIMARY KEY,
    timestamp    REAL NOT NULL,
    source       TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    risk_tier    TEXT NOT NULL,
    trust_tier   TEXT NOT NULL,
    session_id   TEXT,
    skill_id     TEXT,
    degraded     INTEGER DEFAULT 0,
    conflict_detected INTEGER DEFAULT 0,
    dq_score     REAL,
    latency_ms   REAL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_timestamp ON telemetry_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_session    ON telemetry_events(session_id);
CREATE INDEX IF NOT EXISTS idx_source     ON telemetry_events(source);
CREATE INDEX IF NOT EXISTS idx_risk_tier  ON telemetry_events(risk_tier);
"""


class TelemetryCollector:
    """Receives TelemetryEvents from all GAIA engines, persists to SQLite,
    streams to Glass Room subscribers, and indexes YELLOW/RED events in Crystal.

    Thread-safety: all writes go through asyncio; SQLite is opened in
    check_same_thread=False with WAL mode for concurrent reads.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        crystal_indexer: Any | None = None,
    ) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._crystal = crystal_indexer
        self._subscribers: list[Callable[[TelemetryEvent], None]] = []
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_CREATE_EVENTS_TABLE)
        self._conn.commit()
        logger.info("[TelemetryCollector] Started. DB: %s", self._db_path)

    async def stop(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Emit
    # ------------------------------------------------------------------

    async def emit(self, event: TelemetryEvent | dict[str, Any]) -> None:
        """Ingest a telemetry event. Never raises — Canon C30."""
        try:
            if isinstance(event, dict):
                event = _dict_to_event(event)
            self._auto_flag_risk(event)
            await self._persist(event)
            self._broadcast(event)
            if event.index_in_crystal and self._crystal:
                await self._index_in_crystal(event)
        except Exception as exc:
            logger.error("[TelemetryCollector] emit failed: %s", exc)

    def _auto_flag_risk(self, event: TelemetryEvent) -> None:
        """Auto-promote risk tier and Crystal indexing for YELLOW/RED events."""
        if event.conflict_type in ("SAFETY_ETHICAL_OVERRIDE",):
            event.risk_tier = RiskTier.RED
            event.index_in_crystal = True
        elif event.degraded or event.conflict_detected:
            if event.risk_tier == RiskTier.GREEN:
                event.risk_tier = RiskTier.YELLOW
            event.index_in_crystal = True

    async def _persist(self, event: TelemetryEvent) -> None:
        if not self._conn:
            return
        row = (
            event.event_id,
            event.timestamp,
            event.source if isinstance(event.source, str) else event.source.value,
            event.event_type,
            event.risk_tier if isinstance(event.risk_tier, str) else event.risk_tier.value,
            event.trust_tier if isinstance(event.trust_tier, str) else event.trust_tier.value,
            event.session_id,
            event.skill_id,
            int(event.degraded),
            int(event.conflict_detected),
            event.dq_score,
            event.latency_ms,
            json.dumps(event.payload),
        )
        self._conn.execute(
            """INSERT OR IGNORE INTO telemetry_events
               (event_id, timestamp, source, event_type, risk_tier, trust_tier,
                session_id, skill_id, degraded, conflict_detected, dq_score, latency_ms, payload_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
        self._conn.commit()

    def _broadcast(self, event: TelemetryEvent) -> None:
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception:
                pass

    async def _index_in_crystal(self, event: TelemetryEvent) -> None:
        try:
            await self._crystal.index_event(event)
        except Exception as exc:
            logger.warning("[TelemetryCollector] Crystal indexing failed: %s", exc)

    # ------------------------------------------------------------------
    # Glass Room real-time subscriptions
    # ------------------------------------------------------------------

    def subscribe(self, callback: Callable[[TelemetryEvent], None]) -> None:
        """Register a real-time Glass Room subscriber."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[TelemetryEvent], None]) -> None:
        self._subscribers = [s for s in self._subscribers if s is not callback]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def query(
        self,
        session_id: str | None = None,
        source: str | None = None,
        risk_tier: str | None = None,
        since: float | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Query telemetry events with optional filters."""
        if not self._conn:
            return []
        clauses, params = [], []
        if session_id:
            clauses.append("session_id = ?"); params.append(session_id)
        if source:
            clauses.append("source = ?"); params.append(source)
        if risk_tier:
            clauses.append("risk_tier = ?"); params.append(risk_tier)
        if since:
            clauses.append("timestamp >= ?"); params.append(since)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn.execute(
            f"SELECT * FROM telemetry_events {where} ORDER BY timestamp DESC LIMIT ?",
            [*params, limit],
        ).fetchall()
        cols = [d[0] for d in self._conn.execute(
            "SELECT * FROM telemetry_events LIMIT 0"
        ).description or []]
        return [dict(zip(cols, row)) for row in rows]

    # ------------------------------------------------------------------
    # Export + Erasure (Canon C01)
    # ------------------------------------------------------------------

    def export_session(self, session_id: str) -> list[dict[str, Any]]:
        """Export all events for a session as JSON-serializable dicts."""
        return self.query(session_id=session_id, limit=10_000)

    def delete_session(self, session_id: str) -> int:
        """Delete all telemetry for a session. Returns row count deleted."""
        if not self._conn:
            return 0
        cursor = self._conn.execute(
            "DELETE FROM telemetry_events WHERE session_id = ?",
            (session_id,),
        )
        self._conn.commit()
        logger.info(
            "[TelemetryCollector] Erased %d events for session '%s' (Canon C01)",
            cursor.rowcount, session_id,
        )
        return cursor.rowcount


def _dict_to_event(d: dict[str, Any]) -> TelemetryEvent:
    """Convert a raw dict emitted by SelfHealingEngine or other sources."""
    from .telemetry_event import TelemetrySource, TrustTier, RiskTier
    e = TelemetryEvent()
    for k, v in d.items():
        if hasattr(e, k):
            setattr(e, k, v)
    return e
