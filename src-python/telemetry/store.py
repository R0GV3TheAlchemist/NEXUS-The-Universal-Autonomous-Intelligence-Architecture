"""Append-only SQLite store for TelemetryEvents.

Design contract (Canon C01 — Sovereignty, Canon C05 — Transparency):
- Rows are never updated or deleted by the system.
- Deletion is available only via user-initiated right-to-erasure (Issue #127).
- The file is local-only; no sync or transmission.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import TelemetryEvent, SkillHealthReport, DecisionQualityRecord


DEFAULT_DB_PATH = Path.home() / ".gaia" / "telemetry.db"


CREATE_EVENTS_SQL = """
CREATE TABLE IF NOT EXISTS telemetry_events (
    id                TEXT PRIMARY KEY,
    timestamp         TEXT NOT NULL,
    session_id        TEXT NOT NULL DEFAULT '',
    source            TEXT NOT NULL DEFAULT '',
    event_type        TEXT NOT NULL DEFAULT '',
    skill_id          TEXT,
    trust_tier        TEXT,
    intent_class      TEXT,
    risk_tier         TEXT,
    input_summary     TEXT NOT NULL DEFAULT '',
    output_summary    TEXT NOT NULL DEFAULT '',
    duration_ms       INTEGER NOT NULL DEFAULT 0,
    dq_score          REAL,
    degraded          INTEGER NOT NULL DEFAULT 0,
    fallback_mode     TEXT,
    biometric_context TEXT,
    planetary_context TEXT,
    canon_refs        TEXT NOT NULL DEFAULT '',
    tags              TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_te_session ON telemetry_events(session_id);
CREATE INDEX IF NOT EXISTS idx_te_source  ON telemetry_events(source);
CREATE INDEX IF NOT EXISTS idx_te_ts      ON telemetry_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_te_risk    ON telemetry_events(risk_tier);
"""


class TelemetryStore:
    """Thread-safe, append-only SQLite store."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(CREATE_EVENTS_SQL)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def insert(self, event: TelemetryEvent) -> None:
        """Append a single TelemetryEvent. Never updates existing rows."""
        d = event.to_dict()
        d["degraded"] = int(d["degraded"])  # SQLite has no bool
        cols = ", ".join(d.keys())
        placeholders = ", ".join(f":{k}" for k in d.keys())
        sql = f"INSERT OR IGNORE INTO telemetry_events ({cols}) VALUES ({placeholders})"
        with self._conn:
            self._conn.execute(sql, d)

    # ------------------------------------------------------------------
    # Read — session trace
    # ------------------------------------------------------------------

    def get_session_trace(self, session_id: str) -> list[TelemetryEvent]:
        """Return all events for a session ordered chronologically."""
        rows = self._conn.execute(
            "SELECT * FROM telemetry_events WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    # ------------------------------------------------------------------
    # Read — skill health
    # ------------------------------------------------------------------

    def get_skill_health(self, skill_id: str, window_minutes: int = 60) -> SkillHealthReport:
        """Compute a SkillHealthReport from recent events."""
        since = (datetime.utcnow() - timedelta(minutes=window_minutes)).isoformat()
        rows = self._conn.execute(
            """
            SELECT event_type, degraded, duration_ms, timestamp
            FROM telemetry_events
            WHERE skill_id = ? AND timestamp >= ?
            ORDER BY timestamp
            """,
            (skill_id, since),
        ).fetchall()

        total = len(rows)
        errors = sum(1 for r in rows if r["event_type"] == "job_failed")
        fallbacks = sum(1 for r in rows if r["degraded"])
        avg_dur = (sum(r["duration_ms"] for r in rows) / total) if total else 0.0
        last_fail_rows = [
            r["timestamp"] for r in rows if r["event_type"] == "job_failed"
        ]
        last_fail = datetime.fromisoformat(last_fail_rows[-1]) if last_fail_rows else None

        return SkillHealthReport(
            skill_id=skill_id,
            total_events=total,
            error_count=errors,
            fallback_count=fallbacks,
            avg_duration_ms=avg_dur,
            error_rate=round(errors / total, 3) if total else 0.0,
            last_failure_at=last_fail,
            window_minutes=window_minutes,
        )

    # ------------------------------------------------------------------
    # Read — DQ history
    # ------------------------------------------------------------------

    def get_dq_history(self, limit: int = 100) -> list[dict]:
        """Return the last N events that have a DQ score, newest first."""
        rows = self._conn.execute(
            """
            SELECT session_id, intent_class, dq_score, timestamp
            FROM telemetry_events
            WHERE dq_score IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Read — recent events (Glass Room live feed seed)
    # ------------------------------------------------------------------

    def get_recent_events(self, limit: int = 50, session_id: Optional[str] = None) -> list[TelemetryEvent]:
        if session_id:
            rows = self._conn.execute(
                "SELECT * FROM telemetry_events WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM telemetry_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_event(r) for r in rows]

    # ------------------------------------------------------------------
    # User-initiated deletion (right to erasure — Canon C01)
    # ------------------------------------------------------------------

    def delete_range(self, since: datetime, until: datetime) -> int:
        """Delete all events in [since, until]. Returns count deleted."""
        cursor = self._conn.execute(
            "DELETE FROM telemetry_events WHERE timestamp >= ? AND timestamp <= ?",
            (since.isoformat(), until.isoformat()),
        )
        self._conn.commit()
        return cursor.rowcount

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_session_json(self, session_id: str) -> str:
        """Export full session trace as JSON string for user download."""
        events = self.get_session_trace(session_id)
        return json.dumps([e.to_dict() for e in events], indent=2, default=str)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _row_to_event(self, row: sqlite3.Row) -> TelemetryEvent:
        d = dict(row)
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        d["degraded"] = bool(d["degraded"])
        d["canon_refs"] = [c for c in d.get("canon_refs", "").split(",") if c]
        d["tags"] = [t for t in d.get("tags", "").split(",") if t]
        return TelemetryEvent(**d)

    def close(self) -> None:
        self._conn.close()
