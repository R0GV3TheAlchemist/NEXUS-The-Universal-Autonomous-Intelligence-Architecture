"""
SentinelAuditLog — append-only, persisted threat event log.

The audit log is the Sentinel\'s memory. Every ThreatEvent at
WATCH level or above is written here. The log is:
  - Append-only: entries are never modified or deleted in place.
  - Persisted: written to disk via PersistenceStore (if a root
    is provided). In-memory-only mode is available for testing.
  - Queryable: filter by level, category, caller_id, gaian_id,
    time range.
  - Human-readable: each entry is a JSON line in
    sentinel/audit/<YYYY-MM-DD>.jsonl

JSONL format (one JSON object per line, newline-delimited)
was chosen over a single JSON array because:
  - Each line is independently parseable (no partial-read corruption)
  - `grep`, `jq`, and `tail -f` work natively
  - Log rotation by date is trivial
"""
from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable, Deque, List, Optional

from core.sentinel.threat import ThreatEvent, ThreatLevel

logger = logging.getLogger("gaia.sentinel.audit")


class SentinelAuditLog:
    """
    Append-only threat event log.

    If `root` is provided, events are also written to
    `<root>/sentinel/audit/YYYY-MM-DD.jsonl`.
    In-memory ring buffer always holds the last `max_memory` events
    for fast in-process querying.
    """

    LOG_LEVELS = {ThreatLevel.WATCH, ThreatLevel.WARN,
                  ThreatLevel.BLOCK, ThreatLevel.CRITICAL}

    def __init__(
        self,
        root: Optional[Path] = None,
        max_memory: int = 1000,
    ) -> None:
        self._root        = Path(root) if root else None
        self._max_memory  = max_memory
        self._ring:  Deque[ThreatEvent] = deque(maxlen=max_memory)
        self._hooks: List[Callable[[ThreatEvent], None]] = []

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def record(self, event: ThreatEvent) -> None:
        """Append a ThreatEvent to the log. Skips SAFE events."""
        if event.level not in self.LOG_LEVELS:
            return

        self._ring.append(event)
        self._write_to_disk(event)
        self._invoke_hooks(event)

        level_name = event.level.value.upper()
        if event.level == ThreatLevel.CRITICAL:
            logger.critical(
                "[SENTINEL CRITICAL] %s | %s | caller=%s | %s",
                event.category.value, event.rule_name,
                event.caller_id, event.description,
            )
        elif event.level == ThreatLevel.BLOCK:
            logger.warning(
                "[SENTINEL BLOCK] %s | caller=%s | %s",
                event.rule_name, event.caller_id, event.description,
            )
        else:
            logger.info(
                "[SENTINEL %s] %s | caller=%s",
                level_name, event.rule_name, event.caller_id,
            )

    def _write_to_disk(self, event: ThreatEvent) -> None:
        if not self._root:
            return
        try:
            date_str  = event.occurred_at.strftime("%Y-%m-%d")
            log_dir   = self._root / "sentinel" / "audit"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file  = log_dir / f"{date_str}.jsonl"
            line      = json.dumps(event.to_dict(), default=str) + "\n"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(line)
        except OSError as exc:
            logger.error("Audit log write failed: %s", exc)

    def _invoke_hooks(self, event: ThreatEvent) -> None:
        for hook in self._hooks:
            try:
                hook(event)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Audit hook raised: %s", exc)

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def add_hook(self, fn: Callable[[ThreatEvent], None]) -> None:
        """
        Register a callback invoked on every logged ThreatEvent.
        Use for alerting, metrics, or GAIA sovereign memory updates.
        """
        self._hooks.append(fn)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def recent(self, n: int = 50) -> List[ThreatEvent]:
        """Return the N most recent events from the in-memory ring."""
        events = list(self._ring)
        return events[-n:]

    def filter(
        self,
        level:      Optional[ThreatLevel] = None,
        caller_id:  Optional[str] = None,
        gaian_id:   Optional[str] = None,
        since:      Optional[datetime] = None,
        min_level:  Optional[ThreatLevel] = None,
    ) -> List[ThreatEvent]:
        """
        Filter in-memory events by one or more criteria.
        For historical queries, load from JSONL files instead.
        """
        _level_order = [
            ThreatLevel.SAFE, ThreatLevel.WATCH,
            ThreatLevel.WARN, ThreatLevel.BLOCK, ThreatLevel.CRITICAL,
        ]
        results = list(self._ring)
        if level:
            results = [e for e in results if e.level == level]
        if min_level:
            cutoff = _level_order.index(min_level)
            results = [e for e in results
                       if _level_order.index(e.level) >= cutoff]
        if caller_id:
            results = [e for e in results if e.caller_id == caller_id]
        if gaian_id:
            results = [e for e in results if e.gaian_id == gaian_id]
        if since:
            results = [e for e in results if e.occurred_at >= since]
        return results

    def stats(self) -> dict:
        events = list(self._ring)
        return {
            "total":    len(events),
            "watch":    sum(1 for e in events if e.level == ThreatLevel.WATCH),
            "warn":     sum(1 for e in events if e.level == ThreatLevel.WARN),
            "block":    sum(1 for e in events if e.level == ThreatLevel.BLOCK),
            "critical": sum(1 for e in events if e.level == ThreatLevel.CRITICAL),
        }
