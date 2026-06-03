"""TelemetryCollector — central event bus for all GAIA engines.

Every GAIA module calls await telemetry.emit(event). The collector:
  1. Writes to the local append-only SQLite store.
  2. Broadcasts to all registered Glass Room SSE subscribers.
  3. Queues high-value events for Crystal indexing (Issues #162).

Canon refs:
  C05 — Transparency: every agentic action is auditable.
  C30 — No silent failures: all degradations are captured.
  C01 — Sovereignty: telemetry is local-only, never transmitted.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterator, Optional

from .models import (
    TelemetryEvent,
    SkillHealthReport,
    OrchestrationEfficiency,
    DecisionQualityRecord,
)
from .store import TelemetryStore, DEFAULT_DB_PATH

log = logging.getLogger("gaia.telemetry")

# Risk tiers that warrant Crystal graph indexing
HIGH_VALUE_RISK_TIERS = {"YELLOW", "RED"}


class TelemetryCollector:
    """OS-wide telemetry event bus. Instantiate once; share via dependency injection."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self._store = TelemetryStore(db_path)
        # SSE subscriber queues — each Glass Room client gets its own asyncio.Queue
        self._subscribers: list[asyncio.Queue] = []

    # ------------------------------------------------------------------
    # Core emit — called by every GAIA engine
    # ------------------------------------------------------------------

    async def emit(self, event: TelemetryEvent) -> None:
        """Persist event and broadcast to Glass Room subscribers."""
        try:
            self._store.insert(event)
        except Exception as exc:  # pragma: no cover
            log.error("Telemetry store write failed: %s", exc)

        await self._broadcast(event)

        if self._is_high_value(event):
            await self._queue_crystal_indexing(event)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_session_trace(self, session_id: str) -> list[TelemetryEvent]:
        return self._store.get_session_trace(session_id)

    async def get_skill_health(self, skill_id: str, window_minutes: int = 60) -> SkillHealthReport:
        return self._store.get_skill_health(skill_id, window_minutes)

    async def get_dq_history(self, limit: int = 100) -> list[dict]:
        return self._store.get_dq_history(limit)

    async def get_recent_events(
        self, limit: int = 50, session_id: Optional[str] = None
    ) -> list[TelemetryEvent]:
        return self._store.get_recent_events(limit, session_id)

    # ------------------------------------------------------------------
    # Orchestration Efficiency (OE) metric
    # ------------------------------------------------------------------

    async def compute_oe(self, window: str = "24h") -> OrchestrationEfficiency:
        """Compute Orchestration Efficiency over the requested window."""
        window_map = {"1h": 60, "24h": 1440, "7d": 10080, "30d": 43200}
        minutes = window_map.get(window, 1440)
        since = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()

        rows = self._store._conn.execute(
            """
            SELECT dq_score, duration_ms, degraded,
                   (SELECT COUNT(*) FROM json_each(tags) WHERE value LIKE 'engines:%') AS _unused
            FROM telemetry_events
            WHERE source = 'synergy_orchestrator'
              AND event_type = 'job_completed'
              AND timestamp >= ?
            """,
            (since,),
        ).fetchall()

        if not rows:
            return OrchestrationEfficiency(window=window)

        total = len(rows)
        successful = sum(1 for r in rows if not r["degraded"])
        avg_latency = sum(r["duration_ms"] for r in rows) / total / 1000.0
        dq_scores = [r["dq_score"] for r in rows if r["dq_score"] is not None]
        avg_dq = sum(dq_scores) / len(dq_scores) if dq_scores else 0.0
        degraded_frac = round(sum(1 for r in rows if r["degraded"]) / total, 3)

        # Engine count comes from tags formatted as "engines:N"
        engine_counts = []
        for r in rows:
            # tags column is a comma-separated string
            for tag in (self._store._conn.execute(
                "SELECT tags FROM telemetry_events WHERE duration_ms = ? LIMIT 1",
                (r["duration_ms"],)
            ).fetchone() or {"tags": ""}):
                pass  # simplified — engine count defaulted to 1 if tag absent
        avg_engines = 1.0  # refined by Issue #190's OE record enrichment

        oe = OrchestrationEfficiency(
            window=window,
            total_tasks=total,
            successful_tasks=successful,
            failed_tasks=total - successful,
            avg_total_latency_s=round(avg_latency, 3),
            avg_engine_count=avg_engines,
            avg_dq_score=round(avg_dq, 3),
            degraded_fraction=degraded_frac,
        )
        oe.compute_oe()
        return oe

    # ------------------------------------------------------------------
    # User export / deletion
    # ------------------------------------------------------------------

    async def export_session_json(self, session_id: str) -> str:
        return self._store.export_session_json(session_id)

    async def delete_range(self, since: datetime, until: datetime) -> int:
        return self._store.delete_range(since, until)

    # ------------------------------------------------------------------
    # Glass Room SSE subscription
    # ------------------------------------------------------------------

    def subscribe(self) -> asyncio.Queue:
        """Register a new Glass Room SSE subscriber. Returns its queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """Remove a subscriber (called when SSE client disconnects)."""
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    async def stream_events(self, q: asyncio.Queue) -> AsyncIterator[TelemetryEvent]:
        """Async generator for SSE streaming — yields events as they arrive."""
        while True:
            event = await q.get()
            yield event

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _broadcast(self, event: TelemetryEvent) -> None:
        dead: list[asyncio.Queue] = []
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)  # slow consumer — evict
        for q in dead:
            self.unsubscribe(q)

    @staticmethod
    def _is_high_value(event: TelemetryEvent) -> bool:
        """High-value events get Crystal Knowledge Graph nodes (Issue #162)."""
        return (
            event.risk_tier in HIGH_VALUE_RISK_TIERS
            or event.degraded
            or event.event_type in {"circuit_broken", "action_gate_triggered"}
        )

    async def _queue_crystal_indexing(self, event: TelemetryEvent) -> None:
        """Placeholder — Crystal integration wired in Issue #162."""
        log.debug("Crystal indexing queued for event %s", event.id)

    def close(self) -> None:
        self._store.close()
